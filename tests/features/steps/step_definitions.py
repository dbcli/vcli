# -*- coding: utf-8 -*-
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import os

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
        'host': url.hostname,
        'port': url.port or 5433,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:]
    }
    cmd = 'vcli -h %(host)s -U %(user)s -W -p %(port)s %(database)s' % args
    context.cli = pexpect.spawnu(cmd)
    context.cli.expect_exact('Password:')
    context.cli.sendline(args['password'])


@when('we run vcli help')
def step_run_cli_help(context):
    context.cli = pexpect.spawnu('vcli --help')
    context.exit_sent = True


@when('we wait for prompt')
def step_wait_prompt(context):
    """
    Make sure prompt is displayed.
    """
    context.cli.expect('{0}=> '.format(context.conf['dbname']), timeout=7)


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


@when('we insert into table')
def step_insert_into_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline("insert into vcli_test.people (name) values('Bob');")
    context.cli.expect(r'OUTPUT\s*\|', timeout=2)
    context.cli.expect(r'1\s*\|', timeout=1)


@when('we update table')
def step_update_table(context):
    """
    Send update table.
    """
    context.cli.sendline("update vcli_test.people set name = 'Alice';")
    context.cli.expect(r'OUTPUT\s*\|', timeout=2)
    context.cli.expect(r'1\s*\|', timeout=1)


@when('we delete from table')
def step_delete_from_table(context):
    """
    Send delete from table.
    """
    context.cli.sendline('delete from vcli_test.people;')
    context.cli.expect(r'OUTPUT\s*\|', timeout=2)
    context.cli.expect(r'1\s*\|', timeout=1)


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


@then('vcli exits')
def step_wait_exit(context):
    """
    Make sure the cli exits.
    """
    context.cli.expect(pexpect.EOF, timeout=2)


@then('we see vcli help')
def step_see_cli_help(context):
    context.cli.expect_exact('Usage: vcli ')


@then('we see vcli prompt')
def step_see_prompt(context):
    """
    Wait to see the prompt.
    """
    context.cli.expect('{0}=> '.format(context.conf['dbname']), timeout=3)


@then('we see help output')
def step_see_help(context):
    for expected_line in context.fixture_data['help_commands.txt']:
        try:
            context.cli.expect_exact(expected_line, timeout=3)
        except pexpect.TIMEOUT:
            assert False, 'Expected: ' + expected_line.strip()


@then('we see schema created')
def step_see_schema_created(context):
    """
    Wait to see create database output.
    """
    context.cli.sendline('\\dn')
    context.cli.expect(r'vcli_test\s*\|\s*%(user)s' % context.conf, timeout=2)


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
    context.cli.expect_exact('You are now connected to database', timeout=2)


@then('we see table created')
def step_see_table_created(context):
    """
    Wait to see create table output.
    """
    context.cli.sendline('\\dt vcli_test.*')
    context.cli.expect(r'vcli_test\s*\|\s*people', timeout=2)


@then('we see record inserted')
def step_see_record_inserted(context):
    """
    Wait to see insert output.
    """
    context.cli.sendline('select name from vcli_test.people;')
    context.cli.expect(r'Bob\s*\|', timeout=2)


@then('we see record updated')
def step_see_record_updated(context):
    """
    Wait to see update output.
    """
    context.cli.sendline('select name from vcli_test.people;')
    context.cli.expect(r'Alice\s*\|', timeout=2)


@then('we see record deleted')
def step_see_data_deleted(context):
    """
    Wait to see delete output.
    """
    context.cli.sendline('select count(1) as rowcount from vcli_test.people;')
    context.cli.expect(r'rowcount\s*\|', timeout=2)
    context.cli.expect(r'0\s*\|', timeout=1)


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
        assert False, "Table 'vcli_test.people' should not exist"
