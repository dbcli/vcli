# -*- coding: utf-8 -*-
import os
import tempfile

import pytest

from textwrap import dedent

from vertica_python import errors

from utils import run, dbtest
from vcli.packages.vspecial.main import VSpecial


@dbtest
def test_conn(executor):
    run(executor, '''create table vcli_test.test(a varchar)''')
    run(executor, '''insert into vcli_test.test values('abc')''')
    output = run(executor, '''select * from vcli_test.test''', join=True)
    assert output == dedent("""\
        +-----+
        | a   |
        |-----|
        | abc |
        +-----+""")


@dbtest
def test_bools_are_treated_as_strings(executor):
    run(executor, 'create table vcli_test.test(a boolean)')
    run(executor, 'insert into vcli_test.test values(True)')
    output = run(executor, 'select * from vcli_test.test', join=True)
    assert output == dedent("""\
        +------+
        | a    |
        |------|
        | True |
        +------+""")


@dbtest
def test_schemata_table_views_and_columns_query(executor):
    run(executor, "create table vcli_test.a(x varchar, y varchar)")
    run(executor, "create table vcli_test.b(z varchar)")
    run(executor, "create view vcli_test.d as select 1 as e")

    # tables
    assert set(executor.tables()) >= set([
        ('vcli_test', 'a'), ('vcli_test', 'b')
    ])

    assert set(executor.table_columns()) >= set([
        ('vcli_test', 'a', 'x'), ('vcli_test', 'a', 'y'),
        ('vcli_test', 'b', 'z')
    ])

    # views
    assert ('vcli_test', 'd') in set(executor.views())
    assert ('vcli_test', 'd', 'e') in set(executor.view_columns())


@dbtest
def test_functions_query(executor):
    run(executor,
        'create function vcli_test.myzero() return int as begin return 0; end')
    funcs = list(executor.functions())
    assert ('vcli_test', 'myzero') in funcs


@dbtest
def test_invalid_syntax(executor):
    with pytest.raises(errors.ProgrammingError) as excinfo:
        run(executor, 'invalid syntax!')
    assert 'syntax error at or near "invalid"' in str(excinfo.value).lower()


@dbtest
def test_invalid_column_name(executor):
    with pytest.raises(errors.ProgrammingError) as excinfo:
        run(executor, 'select invalid command')
    assert 'column "invalid" does not exist' in str(excinfo.value).lower()


@pytest.fixture(params=[True, False])
def expanded(request):
    return request.param


@dbtest
def test_unicode_support_in_output(executor, expanded):
    run(executor, "create table vcli_test.unicodechars(t varchar)")
    run(executor, "insert into vcli_test.unicodechars (t) values ('é')")

    # See issue #24, this raises an exception without proper handling
    assert u'é' in run(
        executor, "select * from vcli_test.unicodechars", join=True,
        expanded=expanded)


@dbtest
def test_multiple_queries_same_line(executor):
    result = run(executor, "select 'foo'; select 'bar'")
    assert "foo" in result[0]
    assert "bar" in result[1]


@dbtest
def test_multiple_queries_with_special_command_same_line(executor, vspecial):
    result = run(executor, "select 'foo'; \d", vspecial=vspecial)
    assert "foo" in result[0]
    # This is a lame check. :(
    assert "Schema" in result[1]


@dbtest
def test_multiple_queries_same_line_syntaxerror(executor):
    with pytest.raises(errors.ProgrammingError) as excinfo:
        run(executor, "select 'foo'; invalid syntax")
    assert 'syntax error at or near "invalid"' in str(excinfo.value).lower()


@pytest.fixture
def vspecial():
    return VSpecial()


@dbtest
def test_special_command_help(executor, vspecial):
    result = run(executor, '\\?', vspecial=vspecial)[0].split('|')
    assert(result[1].find(u'Command') != -1)
    assert(result[2].find(u'Description') != -1)


@dbtest
def test_bytea_field_support_in_output(executor):
    run(executor, "create table vcli_test.binarydata(c bytea)")
    run(executor, """
        insert into vcli_test.binarydata (c)
        values (hex_to_binary('0x616263'))
    """)

    assert u'abc' in run(
        executor, "select * from vcli_test.binarydata", join=True)


@dbtest
def test_unicode_support_in_unknown_type(executor):
    assert u'日本語' in run(executor, "SELECT '日本語' AS japanese;", join=True)


@dbtest
@pytest.mark.parametrize('value', ['10000000', '10000000.0', '10000000000000'])
def test_large_numbers_render_directly(executor, value):
    run(executor, "create table vcli_test.numbertest(a numeric)")
    run(executor,
        "insert into vcli_test.numbertest (a) values ({0})".format(value))

    assert value in run(executor, "select * from vcli_test.numbertest",
                        join=True)


@dbtest
@pytest.mark.parametrize('command', ['di', 'dv', 'ds', 'df', 'dT'])
@pytest.mark.parametrize('verbose', ['', '+'])
@pytest.mark.parametrize('pattern', ['', 'x', '*.*', 'x.y', 'x.*', '*.y'])
def test_describe_special(executor, command, verbose, pattern):
    # We don't have any tests for the output of any of the special commands,
    # but we can at least make sure they run without error
    sql = r'\{command}{verbose} {pattern}'.format(**locals())
    executor.run(sql)


@dbtest
def test_copy_from_local_csv(executor):
    run(executor, """
        create table vcli_test.people (
            name varchar(50),
            age integer)
    """)

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write('Alice,20\nBob,30\nCindy,40\n')

    try:
        run(executor, """
            copy vcli_test.people from local '%s' delimiter ','
        """ % f.name)
    finally:
        os.remove(f.name)

    output = run(executor, "select * from vcli_test.people", join=True)
    assert output == dedent("""\
        +--------+-------+
        | name   |   age |
        |--------+-------|
        | Alice  |    20 |
        | Bob    |    30 |
        | Cindy  |    40 |
        +--------+-------+""")


@dbtest
def test_special_command_align_mode(executor, vspecial):
    output = run(executor, "select 'Alice' as name, 20 as age",
                 vspecial=vspecial, join=True)
    assert output == dedent("""\
        +--------+-------+
        | name   |   age |
        |--------+-------|
        | Alice  |    20 |
        +--------+-------+""")

    output = run(executor, '\\a', vspecial=vspecial, join=True)
    assert 'unaligned' in output

    output = run(executor, "select 'Alice' as name, 20 as age",
                 vspecial=vspecial, aligned=False, join=True)
    assert output == dedent("""\
        name|age
        Alice|20""")
