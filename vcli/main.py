#!/usr/bin/env python
from __future__ import print_function

import getpass
import logging
import os
import sys
import threading
import traceback

import click
import sqlparse

import vcli.packages.vspecial as special

from collections import namedtuple
from time import time
from urlparse import urlparse

from prompt_toolkit import CommandLineInterface, Application, AbortAction
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Always, HasFocus, IsDone
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import (
    ConditionalProcessor, HighlightMatchingBracketProcessor)
from prompt_toolkit.shortcuts import create_default_layout, create_eventloop
from pygments.lexers.sql import PostgresLexer
from pygments.token import Token
from vertica_python import errors

from .__init__ import __version__
from .config import write_default_config, load_config
from .encodingutils import utf8tounicode
from .key_bindings import vcli_bindings
from .packages import vtablefmt
from .packages.expanded import expanded_table
from .packages.tabulate import tabulate
from .packages.vspecial.main import (VSpecial, NO_QUERY)
from .vbuffer import VBuffer
from .completion_refresher import CompletionRefresher
from .vcompleter import VCompleter
from .vexecute import VExecute
from .vstyle import style_factory
from .vtoolbar import create_toolbar_tokens_func


# Query tuples are used for maintaining history
Query = namedtuple('Query', ['query', 'successful', 'mutating'])


