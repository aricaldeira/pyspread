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

from argparse import Action, ArgumentParser
from pathlib import Path

from src import APP_NAME, VERSION


class PathAction(Action):
    """Action that handles paths with spaces and provides a pathlib Path"""

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            setattr(namespace, self.dest, Path(" ".join(values)))
        else:
            setattr(namespace, self.dest, None)


class ArgumentParser(ArgumentParser):
    """Parser for the command line"""

    def __init__(self):

        description = "pyspread is a non-traditional spreadsheet that is " \
                      "based on and written in the programming language " \
                      "Python."

        # Override usage because of the PathAction fix for paths with spaces
        usage = "{} [-h] [--version] [file]".format(APP_NAME)

        super().__init__(prog=APP_NAME, description=description, usage=usage)

        self.add_argument('--version', action='version', version=VERSION)
        self.add_argument('file', action=PathAction, nargs="*",
                          help='open pyspread file in pys or pysu format')
