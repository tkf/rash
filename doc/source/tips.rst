======
 Tips
======

Define Zsh ZLE widget
=====================

You can use the ZLE widget :ref:`rash-zle-isearch` loaded by
:ref:`rash init` to define your own modified widget.  It takes
arguments and passes them to :ref:`rash isearch` directly.  Here
is a recipe for "Do What I Mean" search:

.. sourcecode:: sh

   rash-zle-dwim(){
       rash-zle-isearch --query-template "-x 0 -d . @ {0} "
   }
   zle -N rash-zle-dwim
   bindkey "^Xs" rash-zle-dwim


In the :term:`configuration file`, you should define an alias
called ``@`` like this (see also |search.alias|)::

   config.search.alias['@'] = [...]  # some complex query

.. |search.alias| replace::
   :attr:`config.search.alias <rash.config.SearchConfig.alias>`
