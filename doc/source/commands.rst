=============================
 RASH command line interface
=============================


Search interface
================

.. _rash search:

:program:`rash search`
----------------------
.. program-output:: rash search --help


.. _rash show:

:program:`rash show`
--------------------
.. program-output:: rash show --help


.. _rash isearch:

:program:`rash isearch`
-----------------------
.. program-output:: rash isearch --help


System setup interface
======================

.. _rash init:

:program:`rash init`
--------------------
.. program-output:: rash init --help


.. _rash daemon:

:program:`rash daemon`
----------------------
.. program-output:: rash daemon --help


.. _rash locate:

:program:`rash locate`
----------------------
.. program-output:: rash locate --help


.. _rash version:

:program:`rash version`
-----------------------
.. program-output:: rash version --help


Low level commands
==================

.. _rash record:

:program:`rash record`
----------------------

.. program-output:: rash record --help


.. _rash index:

:program:`rash index`
---------------------

.. program-output:: rash index --help


ZSH functions
=============

.. _rash-zle-isearch:

:program:`rash-zle-isearch`
---------------------------

To setup :kbd:`Ctrl-x r` to start :ref:`rash isearch`, add this to
your :file:`.zshrc`:

.. sourcecode:: sh

   bindkey "^Xr" rash-zle-isearch
