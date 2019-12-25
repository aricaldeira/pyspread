# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

**Provides**

* :class:`CommandLineParser`:

"""

import argparse

from src import APP_NAME, VERSION

# Usage:
# pyspread - Launches pyspread with standard size grid
# pyspread <infile> - also opens infile
# pyspread -k --key <key> - uses key instead of settings key
# pyspread -d --dimensions <rows> <columns> <tables> - custom size grid
# pyspread -u --updatetimeinterval <time> -
#                    periodic updates enabled and time update interval
# pyspread -v - display version string


class ArgumentParser(argparse.ArgumentParser):
    """Parser for the command line

    Usage
    -----

    pyspread - Launches pyspread with standard size grid
    pyspread <infile> - Launches pyspread and opens infile
    pyspread --version - display version string

    """

    def __init__(self):

        description = "pyspread is a non-traditional spreadsheet that is " \
                      "based on and written in the programming language " \
                      "Python."

        super().__init__(prog=APP_NAME, description=description)

        self.add_argument('--version', action='version', version=VERSION)
        self.add_argument('file', nargs='?', default=None,
                          help='open pyspread file in pys or pysu format')
