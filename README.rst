vcli: A REPL for Vertica
========================

|Build Status| |PyPI|

A Vertica_ client that does auto-completion and syntax highlighting, based on
pgcli_.

.. image:: screenshots/vcli.gif


Installation
------------

Just install it like a regular Python package::

    $ pip install vcli

You'll probably see some permission errors if you're installing it on the
system-wide Python. If that's what you want to do, you need to ``sudo``::

    $ sudo pip install vcli

To upgrade vcli, do::

    $ pip install -U vcli


Usage
-----

Connecting to a Database
~~~~~~~~~~~~~~~~~~~~~~~~
::

    $ vcli --help
    Usage: vcli [OPTIONS] [DATABASE]

    Options:
      -h, --host TEXT        Database server host address  [default: localhost]
      -p, --port INTEGER     Database server port  [default: 5433]
      -U, --user TEXT        Database username  [default: CURRENT_USER]
      -W, --prompt-password  Prompt for password  [default: False]
      -w, --password TEXT    Database password  [default: ]
      -v, --version          Print version and exit
      --vclirc TEXT          Location of .vclirc file  [default: ~/.vclirc]
      --help                 Show this message and exit.

**Examples**

Use URL to connect::

    $ vcli vertica://dbadmin:pass@localhost:5433/mydb

Prompt for password::

    $ vcli -h localhost -U dbadmin -W -p 5433 mydb

Don't prompt for password::

    $ vcli -h localhost -U dbadmin -w pass -p 5433 mydb

Use VERTICA_URL environment variable::

    $ VERTICA_URL=vertica://dbadmin:pass@localhost:5433/mydb vcli


Special Commands
~~~~~~~~~~~~~~~~
::

    vcli_demo=> \h
    +---------------------+--------------------------------------+
    | Command             | Description                          |
    |---------------------+--------------------------------------|
    | \#                  | Refresh auto-completions             |
    | \?                  | Show help                            |
    | \a                  | Aligned or unaligned                 |
    | \c[onnect] [DBNAME] | Connect to a new database            |
    | \d [PATTERN]        | List or describe tables              |
    | \dS [PATTERN]       | List system tables                   |
    | \dT [PATTERN]       | List data types                      |
    | \df [PATTERN]       | List functions                       |
    | \dj [PATTERN]       | List projections                     |
    | \dn [PATTERN]       | List schemas                         |
    | \dp [PATTERN]       | List access privileges               |
    | \ds [PATTERN]       | List sequences                       |
    | \dt [PATTERN]       | List tables                          |
    | \dtv [PATTERN]      | List tables and views                |
    | \du [PATTERN]       | List users                           |
    | \dv [PATTERN]       | List views                           |
    | \e [FILE]           | Edit the query with external editor  |
    | \h                  | Show help                            |
    | \i FILE             | Execute commands from file           |
    | \l                  | List databases                       |
    | \n[+] [NAME]        | List or execute named queries        |
    | \nd [NAME]          | Delete a named query                 |
    | \ns NAME QUERY      | Save a named query                   |
    | \o [FILE]           | Output to file or stdout             |
    | \q                  | Quit vcli                            |
    | \refresh            | Refresh auto-completions             |
    | \t                  | Toggle header                        |
    | \timing             | Toggle timing of commands            |
    | \x                  | Toggle expanded output               |
    | \z [PATTERN]        | List access privileges (same as \dp) |
    +---------------------+--------------------------------------+


Thanks
------

Thanks to pgcli_. Most of the hard work, especially the auto-completion part,
were already done well by the pgcli core team. vcli wouldn't be possible if it
weren't for them.


.. |Build Status| image:: https://api.travis-ci.org/dbcli/vcli.svg?branch=master
    :target: https://travis-ci.org/dbcli/vcli

.. |PyPI| image:: https://img.shields.io/pypi/v/vcli.svg
    :target: https://pypi.python.org/pypi/vcli/
    :alt: Latest Version

.. _pgcli: http://pgcli.com
.. _Vertica: http://www.vertica.com/
