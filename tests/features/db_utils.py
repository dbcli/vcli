# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from vertica_python import connect


def create_schema(hostname='localhost', username=None, password=None,
                  dbname=None, port=None, schema_name=None):
    """Create test schema."""
    cn = create_cn(hostname, password, username, dbname, port)

    with cn.cursor() as cr:
        cr.execute('DROP SCHEMA IF EXISTS %s CASCADE' % dbname)
        cr.execute('CREATE SCHEMA %s' % dbname)

    cn.close()
    cn = create_cn(hostname, password, username, dbname, port)
    return cn


def create_cn(hostname, password, username, dbname, port):
    """
    Open connection to database.
    :param hostname:
    :param password:
    :param username:
    :param dbname: string
    :return: vertica_python.Connection
    """
    cn = connect(host=hostname, user=username, database=dbname,
                 password=password, port=port)

    print('Created connection: {0}.'.format(hostname))
    return cn


def drop_schema(hostname='localhost', username=None, password=None,
                dbname=None, port=None):
    cn = create_cn(hostname, password, username, dbname, port)

    with cn.cursor() as cr:
        cr.execute('DROP SCHEMA IF EXISTS %s CASCADE' % dbname)

    close_cn(cn)


def close_cn(cn=None):
    """
    Close connection.
    :param connection: vertica_python.connection
    """
    if cn:
        cn.close()
        print('Closed connection: {0}.'.format(cn.options['host']))
