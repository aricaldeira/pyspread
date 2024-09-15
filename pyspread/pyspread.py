#!/usr/bin/python3
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

pyspread
========

- Main Python spreadsheet application
- Run this script to start the application.

**Provides**

* MainApplication: Initial command line operations and application launch
* :class:`MainWindow`: Main windows class

"""

import logging
import os
import sys
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

try:
    from pyspread.cli import PyspreadArgumentParser
    from pyspread.main_window import MainWindow

except ImportError:
    from cli import PyspreadArgumentParser
    from main_window import MainWindow


LICENSE = "GNU GENERAL PUBLIC LICENSE Version 3"

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def excepthook(exception_type, exception_value, exception_traceback):
    """Exception hook that prevents pyspread from crashing on exceptions"""

    traceback_msg = "".join(traceback.format_exception(exception_type,
                                                       exception_value,
                                                       exception_traceback))
    print(f"Error: {traceback_msg}\n")


def main():
    """Pyspread main"""

    sys.excepthook = excepthook

    parser = PyspreadArgumentParser()
    args, _ = parser.parse_known_args()

    logging.basicConfig(level=args.loglevel)

    app = QApplication(sys.argv)
    app.setDesktopFileName("io.gitlab.pyspread.pyspread")
    main_window = MainWindow(args.file, default_settings=args.default_settings)

    main_window.show()

    app.exec()

    sys.exit()


if __name__ == '__main__':
    main()
