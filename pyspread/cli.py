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

* :func:`check_mandatory_dependencies`:
* :class:`PathAction`:
* :class:`CommandLineParser`:

"""

from argparse import ArgumentParser
from pathlib import Path
import logging
import sys

try:
    import PyQt6.QtSvg as pyqtsvg
except ImportError:
    pyqtsvg = None

try:
    from pyspread.__init__ import APP_NAME, VERSION
    from pyspread.installer import REQUIRED_DEPENDENCIES
except ImportError:
    from __init__ import APP_NAME, VERSION
    from installer import REQUIRED_DEPENDENCIES


def check_mandatory_dependencies():
    """Checks mandatory dependencies and exits if they are not met"""

    def dependency_warning(message: str):
        """Print warning message to stdout

        :param message: Warning message to be displayed

        """

        sys.stdout.write(f'Warning: {message}\n')

    # Check Python version
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    if major < 3 or major == 3 and minor < 6:
        msg = f"Python has version {major}.{minor}.{micro}" + \
               " but ≥ 3.6 is required."
        dependency_warning(msg)

    for module in REQUIRED_DEPENDENCIES:
        if module.is_installed() is None or not module.is_installed():
            dependency_warning(f"Required module {module.name} not found.")
        elif module.version < module.required_version:
            msg = f"Module {module.name} has version {module.version}" + \
                  f"but {module.required_version} is required."
            dependency_warning(msg)
    if pyqtsvg is None:
        # Import of mandatory module failed
        msg = "Required module PyQt6.QtSvg not found."
        dependency_warning(msg)


class PyspreadArgumentParser(ArgumentParser):
    """Parser for the command line"""

    def __init__(self):
        check_mandatory_dependencies()

        description = "pyspread is a non-traditional spreadsheet that is " \
                      "based on and written in the programming language " \
                      "Python."

        super().__init__(prog=APP_NAME, description=description)

        self.add_argument('--version', action='version', version=VERSION)

        self.add_argument('--default-settings', action='store_true',
                          help='start with default settings and save them on '
                               'exit')

        self.add_argument('-d', '--debug',
                          help="Print debug information",
                          action="store_const", dest="loglevel",
                          const=logging.DEBUG, default=logging.WARNING)

        self.add_argument('-v', '--verbose',
                          help="Print verbose information",
                          action="store_const", dest="loglevel",
                          const=logging.INFO)

        self.add_argument('file', type=Path, nargs='?', default=None,
                          help='open pyspread file in pys or pysu format')
