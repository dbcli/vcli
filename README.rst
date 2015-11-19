vcli: A REPL for Vertica
========================

|Build Status|

A Vertica_ client that does auto-completion and syntax highlighting, based on
pgcli_.


Installation
------------

Just install it like a regular Python package::

    pip install vcli


Usage
-----
::

    Usage: vcli [OPTIONS] [DATABASE]

    Options:
      -h, --host TEXT        Database server host address  [default: localhost]
      -p, --port INTEGER     Database server port  [default: 5433]
      -U, --user TEXT        Database username  [default: eliang]
      -W, --prompt-password  Prompt for password  [default: False]
      -w, --password TEXT    Database password  [default: ]
      -v, --version          Print version and exit
      --vclirc TEXT          Location of .vclirc file  [default: ~/.vclirc]
      --help                 Show this message and exit.

Examples::

    # Use URL to connect
    vcli vertica://dbadmin:pass@localhost:5433/mydb

    # Prompt for password
    vcli -h localhost -U dbadmin -W -p 5433 mydb

    # Don't prompt for password
    vcli -h localhost -U dbadmin -w pass -p 5433 mydb

    # Use VERTICA_URL environment variable
    VERTICA_URL=vertica://dbadmin:pass@localhost:5433/mydb vcli


Thanks
------

Thanks to pgcli_. Most of the hard work, especially the auto-completion part,
were already done well by the pgcli core team. vcli wouldn't be possible if it
weren't for them.


.. |Build Status| image:: https://api.travis-ci.org/dbcli/vcli.svg?branch=master
    :target: https://travis-ci.org/dbcli/vcli

.. _pgcli: http://pgcli.com
.. _Vertica: http://www.vertica.com/
