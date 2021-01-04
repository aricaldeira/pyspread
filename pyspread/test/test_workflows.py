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
test_workflows
==============

Unit tests for workflows.py

"""

from contextlib import contextmanager
from os.path import abspath, dirname, join
from pathlib import Path
import sys

import pytest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

PYSPREADPATH = abspath(join(dirname(__file__) + "/.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)


with insert_path(PYSPREADPATH):
    from ..pyspread import MainWindow


app = QApplication.instance()
if app is None:
    app = QApplication([])
main_window = MainWindow()


class TestWorkflows:
    """Unit tests for Workflows in workflows.py"""

    workflows = main_window.workflows

    def test_disable_entryline_updates(self):
        """Unit test for disable_entryline_updates"""

        assert main_window.entry_line.updatesEnabled()

        with self.workflows.disable_entryline_updates():
            assert not main_window.entry_line.updatesEnabled()

        assert main_window.entry_line.updatesEnabled()

    def test_busy_cursor(self):
        """Unit test for busy_cursor"""

        assert QApplication.overrideCursor() != Qt.WaitCursor

        with self.workflows.busy_cursor():
            assert QApplication.overrideCursor() == Qt.WaitCursor

        assert QApplication.overrideCursor() != Qt.WaitCursor

    def test_prevent_updates(self):
        """Unit test for prevent_updates"""

        assert not main_window.prevent_updates

        with self.workflows.prevent_updates():
            assert main_window.prevent_updates

        assert not main_window.prevent_updates

    def test_reset_changed_since_save(self):
        """Unit test for reset_changed_since_save"""

        main_window.settings.changed_since_save = True
        self.workflows.reset_changed_since_save()
        assert not main_window.settings.changed_since_save

    param_update_main_window_title = [
        (Path.home(), "pyspread"),
        (Path("/test.pys"), "test.pys - pyspread"),
    ]

    @pytest.mark.parametrize("path, title", param_update_main_window_title)
    def test_update_main_window_title(self, path, title):
        """Unit test for update_main_window_title"""

        main_window.settings.last_file_input_path = path
        self.workflows.update_main_window_title()
        assert main_window.windowTitle() == title
