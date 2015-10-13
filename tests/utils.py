import getpass
import os

import pytest
import vertica_python as vertica

from vcli.main import format_output

from urlparse import urlparse


url = urlparse(os.getenv('VERTICA_URL'))
VERTICA_USER = url.username or getpass.getuser()
VERTICA_PASSWORD = url.password or ''
VERTICA_HOST = url.hostname or 'localhost'
VERTICA_DATABASE = url.path[1:]


def db_connection():
    conn = vertica.connect(user=VERTICA_USER, password=VERTICA_PASSWORD,
                           host=VERTICA_HOST, database=VERTICA_DATABASE)
    return conn


try:
    conn = db_connection()
    CAN_CONNECT_TO_DB = True
except:
    raise
    CAN_CONNECT_TO_DB = False


dbtest = pytest.mark.skipif(
    not CAN_CONNECT_TO_DB,
    reason="Need a Vertica instance at %s accessible by user '%s'" %
    (VERTICA_HOST, VERTICA_USER))


def create_schema():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE SCHEMA vcli_test')


def drop_schema(conn):
    with conn.cursor() as cur:
        cur.execute('DROP SCHEMA vcli_test CASCADE')


def run(executor, sql, join=False, expanded=False, vspecial=None,
        aligned=True, show_header=True):
    " Return string output for the sql to be run "
    result = []
    for title, rows, headers, status, force_stdout in executor.run(sql, vspecial):
        result.extend(format_output(title, rows, headers, status, 'psql',
                                    expanded=expanded, aligned=aligned,
                                    show_header=show_header))
    if join:
        result = '\n'.join(result)
    return result
