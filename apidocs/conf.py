# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

try:
    from pyspread.settings import VERSION
except ImportError:
    sys.path.insert(0, os.path.abspath('../'))
    from pyspread.settings import VERSION

project = 'pyspread'
copyright = 'Martin Manns and the pyspread team '
author = 'Martin Manns and the pyspread team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'recommonmark'
]

templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', "requirements.txt"]

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

primary_domain = 'py'
highlight_language = 'py'

release = VERSION

# Were autodoc so set stuff aphabetically
autodoc_member_order = "alphabetical"

# Flags for the stuff to document..
autodoc_default_flags = [
    'members',
    'undoc-members',
    'private-members',
    #'special-members',
    'inherited-members',
    #"exclude-members ",
    'show-inheritance'
]

autoclass_content = "both"
autosummary_generate = True



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'

html_static_path = ['_static']
html_css_files = [
    'css/w3.css',
]

html_title = 'pyspread API docs'
html_short_title = "pyspread"
html_favicon = "_static/pyspread.png"


html_sidebars = {
   '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
   'using/windows': ['windowssidebar.html', 'searchbox.html'],
}


# If true, links to the reST sources are added to the pages.
#
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#
html_show_copyright = False

html_context = {"git_repos_url": "https://gitlab.com/pyspread/pyspread"}

intersphinx_mapping = {
    'python': ('http://docs.python.org/3', None),
    'numpy': ('http://docs.scipy.org/doc/numpy', None),
    'scipy': ('http://docs.scipy.org/doc/scipy/reference', None),
    'matplotlib': ('https://matplotlib.org/', None)
}
