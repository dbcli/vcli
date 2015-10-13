import logging
import socket
import sys

import sqlparse

import vertica_python as vertica

from sqlparse.tokens import Token as _Token
from sqlparse.sql import Token

from .packages import vspecial as special
from .encodingutils import PY2


_logger = logging.getLogger(__name__)


class VExecute(object):

    # The boolean argument to the current_schemas function indicates whether
    # implicit schemas, e.g. pg_catalog
    search_path_query = '''
        SELECT current_schemas(true)'''

    schemata_query = '''
        SELECT  schema_name
        FROM    v_catalog.schemata
        ORDER BY 1'''

    tables_query = '''
        SELECT  table_schema, table_name
        FROM    v_catalog.tables
        ORDER BY 1, 2'''

    views_query = '''
        SELECT table_schema, table_name
        FROM v_catalog.views
        ORDER BY 1, 2'''

    table_columns_query = '''
        SELECT  table_schema, table_name, column_name
        FROM    v_catalog.columns
        ORDER BY 1, 2, 3'''

    view_columns_query = '''
        SELECT  table_schema, table_name, column_name
        FROM v_catalog.view_columns
        ORDER BY 1, 2, 3'''

    functions_query = '''
        SELECT schema_name, function_name
        FROM v_catalog.user_functions
        WHERE schema_name NOT IN ('v_catalog', 'v_monitor', 'v_internal')
        ORDER BY 1, 2'''

    databases_query = '''
        SELECT  database_name, owner_id, 'UTF8' AS encoding,
                'en_US.utf8' AS collate, 'en_US.utf8' AS ctype
        FROM    v_catalog.databases
        ORDER BY 1'''

    datatypes_query = '''
        SELECT schema_name, type_name
        FROM v_catalog.types, v_catalog.schemata
        WHERE schema_name NOT IN ('v_catalog', 'v_monitor', 'v_internal')
        ORDER BY 1, 2'''

    def __init__(self, database, user, password, host, port):
        self.dbname = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connect()

    def connect(self, database=None, user=None, password=None, host=None,
                port=None):

        db = (database or self.dbname)
        user = (user or self.user)
        password = (password or self.password)
        host = (host or self.host)
        port = (port or self.port)

        conn = vertica.connect(database=db, user=user, password=password,
                               host=host, port=int(port))

        # HACK: Modify vertica_python's connection socket to do keep alive
        # TODO: Keep alive for Windows and other platforms
        # http://stackoverflow.com/questions/12248132/how-to-change-tcp-keepalive-timer-using-python-script
        sock = conn._socket()
        if sys.platform == 'darwin':  # Mac OS X
            tcp_keepalive = 0x10
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, tcp_keepalive, 60)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        elif sys.platform.startswith('linux'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

        if hasattr(self, 'conn'):
            self.conn.close()
        self.conn = conn
        # self.conn.autocommit = True
        self.dbname = db
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        # register_json_typecasters(self.conn, self._json_typecaster)
        # register_hstore_typecaster(self.conn)

    def _json_typecaster(self, json_data):
        """Interpret incoming JSON data as a string.

        The raw data is decoded using the connection's encoding, which defaults
        to the database's encoding.

        See http://initd.org/psycopg/docs/connection.html#connection.encoding
        """

        if PY2:
            return json_data.decode(self.conn.encoding)
        else:
            return json_data

    def run(self, statement, vspecial=None):
        """Execute the sql in the database and return the results.

        :param statement: A string containing one or more sql statements
        :param vspecial: VSpecial object
        :return: List of tuples containing (title, rows, headers, status,
                                            force_stdout)
        """
        # Remove spaces and EOL
        statement = statement.strip()
        if not statement:  # Empty string
            yield (None, None, None, None, True)

        # Split the sql into separate queries and run each one.
        for sql in sqlparse.split(statement):
            # Remove spaces, eol and semi-colons.
            sql = sql.rstrip(';')

            if vspecial:
                # First try to run each query as special
                try:
                    _logger.debug('Trying a vspecial command. sql: %r', sql)
                    cur = self.conn.cursor()
                    for result in vspecial.execute(cur, sql):
                        yield result
                    return
                except special.CommandNotFound:
                    pass

            yield self.execute_normal_sql(sql)

    def execute_normal_sql(self, split_sql):
        _logger.debug('Regular sql statement. sql: %r', split_sql)
        cur = self.conn.cursor()

        tree = sqlparse.parse(split_sql)[0]
        if _is_copy_from_local(tree):
            _execute_copy_from_local_sql(tree, cur)
        else:
            cur.execute(split_sql)

        title = None
        statusmessage = None
        first_token = split_sql.split()[0].lower()
        if cur.description and first_token in ('select', 'update', 'delete',
                                               'insert'):
            headers = [x[0] for x in cur.description]
            return (title, cur, headers, statusmessage, False)
        else:
            _logger.debug('No rows in result.')
            return (title, None, None, statusmessage, True)

    def search_path(self):
        """Returns the current search path as a list of schema names"""
        with self.conn.cursor() as cur:
            _logger.debug('Search path query. sql: %r', self.search_path_query)
            cur.execute(self.search_path_query)
            names = cur.fetchone()[0]
            return names.split(',')

    def schemata(self):
        """Returns a list of schema names in the database"""
        with self.conn.cursor() as cur:
            _logger.debug('Schemata Query. sql: %r', self.schemata_query)
            cur.execute(self.schemata_query)
            return (x[0] for x in cur.fetchall())

    def tables(self):
        """Yields (schema_name, table_name) tuples"""
        with self.conn.cursor() as cur:
            _logger.debug('Tables Query. sql: %r', self.tables_query)
            cur.execute(self.tables_query)
            for row in cur.iterate():
                yield tuple(row)

    def views(self):
        """Yields (schema_name, view_name) tuples.

            Includes both views and and materialized views
        """
        with self.conn.cursor() as cur:
            _logger.debug('Views Query. sql: %r', self.views_query)
            cur.execute(self.views_query)
            for row in cur.iterate():
                yield tuple(row)

    def table_columns(self):
        with self.conn.cursor() as cur:
            _logger.debug('Columns Query. sql: %r', self.table_columns_query)
            cur.execute(self.table_columns_query)
            for row in cur.iterate():
                yield tuple(row)

    def view_columns(self):
        with self.conn.cursor() as cur:
            _logger.debug('Columns Query. sql: %r', self.view_columns_query)
            cur.execute(self.view_columns_query)
            for row in cur.iterate():
                yield tuple(row)

    def databases(self):
        with self.conn.cursor() as cur:
            _logger.debug('Databases Query. sql: %r', self.databases_query)
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]

    def functions(self):
        """Yields tuples of (schema_name, function_name)"""
        with self.conn.cursor() as cur:
            _logger.debug('Functions Query. sql: %r', self.functions_query)
            cur.execute(self.functions_query)
            for row in cur.iterate():
                yield tuple(row)

    def datatypes(self):
        """Yields tuples of (schema_name, type_name)"""
        with self.conn.cursor() as cur:
            _logger.debug('Datatypes Query. sql: %r', self.datatypes_query)
            cur.execute(self.datatypes_query)
            for row in cur.iterate():
                yield tuple(row)


