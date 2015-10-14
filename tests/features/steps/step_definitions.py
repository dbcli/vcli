# -*- coding: utf-8 -*-
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import codecs
import getpass
import os
import re
import tempfile

import pexpect
import pip

from urlparse import urlparse

from behave import given, when, then


@given('we have vcli installed')
def step_install_cli(_):
    """
    Check that vcli is in installed modules.
    """
    dists = set([di.key for di in pip.get_installed_distributions()])
    assert 'vcli' in dists


@when('we run vcli without arguments')
def step_run_cli_without_args(context):
    """
    Run the process using pexpect.
    """
    context.cli = pexpect.spawnu('vcli')


@when('we run vcli with url')
def step_run_cli_with_url(context):
    context.cli = pexpect.spawnu('vcli %s' % os.getenv('VERTICA_URL'))


@when('we run vcli with arguments')
def step_run_cli_with_args(context):
    url = urlparse(os.getenv('VERTICA_URL'))
    args = {
        'host': url.hostname or 'localhost',
        'port': url.port or 5433,
        'user': url.username or getpass.getuser(),
        'password': url.password or '',
        'database': url.path[1:]
    }
    cmd = 'vcli -h %(host)s -U %(user)s -p %(port)s %(database)s' % args
    if args['password']:
        cmd += ' -W'

    context.cli = pexpect.spawnu(cmd)

    if args['password']:
        _expect_exact(context, 'Password:', timeout=1)
        context.cli.sendline(args['password'])


@when('we run vcli help')
def step_run_cli_help(context):
    context.cli = pexpect.spawnu('vcli --help')
    context.exit_sent = True


@when('we wait for time prompt')
def step_wait_time_prompt(context):
    _expect_exact(context, 'Time: ', timeout=2)


@when('we wait for prompt')
def step_wait_prompt(context):
    """
    Make sure prompt is displayed.
    """
    _expect_prompt(context, timeout=7)


@when('we send "ctrl + d"')
def step_ctrl_d(context):
    """
    Send Ctrl + D to hopefully exit.
    """
    context.cli.sendcontrol('d')
    context.exit_sent = True


@when('we send "\q" command')
def step_quit(context):
    """
    Send \q to hopefully exit.
    """
    context.cli.sendline('\\q')
    context.exit_sent = True


@when('we send "\?" command')
def step_send_help(context):
    """
    Send \? to see help.
    """
    context.cli.sendline('\\?')


@when('we send "\h" command')
def step_send_help2(context):
    """
    Send \h to see help.
    """
    context.cli.sendline('\\h')


@when('we create schema')
def step_schema_create(context):
    """
    Send create database.
    """
    context.cli.sendline('create schema vcli_test;')


@when('we drop schema')
def step_schema_drop(context):
    """
    Send drop schema.
    """
    context.cli.sendline('drop schema vcli_test;')


@when('we create table')
def step_create_table(context):
    """
    Send create table.
    """
    context.cli.sendline('create table vcli_test.people(name varchar(30));')
    _expect_prompt(context, timeout=2)


@when('we insert into table')
def step_insert_into_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline("insert into vcli_test.people (name) values('Bob');")
    _expect(context, r'OUTPUT\s*\|', timeout=2)
    _expect(context, r'1\s*\|', timeout=1)


@when('we update table')
def step_update_table(context):
    """
    Send update table.
    """
    context.cli.sendline("update vcli_test.people set name = 'Alice';")
    _expect(context, r'OUTPUT\s*\|', timeout=2)
    _expect(context, r'1\s*\|', timeout=1)


@when('we delete from table')
def step_delete_from_table(context):
    """
    Send delete from table.
    """
    context.cli.sendline('delete from vcli_test.people;')
    _expect(context, r'OUTPUT\s*\|', timeout=2)
    _expect(context, r'1\s*\|', timeout=1)


@when('we drop table')
def step_drop_table(context):
    """
    Send drop table.
    """
    context.cli.sendline('drop table vcli_test.people;')


@when('we connect to database')
def step_db_connect_database(context):
    """
    Send connect to database.
    """
    dbname = context.conf['dbname']
    context.cli.sendline('\\c %s' % dbname)


@when('we switch output verbosity')
def step_switch_output_verbosity(context):
    context.cli.sendline('\\t')
    _expect_exact(context, ' header.', timeout=1)
    _expect_prompt(context, timeout=1)

    context.cli.sendline('\\a')
    _expect_exact(context, 'Output format is ', timeout=1)
    _expect_prompt(context, timeout=1)


@when('we redirect output to file')
def step_redirect_output_to_file(context):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        context.temp_filename = f.name
    context.cli.sendline('\\o %s' % context.temp_filename)
    _expect_exact(context, 'output to file.', timeout=1)
    _expect_prompt(context, timeout=1)


