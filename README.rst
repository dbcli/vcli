vcli: A REPL for Vertica
========================

A Vertica client that does auto-completion and syntax highlighting, based on
Amjith Ramanujam's pgcli_.


Quick Start
-----------

vcli is not officially released yet, but you can install the latest development
version with pip::

    $ pip install https://github.com/dbcli/vcli/archive/master.zip


Usage
-----

::

    $ vcli [database_name]

    or

    $ vcli vertica://[user[:password]@][netloc][:port][/dbname]

Example:

::

    $ vcli vertica://amjith:pa$$w0rd@example.com:5433/app_db


Thanks
------

Thanks to the pgcli_ Core team. Most of the hard work, especially the
auto-completion part, were already done well by the team. vcli wouldn't be
possible if it weren't for them.


.. _pgcli: http://pgcli.com
