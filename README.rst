vcli: A REPL for Vertica
========================

A Vertica client that does auto-completion and syntax highlighting, forked from
Amjith Ramanujam's `pgcli <http://pgcli.com>`_.


Quick Start
-----------

vcli is not officially released yet, but you can install the latest development
version with pip::

    $ pip install https://github.com/eliangcs/vcli/archive/master.zip


Usage
-----

::

    $ vcli [database_name]

    or

    $ vcli vertica://[user[:password]@][netloc][:port][/dbname]

Examples:

::

    $ vcli vertica://amjith:pa$$w0rd@example.com:5433/app_db


Thanks
------

Thanks to Amjith Ramanujam's `pgcli <http://pgcli.com>`_. Most of the hard
work, especially the auto-completion part, were already done wonderfully by
Amjith.