class VCli(object):

    def __init__(self, vexecute=None, vclirc_file=None):
        self.vexecute = vexecute

        from vcli import __file__ as package_root
        package_root = os.path.dirname(package_root)

        default_config = os.path.join(package_root, 'vclirc')
        write_default_config(default_config, vclirc_file)

        self.vspecial = VSpecial()

        # Load config.
        c = self.config = load_config(vclirc_file, default_config)
        self.multi_line = c['main'].as_bool('multi_line')
        self.vi_mode = c['main'].as_bool('vi')
        self.vspecial.timing_enabled = c['main'].as_bool('timing')
        self.table_format = c['main']['table_format']
        self.syntax_style = c['main']['syntax_style']
        self.cli_style = c['colors']
        self.wider_completion_menu = c['main'].as_bool('wider_completion_menu')
        self.completion_refresher = CompletionRefresher()

        self.logger = logging.getLogger(__name__)
        self.initialize_logging()

        self.query_history = []

        # Initialize completer
        smart_completion = c['main'].as_bool('smart_completion')
        completer = VCompleter(smart_completion, vspecial=self.vspecial)
        self.completer = completer
        self._completer_lock = threading.Lock()
        self.register_special_commands()

        self.cli = None

    def register_special_commands(self):
        self.vspecial.register(self.change_db, '\\c',
                               '\\c[onnect] [DBNAME]',
                               'Connect to a new database',
                               aliases=('use', '\\connect', 'USE'))
        self.vspecial.register(self.refresh_completions, '\\#', '\\#',
                               'Refresh auto-completions', arg_type=NO_QUERY)
        self.vspecial.register(self.refresh_completions, '\\refresh',
                               '\\refresh', 'Refresh auto-completions',
                               arg_type=NO_QUERY)

    def change_db(self, pattern, **_):
        if pattern:
            db = pattern[1:-1] if pattern[0] == pattern[-1] == '"' else pattern
            self.vexecute.connect(database=db)
        else:
            self.vexecute.connect()

        yield (None, None, None, 'You are now connected to database "%s" as '
               'user "%s"' % (self.vexecute.dbname, self.vexecute.user), True)

    def initialize_logging(self):

        log_file = self.config['main']['log_file']
        log_level = self.config['main']['log_level']

        level_map = {'CRITICAL': logging.CRITICAL,
                     'ERROR': logging.ERROR,
                     'WARNING': logging.WARNING,
                     'INFO': logging.INFO,
                     'DEBUG': logging.DEBUG
                     }

        handler = logging.FileHandler(os.path.expanduser(log_file))

        formatter = logging.Formatter(
            '%(asctime)s (%(process)d/%(threadName)s) '
            '%(name)s %(levelname)s - %(message)s')

        handler.setFormatter(formatter)

        root_logger = logging.getLogger('vcli')
        root_logger.addHandler(handler)
        root_logger.setLevel(level_map[log_level.upper()])

        root_logger.debug('Initializing vcli logging.')
        root_logger.debug('Log file %r.', log_file)

    def connect_uri(self, uri):
        uri = urlparse(uri)
        database = uri.path[1:]  # ignore the leading fwd slash
        host = uri.hostname or 'localhost'
        user = uri.username or getpass.getuser()
        port = uri.port or 5433
        password = uri.password or ''
        self.connect(database, host, user, port, password)

    def connect(self, database, host, user, port, passwd):
        # Connect to the database
        try:
            self.vexecute = VExecute(database, user, passwd, host, port)
        except errors.DatabaseError as e:  # Connection can fail
            self.logger.debug('Database connection failed: %r.', e)
            self.logger.error("traceback: %r", traceback.format_exc())
            error_msg = str(e) or type(e).__name__
            click.secho(error_msg, err=True, fg='red')
            exit(1)

    def handle_editor_command(self, cli, document):
        """
        Editor command is any query that is prefixed or suffixed
        by a '\e'. The reason for a while loop is because a user
        might edit a query multiple times.
        For eg:
        "select * from \e"<enter> to edit it in vim, then come
        back to the prompt with the edited query "select * from
        blah where q = 'abc'\e" to edit it again.
        :param cli: CommandLineInterface
        :param document: Document
        :return: Document
        """
        while special.editor_command(document.text):
            filename = special.get_filename(document.text)
            sql, message = special.open_external_editor(filename,
                                                        sql=document.text)
            if message:
                # Something went wrong. Raise an exception and bail.
                raise RuntimeError(message)
            cli.current_buffer.document = Document(
                sql, cursor_position=len(sql))
            document = cli.run(False)
            continue
        return document

    def run_cli(self):
        vexecute = self.vexecute
        logger = self.logger
        original_less_opts = self.adjust_less_opts()

        completer = self.completer
        self.refresh_completions()

        def set_vi_mode(value):
            self.vi_mode = value

        key_binding_manager = vcli_bindings(
            get_vi_mode_enabled=lambda: self.vi_mode,
            set_vi_mode_enabled=set_vi_mode)

        click.secho('Version: %s' % __version__)

        def prompt_tokens(cli):
            return [(Token.Prompt, '%s=> ' % vexecute.dbname)]

        get_toolbar_tokens = create_toolbar_tokens_func(lambda: self.vi_mode,
                                                        self.completion_refresher.is_refreshing)
        input_processors = [
            # Highlight matching brackets while editing.
            ConditionalProcessor(
                processor=HighlightMatchingBracketProcessor(chars='[](){}'),
                filter=HasFocus(DEFAULT_BUFFER) & ~IsDone())
        ]
        layout = create_default_layout(
            lexer=PostgresLexer,
            reserve_space_for_menu=True,
            get_prompt_tokens=prompt_tokens,
            get_bottom_toolbar_tokens=get_toolbar_tokens,
            display_completions_in_columns=self.wider_completion_menu,
            multiline=True,
            extra_input_processors=input_processors)
        history_file = self.config['main']['history_file']
        with self._completer_lock:
            buf = VBuffer(always_multiline=self.multi_line, completer=self.completer,
                          history=FileHistory(os.path.expanduser(history_file)),
                          complete_while_typing=Always())

            application = Application(style=style_factory(self.syntax_style, self.cli_style),
                                      layout=layout, buffer=buf,
                                      key_bindings_registry=key_binding_manager.registry,
                                      on_exit=AbortAction.RAISE_EXCEPTION,
                                      ignore_case=True)
            self.cli = CommandLineInterface(application=application,
                                            eventloop=create_eventloop())

        try:
            while True:
                document = self.cli.run()

                # The reason we check here instead of inside the vexecute is
                # because we want to raise the Exit exception which will be
                # caught by the try/except block that wraps the vexecute.run()
                # statement.
                if quit_command(document.text):
                    raise EOFError

                try:
                    document = self.handle_editor_command(self.cli, document)
                except RuntimeError as e:
                    logger.error("sql: %r, error: %r", document.text, e)
                    logger.error("traceback: %r", traceback.format_exc())
                    click.secho(str(e), err=True, fg='red')
                    continue

                # Keep track of whether or not the query is mutating. In case
                # of a multi-statement query, the overall query is considered
                # mutating if any one of the component statements is mutating
                mutating = False

                try:
                    logger.debug('sql: %r', document.text)
                    successful = False
                    # Initialized to [] because res might never get initialized
                    # if an exception occurs in vexecute.run(). Which causes
                    # finally clause to fail.
                    res = []
                    start = time()
                    # Run the query.
                    res = vexecute.run(document.text, self.vspecial)
                    duration = time() - start

                    file_output = None
                    stdout_output = []

                    total = 0
                    for title, cur, headers, status, force_stdout in res:
                        logger.debug("headers: %r", headers)
                        logger.debug("rows: %r", cur)
                        logger.debug("status: %r", status)
                        start = time()
                        threshold = 1000
                        if (is_select(status) and
                                cur and cur.rowcount > threshold):
                            click.secho('The result set has more than %s rows.'
                                        % threshold, fg='red')
                            if not click.confirm('Do you want to continue?'):
                                click.secho("Aborted!", err=True, fg='red')
                                break

                        formatted = format_output(title, cur, headers, status,
                                                  self.table_format,
                                                  self.vspecial.expanded_output,
                                                  self.vspecial.aligned,
                                                  self.vspecial.show_header)

                        if self.vspecial.output is not sys.stdout:
                            file_output = self.vspecial.output

                        if force_stdout or not file_output:
                            output = stdout_output
                        else:
                            output = file_output

                        write_output(output, formatted)

                        if hasattr(cur, 'rowcount'):
                            if self.vspecial.show_header:
                                if cur.rowcount == 1:
                                    write_output(output, '(1 row)')
                                elif headers:
                                    write_output(output, '(%d rows)' % cur.rowcount)
                            if document.text.startswith('\\') and cur.rowcount == 0:
                                stdout_output = ['No matching relations found.']
                        end = time()
                        total += end - start
                        mutating = mutating or is_mutating(status)

                except KeyboardInterrupt:
                    # Restart connection to the database
                    vexecute.connect()
                    logger.debug("cancelled query, sql: %r", document.text)
                    click.secho("cancelled query", err=True, fg='red')
                except NotImplementedError:
                    click.secho('Not Yet Implemented.', fg="yellow")
                except errors.ConnectionError as e:
                    reconnect = True
                    if ('Connection is closed' in utf8tounicode(e.args[0])):
                        reconnect = click.prompt('Connection reset. Reconnect (Y/n)',
                                show_default=False, type=bool, default=True)
                        if reconnect:
                            try:
                                vexecute.connect()
                                click.secho('Reconnected!\nTry the command again.', fg='green')
                            except errors.DatabaseError as e:
                                click.secho(str(e), err=True, fg='red')
                    else:
                        logger.error("sql: %r, error: %r", document.text, e)
                        logger.error("traceback: %r", traceback.format_exc())
                        click.secho(str(e), err=True, fg='red')
                except Exception as e:
                    logger.error("sql: %r, error: %r", document.text, e)
                    logger.error("traceback: %r", traceback.format_exc())
                    click.secho(str(e), err=True, fg='red')
                else:
                    successful = True
                    if stdout_output:
                        output = '\n'.join(stdout_output)
                        try:
                            click.echo_via_pager(output)
                        except KeyboardInterrupt:
                            pass

                    if file_output:
                        try:
                            file_output.flush()
                        except KeyboardInterrupt:
                            pass
                    if self.vspecial.timing_enabled:
                        print('Time: command: %0.03fs, total: %0.03fs' % (duration, total))

                    # Refresh the table names and column names if necessary.
                    if need_completion_refresh(document.text):
                        self.refresh_completions(need_completion_reset(document.text))

                    # Refresh search_path to set default schema.
                    if need_search_path_refresh(document.text):
                        logger.debug('Refreshing search path')
                        with self._completer_lock:
                            self.completer.set_search_path(vexecute.search_path())
                        logger.debug('Search path: %r', self.completer.search_path)

                query = Query(document.text, successful, mutating)
                self.query_history.append(query)

        except EOFError:
            print ('Goodbye!')
        finally:  # Reset the less opts back to original.
            logger.debug('Restoring env var LESS to %r.', original_less_opts)
            os.environ['LESS'] = original_less_opts

    def adjust_less_opts(self):
        less_opts = os.environ.get('LESS', '')
        self.logger.debug('Original value for LESS env var: %r', less_opts)
        os.environ['LESS'] = '-RXF'

        return less_opts

    def refresh_completions(self, reset=False):
        if reset:
            with self._completer_lock:
                self.completer.reset_completions()
        self.completion_refresher.refresh(self.vexecute, self.vspecial,
                                          self._on_completions_refreshed)
        return [(None, None, None,
                'Auto-completion refresh started in the background.', True)]

    def _on_completions_refreshed(self, new_completer):
        self._swap_completer_objects(new_completer)

        if self.cli:
            # After refreshing, redraw the CLI to clear the statusbar
            # "Refreshing completions..." indicator
            self.cli.request_redraw()

    def _swap_completer_objects(self, new_completer):
        """Swap the completer object in cli with the newly created completer.
        """
        with self._completer_lock:
            self.completer = new_completer
            # When pgcli is first launched we call refresh_completions before
            # instantiating the cli object. So it is necessary to check if cli
            # exists before trying the replace the completer object in cli.
            if self.cli:
                self.cli.current_buffer.completer = new_completer

    def get_completions(self, text, cursor_positition):
        with self._completer_lock:
            return self.completer.get_completions(
                Document(text=text, cursor_position=cursor_positition), None)


