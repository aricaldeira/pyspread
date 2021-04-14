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

try:
    from pyspread.dialogs import GridShapeDialog
except ImportError:
    from dialogs import GridShapeDialog


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

    param_file_new = [
        ((1000, 100, 3), (1000, 100, 3), None),
        ((100, 100, 3), (100, 100, 3), None),
        ((10000000, 100, 3), (1000, 100, 3),
         "Error: Grid shape (10000000, 100, 3) exceeds (1000000, 100000, 100)."
         ),
        (None, (1000, 100, 3), None),
    ]

    @pytest.mark.parametrize("shape, res, msg", param_file_new)
    def test_file_new(self, shape, res, msg, monkeypatch):
        """Unit test for file_new"""

        monkeypatch.setattr(GridShapeDialog, "shape", shape)
        self.workflows.file_new()

        assert main_window.grid.model.shape == res
        assert main_window.grid.current == (0, 0, 0)
        assert main_window.settings.last_file_input_path == Path.home()
        assert main_window.settings.changed_since_save is False
        assert main_window.safe_mode is False
        if msg:
            assert main_window.statusBar().currentMessage() == msg

        monkeypatch.setattr(GridShapeDialog, "shape",
                            main_window.settings.shape)
        self.workflows.file_new()

    param_count_file_lines = [
        ("", 0, "counttest.txt", None),
        ("\n"*100, 100, "counttest.txt", None),
        ("Test"*100, 0, "counttest.txt", None),
        ("Test\n"*10, 10, "counttest.txt", None),
        ("Test\n"*10, None, "false_filename.txt", "Error"),
    ]

    @pytest.mark.parametrize("txt, res, filename, msg", param_count_file_lines)
    def test_count_file_lines(self, txt, res, filename, msg, tmpdir):
        """Unit test for count_file_lines"""

        tmpfile = tmpdir / "counttest.txt"
        tmpfile.write_text(txt, "utf-8")
        testfile = tmpdir / filename
        assert self.workflows.count_file_lines(testfile) == res
        if msg:
            assert str(testfile) in main_window.statusBar().currentMessage()
        tmpfile.remove()
