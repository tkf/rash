=============================
 Rash Advances Shell History
=============================


.. warning:: UNDER CONSTRUCTION!

   It is still useful, but not all of the functions mentioned below
   are implemented.


.. sidebar:: Links:

   * `Repository <https://github.com/tkf/rash>`_ (at GitHub)
   * `Issue tracker <https://github.com/tkf/rash/issues>`_ (at GitHub)
   * `PyPI <http://pypi.python.org/pypi/rash>`_
   * `Travis CI <https://travis-ci.org/#!/tkf/rash>`_ |build-status|


What is this?
=============

Shell history is useful.  But it can be more useful if it logs more
data points.  For example, if you forget which `make` target to run
for certain project, you'd want to search shell commands that are
ran in particular directory.  Wouldn't it be nice if you can do this?::

   rash search --cwd . "make*"

RASH records many data points and they are stored in SQLite database.
Here is a list of recorded information [#]_.

#. Current directory (``$PWD``).
#. Exit code (``$?``)
#. Exit code of pipes (``$PIPESTATUS`` / ``$pipestatus``)
#. The time command is started and terminated.
#. Environment variable (``$PATH``, ``$SHELL``, ``$TERM``, ``$HOST``, etc.)
#. Real terminal.  ``$TERM`` is used to fake programs.
   RASH can detect if you are in tmux, byobu, screen, gnome-terminal, etc.
#. Session information.  If you go back and forth in some terminals,
   RASH does not loose in which sequence you ran the commands in which
   terminal.

.. [#] If you are curious, checkout ``rash record --help``.


Install
=======

RASH is written in Python.  The easiest way to install is to use `pip`
(or `easy_install`, if you wish).  You may need `sudo` for installing
it in a system directory.::

   pip install rash

RASH tested against Python 2.6, 2.7 and 3.2.  However, as watchdog_
does not work with Python 3, you can't get full power of RASH with
Python 3.


Setup
=====
Add this to your `.zshrc` or `.bashrc`.  That's all.::

   source "$(rash init)"

For more information, see ``rash init --help``.


Usage
=====

Searching history -- ``rash search``
------------------------------------

After your shell history is accumulated by RASH, it's the time to
make use of the history!  See ``rash search --help`` for detailed
information.  Here is some examples.

Forget how to run automated test for the current project?::

   rash search --cwd . "*test*" "tox*"

All git commands you ran in one week.::

   rash search --time-after "1 week ago" "git*"

Some intensive task you ran in the current project that succeeded and
took longer than 30 minutes.::

   rash search --cwd-under . --include-exit-code 0 --duration-longer-than 30m

**NOT IMPLEMENTED**
What did I do after `cd`-ing to some directory?::

   rash search --after-context 5 "cd SOME-DIRECTORY"

All failed commands you ran at this directory.::

   rash search --cwd . --exclude-exit-code 0

**NOT IMPLEMENTED**
Top 5 programs you use most.::

   rash search --limit 5 --sort-by-program-frequency

Count number of commands you ran in one day::

   rash search --limit -1 --no-unique --time-after "1 day ago" | wc -l


Showing detailed information -- ``rash show``
---------------------------------------------

If you give ``--with-command-id`` to ``rash search`` command, it prints out
ID number for each command history.::

   % rash search --with-command-id --limit 5 "*git*"
    359  git log
   1253  git help clone
   1677  git help diff
   1678  git diff --word-diff
   1780  git merge

You can see all information associated with a command with
``rash show`` command::

   rash show 1677


Dependency
==========

Python modules:

* watchdog_ [#nopy3k]_
* parsedatetime_ [#nopy3k]_

.. _watchdog: http://pypi.python.org/pypi/watchdog/
.. _parsedatetime: http://pypi.python.org/pypi/parsedatetime/

.. [#nopy3k] These modules do not support Python 3.
             They are not installed in if you use Python 3
             and related functionality is disabled.

Platforms
---------

UNIX-like systems
  RASH is tested in Linux and I am using in Linux.
  It should work in other UNIX-like systems like BSD.

Mac OS
  I guess it works.  Not tested.

MS Windows
  Probably no one wants to use a shell tool in windows, but I
  try to avoid stuff that is platform specific.  Only the
  daemon launcher will not work on Windows but there is several
  ways to avoid using it.  See ``rash init --help``.


Design principle
================

RASH's design is focused on sparseness.  There are several stages
of data transformation until you see the search result, and they
are done by separated processes.

First, `rash record` command dumps shell history in raw JSON record.
This part of program does not touches to DB to make process very fast.
As there is no complex transformation in this command, probably in the
future version is is better to rewrite it entirely in shell function.

Second, `rash daemon` runs in background and watches the directory to
store JSON record.  When JSON record arrives, it insert the data into
database.

`rash record` and `rash daemon` are setup by simple shell snippet
``source $(rash init)``.

Finally, you can search through command history using search interface
such as `rash search`.  This search is very fast as you don't read
all JSON records in separated files.

::

   +-------+         +--------+         +--------+         +--------+
   | Shell |         | Raw    |         | SQLite |         | Search |
   | hooks |-------->| JSON   |-------->|   DB   |-------->| result |
   +-------+         | record |         +--------+         +--------+
                     +--------+

           `rash record`      `rash daemon`      `rash search`
                                                  `rash show`

           \------------------------------/      \------------/
              `rash init` setups them           search interface

License
=======

RASH is licensed under MIT License.


.. Travis CI build status badge
.. |build-status|
   image:: https://secure.travis-ci.org/tkf/rash.png?branch=master
   :target: http://travis-ci.org/tkf/rash
   :alt: Build Status