@click.command()
# Default host is '' so psycopg2 can default to either localhost or unix socket
@click.option('-h', '--host', default='localhost', show_default=True,
              help='Database server host address')
@click.option('-p', '--port', default=5433, show_default=True, type=int,
              help='Database server port')
@click.option('-U', '--user', default=getpass.getuser(), show_default=True,
              help='Database username')
@click.option('-W', '--prompt-password', 'prompt_passwd', is_flag=True,
              default=False, show_default=True, help='Prompt for password')
@click.option('-w', '--password', default='', show_default=True,
              help='Database password')
@click.option('-v', '--version', is_flag=True, help='Print version and exit')
@click.option('--vclirc', default='~/.vclirc', show_default=True,
              help='Location of .vclirc file')
@click.argument('database', nargs=1, default='')
def cli(database, host, port, user, prompt_passwd, password, version, vclirc):
    if version:
        click.echo('Version: %s' % __version__)
        sys.exit(0)

    if prompt_passwd and not password:
        password = click.prompt('Password', hide_input=True,
                                show_default=False, type=str)

    vcli = VCli(vclirc_file=vclirc)

    # Choose which ever one has a valid value
    database = database or os.getenv('VERTICA_URL', '')

    if '://' in database:
        vcli.connect_uri(database)
    else:
        vcli.connect(database, host, user, port, password)

    vcli.logger.debug('Launch Params: \n'
                      '\tdatabase: %r'
                      '\tuser: %r'
                      '\thost: %r'
                      '\tport: %r', database, user, host, port)
    vcli.run_cli()


