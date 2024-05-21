# -*- coding: utf-8 -*-

APP_NAME = "pyspread"

# Current pyspread version

VERSION = "2.3-beta.1"

try:
    from . import formatting
except ImportError:
    import formatting