def _is_copy_from_local(sql_tree):
    first_token = sql_tree.tokens[0]
    if not (first_token.is_keyword and first_token.value.lower() == 'copy'):
        return False

    # Search for 'LOCAL' keyword
    found = False
    for i, token in enumerate(sql_tree.tokens):
        if token.is_keyword and token.value.lower() == 'local':
            found = True
            break

    if not found:
        return False

    # After 'LCOAL', there should be a whitespace then a file path
    try:
        token = sql_tree.tokens[i + 2]
    except IndexError:
        return False

    return token.ttype is _Token.Literal.String.Single


def _execute_copy_from_local_sql(sql_tree, cursor):
    # Search for 'LOCAL' keyword
    for i, token in enumerate(sql_tree.tokens):
        if token.is_keyword and token.value.lower() == 'local':
            break

    file_path = sql_tree.tokens[i + 2].value.strip('\'"')

    # Replace "LOCAL <file_path>" with "stdin"
    sql_tree.tokens = sql_tree.tokens[0:i] + [
        Token(_Token.Keyword, 'stdin')
    ] + sql_tree.tokens[i + 3:]
    new_sql = sql_tree.to_unicode()

    cursor.flush_to_query_ready()
    with open(file_path, 'rb') as f:
        cursor.copy(new_sql, f)

    cursor.flush_to_query_ready()