def format_output(title, cur, headers, status, table_format, expanded=False,
                  aligned=True, show_header=True):
    output = []
    if title:  # Only print the title if it's not None.
        output.append(title)
    if cur and headers:
        headers = [utf8tounicode(x) for x in headers]

        if hasattr(cur, 'iterate'):
            rows = cur.iterate()
        else:
            rows = cur

        if expanded:
            output.append(expanded_table(rows, headers))
        else:
            if aligned:
                numalign, stralign = 'decimal', 'left'
                tablefmt = table_format
            else:
                numalign, stralign = None, None
                tablefmt = vtablefmt.vsv_unaligned
            if not show_header:
                headers = []
            output.append(tabulate(rows, headers, numalign=numalign, stralign=stralign,
                                   tablefmt=tablefmt, missingval=''))
    if status:  # Only print the status if it's not None.
        output.append(status)
    return output


def need_completion_refresh(queries):
    """Determines if the completion needs a refresh by checking if the sql
    statement is an alter, create, drop or change db."""
    for query in sqlparse.split(queries):
        try:
            first_token = query.split()[0]
            return first_token.lower() in ('alter', 'create', 'use', '\\c',
                                           '\\connect', 'drop')
        except Exception:
            return False


def need_completion_reset(queries):
    """Determines if the statement is a database switch such as 'use' or '\\c'.
    When a database is changed the existing completions must be reset before we
    start the completion refresh for the new database.
    """
    for query in sqlparse.split(queries):
        try:
            first_token = query.split()[0]
            if first_token.lower() in ('use', '\\c', '\\connect'):
                return True
        except Exception:
            return False


def need_search_path_refresh(sql):
    """Determines if the search_path should be refreshed by checking if the
    sql has 'set search_path'."""
    return 'set search_path' in sql.lower()


def is_mutating(status):
    """Determines if the statement is mutating based on the status."""
    if not status:
        return False

    mutating = set(['insert', 'update', 'delete', 'alter', 'create', 'drop'])
    return status.split(None, 1)[0].lower() in mutating


def is_select(status):
    """Returns true if the first word in status is 'select'."""
    if not status:
        return False
    return status.split(None, 1)[0].lower() == 'select'


def quit_command(sql):
    return (sql.strip().lower() == 'exit'
            or sql.strip().lower() == 'quit'
            or sql.strip() == '\q'
            or sql.strip() == ':q')


def write_output(out, content):
    if hasattr(out, 'write'):  # out is a file object
        if isinstance(content, basestring):
            out.write(content + '\n')
        else:
            out.write('\n'.join(content) + '\n')
    elif isinstance(out, list):
        if isinstance(content, basestring):
            out.append(content)
        else:  # Assume content is a list
            out.extend(content)
    else:
        raise TypeError("unsupported output type '%s'" % type(out).__name__)


if __name__ == "__main__":
    cli()
