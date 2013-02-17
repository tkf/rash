# -*- coding: utf-8 -*-

import os
from os.path import dirname
import sys

sys.path.insert(0, dirname(dirname(dirname(__file__))))

# To make command "rash" runnable
os.environ['PATH'] = dirname(__file__) + ':' + os.environ['PATH']


# -- General configuration ------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinxcontrib.programoutput',
]

templates_path = []  # ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'RASH'
copyright = u'2013, Takafumi Arakaki'

# The short X.Y version.
version = '0.1.2'
# The full version, including alpha/beta/rc tags.
release = '0.1.2.dev2'

exclude_patterns = []

pygments_style = 'sphinx'


# -- Options for HTML output ----------------------------------------------
html_theme = 'default'
html_static_path = []  # ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'RASHdoc'


# -- Options for LaTeX output ---------------------------------------------
latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'RASH.tex', u'RASH Documentation',
   u'Takafumi Arakaki', 'manual'),
]


# -- Options for manual page output ---------------------------------------
# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'rash', u'RASH Documentation',
     [u'Takafumi Arakaki'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------
# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'RASH', u'RASH Documentation',
   u'Takafumi Arakaki', 'RASH', 'One line description of project.',
   'Miscellaneous'),
]


# -- Options for extensions -----------------------------------------------

autodoc_member_order = 'bysource'