@when('we redirect output to stdout')
def step_redirect_output_to_stdout(context):
    context.cli.sendline('\\o')
    _expect_exact(context, 'output to stdout.', timeout=1)
    _expect_prompt(context, timeout=1)


@when('we select from table')
def step_select_table(context):
    context.cli.sendline('select * from vcli_test.people;')


@then('vcli exits')
def step_wait_exit(context):
    """
    Make sure the cli exits.
    """
    _expect_exact(context, pexpect.EOF, timeout=2)


@then('we see vcli help')
def step_see_cli_help(context):
    _expect_exact(context, 'Usage: vcli ', timeout=1)


@then('we see vcli prompt')
def step_see_prompt(context):
    """
    Wait to see the prompt.
    """
    _expect_prompt(context, timeout=3)


@then('we see help output')
def step_see_help(context):
    for expected_line in context.fixture_data['help_commands.txt']:
        _expect_exact(context, expected_line, timeout=2)


@then('we see schema created')
def step_see_schema_created(context):
    """
    Wait to see create database output.
    """
    context.cli.sendline('\\dn')
    _expect(context, r'vcli_test\s*\|\s*%(user)s' % context.conf, timeout=2)


@then('we see schema dropped')
def step_see_schema_dropped(context):
    """
    Wait to see drop database output.
    """
    context.cli.sendline('\\dn')
    try:
        context.cli.expect(r'vcli_test\s*\|\s*%(user)s' % context.conf,
                           timeout=2)
    except pexpect.TIMEOUT:
        pass
    else:
        assert False, "Schema 'vcli_test' should not exist"


@then('we see database connected')
def step_see_db_connected(context):
    """
    Wait to see drop database output.
    """
    _expect_exact(context, 'You are now connected to database', timeout=2)


@then('we see table created')
def step_see_table_created(context):
    """
    Wait to see create table output.
    """
    context.cli.sendline('\\dt vcli_test.*')
    _expect(context, r'vcli_test\s*\|\s*people', timeout=2)


@then('we see record inserted')
def step_see_record_inserted(context):
    """
    Wait to see insert output.
    """
    context.cli.sendline('select name from vcli_test.people;')
    _expect(context, r'Bob\s*\|', timeout=2)


@then('we see record updated')
def step_see_record_updated(context):
    """
    Wait to see update output.
    """
    context.cli.sendline('select name from vcli_test.people;')
    _expect(context, r'Alice\s*\|', timeout=2)


@then('we see record deleted')
def step_see_data_deleted(context):
    """
    Wait to see delete output.
    """
    context.cli.sendline('select count(1) as rowcount from vcli_test.people;')
    _expect(context, r'rowcount\s*\|', timeout=2)
    _expect(context, r'0\s*\|', timeout=1)


@then('we see result in file')
def step_see_result_in_file(context):
    assert os.path.exists(context.temp_filename)
    with codecs.open(context.temp_filename, encoding='utf-8') as f:
        content = f.read().strip()
    assert content == 'Bob', "'%s' != 'Bob'" % content


@then('we see result in stdout')
def step_see_result_in_stdout(context):
    _expect(context, r'Bob\s*\|', timeout=2)
    _expect(context, r'1 row', timeout=1)


@then('we see table dropped')
def step_see_table_dropped(context):
    """
    Wait to see drop output.
    """
    context.cli.sendline('\\dt vcli_test')

    try:
        context.cli.expect(r'vcli_test\s*\|\s*people', timeout=2)
    except pexpect.TIMEOUT:
        pass
    else:
        raise AssertionError("Table 'vcli_test.people' should not exist")


@when(u'we select unicode data')
def step_select_unicode(context):
    context.cli.sendline(u"SELECT '中文' AS chinese;")


@then(u'wee see unicode result in file')
def step_see_unicode_in_file(context):
    assert os.path.exists(context.temp_filename)
    with codecs.open(context.temp_filename, encoding='utf-8') as f:
        content = f.read().strip()
    assert content == u'中文', u"'%s' != '中文'" % content


def _strip_color(s):
    return re.sub(r'\x1b\[([0-9A-Za-z;?])+[m|K]?', '', s)


def _expect_exact(context, expected, timeout=1):
    try:
        context.cli.expect_exact(expected, timeout=timeout)
    except:
        # Strip color codes out of the output.
        actual = _strip_color(context.cli.before)
        raise AssertionError('Expected:\n---\n{0}\n---\n\nActual:\n---\n{1}\n---'.format(
            expected,
            actual))


def _expect(context, expected, timeout=1):
    try:
        context.cli.expect(expected, timeout=timeout)
    except:
        actual = _strip_color(context.cli.before)
        raise AssertionError('Expected:\n---\n{0}\n---\n\nActual:\n---\n{1}\n---'.format(
            expected,
            actual))


def _expect_prompt(context, timeout=1):
    dbname = context.conf['dbname']
    _expect_exact(context, '{0}=> '.format(dbname), timeout=timeout)
