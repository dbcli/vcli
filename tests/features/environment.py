# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import getpass
import os

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
        'host': url.hostname or 'localhost',
        'user': url.username or getpass.getuser(),
        'pass': url.password or '',
        'port': int(url.port or 5433),
        'dbname': url.path[1:]  # Ignore leading slash
    }

    context.exit_sent = False
    context.fixture_data = fixutils.read_fixture_files()
    context.cn = dbutils.create_cn(
        context.conf['host'], context.conf['pass'], context.conf['user'],
        context.conf['dbname'], context.conf['port'])


def after_scenario(context, _):
    """
    Cleans up after each test complete.
    """

    if hasattr(context, 'cli') and not context.exit_sent:
        context.cli.sendline('DROP SCHEMA IF EXISTS vcli_test CASCADE;')

        # Terminate nicely
        context.cli.terminate()
