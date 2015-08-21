# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
# import sys
import pexpect
import db_utils as dbutils
import fixture_utils as fixutils

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


def before_all(context):
    os.environ['LINES'] = "100"
    os.environ['COLUMNS'] = "100"
    os.environ['PAGER'] = 'cat'

    # VERTICA_URL specifies the Vertica database used for testing
    url = os.getenv('VERTICA_URL')
    if not url:
        raise Exception('You must configure VERTICA_URL environment variable')

    url = urlparse(url)
    context.conf = {
        'host': url.hostname,
        'user': url.username,
        'pass': url.password,
        'port': int(url.port or 5433),
        'dbname': url.path[1:]  # Ignore leading slash
    }

    context.exit_sent = False
    context.fixture_data = fixutils.read_fixture_files()
    context.cn = dbutils.create_cn(
        context.conf['host'], context.conf['pass'], context.conf['user'],
        context.conf['dbname'], context.conf['port'])


# def before_all(context):
#     """
#     Set env parameters.
#     """
#     os.environ['LINES'] = "100"
#     os.environ['COLUMNS'] = "100"
#     os.environ['PAGER'] = 'cat'

#     context.exit_sent = False

#     # vi = '_'.join([str(x) for x in sys.version_info[:3]])
#     # db_name = context.config.userdata.get('vcli_test', None)
#     # db_name_full = '{0}_{1}'.format(db_name, vi)

#     db_name_full = 'localdev'

#     # Store get params from config.
#     context.conf = {
#         'host': context.config.userdata.get('vertica_test_host', 'localhost'),
#         'user': context.config.userdata.get('vertica_test_user', 'dbadmin'),
#         'pass': context.config.userdata.get('vertica_test_pass', 'pass'),
#         'port': context.config.userdata.get('vertica_test_port', 5433),
#         'dbname': db_name_full,
#         'dbname_tmp': db_name_full + '_tmp',
#     }

#     # Store old env vars.
#     context.env = {
#         'VERTICA_DATABASE': os.environ.get('VERTICA_DATABASE', None),
#         'VERTICA_USER': os.environ.get('VERTICA_USER', None),
#         'VERTICA_HOST': os.environ.get('VERTICA_HOST', None),
#         'VERTICA_PASSWORD': os.environ.get('VERTICA_PASSWORD', None),
#     }

#     # Set new env vars.
#     os.environ['VERTICA_DATABASE'] = context.conf['dbname']
#     os.environ['VERTICA_USER'] = context.conf['user']
#     os.environ['VERTICA_HOST'] = context.conf['host']

#     if context.conf['pass']:
#         os.environ['VERTICA_PASSWORD'] = context.conf['pass']
#     else:
#         if 'VERTICA_PASSWORD' in os.environ:
#             del os.environ['VERTICA_PASSWORD']
#         if 'VERTICA_HOST' in os.environ:
#             del os.environ['VERTICA_HOST']

#     context.cn = dbutils.create_cn(
#         context.conf['host'], context.conf['pass'], context.conf['user'],
#         context.conf['dbname'], int(context.conf['port']))

#     context.fixture_data = fixutils.read_fixture_files()


# def after_all(context):
#     """
#     Unset env parameters.
#     """
#     dbutils.close_cn(context.cn)
#     # dbutils.drop_db(context.conf['host'], context.conf['user'],
#     #                 context.conf['pass'], context.conf['dbname'])

#     # Restore env vars.
#     for k, v in context.env.items():
#         if k in os.environ and v is None:
#             del os.environ[k]
#         elif v:
#             os.environ[k] = v


def after_scenario(context, _):
    """
    Cleans up after each test complete.
    """

    if hasattr(context, 'cli') and not context.exit_sent:
        context.cli.sendline('DROP SCHEMA IF EXISTS vcli_test CASCADE;')

        # Send Ctrl + D into cli
        context.cli.sendcontrol('d')
        context.cli.expect(pexpect.EOF, timeout=2)
