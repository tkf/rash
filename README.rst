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
   RASH can detect if you are in tmux, screen or Emacs.
#. Session information.  If you go back and forth in some terminals,
   RASH does not loose in which sequence you ran the commands in which
   terminal.

.. [#] If you are curious, checkout ``rash record --help``.


Install
=======
::

   pip install rash


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

**NOT IMPLEMENTED**
All git commands you ran in one week.::

   rash search --time-after "a week ago" "git*"

**NOT IMPLEMENTED**
Some intensive task you ran in the current project that succeeded and
took longer than 30 minutes.::

   rash search --under . --include-exit-code 0 --duration-longer-than 30m

**NOT IMPLEMENTED**
All failed command you ran at this directory.::

   rash search --cwd . --exclude-exit-code 0

**NOT IMPLEMENTED**
Top 5 programs you use most.::

   rash search --limit 5 --sort-program-frequency

**NOT IMPLEMENTED**
Count number of commands you ran in one day::

   rash search --no-unique --time-after "a day ago" | wc -l


Showing detailed information -- ``rash show``
---------------------------------------------

**NOT IMPLEMENTED**
If you give ``--with-id`` to ``rash search`` command, it prints out
ID number for each command history.::

   % rash search --with-id --limit 5 "*git*"
    359  git log
   1253  git help clone
   1677  git help diff
   1678  git diff --word-diff
   1780  git merge

**NOT IMPLEMENTED**
You can see all information associated with a command with
``rash show`` command::

   rash show --full 1677
