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
test_actions
============

Unit tests for actions in pyspread

"""

import py.test as pytest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from src.pyspread import MainWindow


class TestActions:
    """Unit tests for  file actions

    The tests launch a hidden application instance and check if the
    actions behave as they should from a user perspective.

    """

    def setup_method(self):
        """Sets up a basic pyspread instance"""

        self.app = QApplication([])

        self.main_window = MainWindow(self.app, unit_test=True)

    def teardown_method(self):
        """Sets up a basic pyspread instance as self.app"""

        self.app.quit()

    param_test_file_new = [
        ((1, 1, 1), (1, 1, 1)),
        ((0, 0, 0), (1000, 100, 3)),
        ((9999999999, 0, 0), (1000, 100, 3)),
        ((1000000, 10000, 10), (1000000, 10000, 10)),
    ]

    @pytest.mark.parametrize("shape, res", param_test_file_new)
    def test_file_new(self, shape, res):
        """Unit test for File -> New"""

        self.main_window.unit_test_data = shape
        self.main_window.main_window_actions.new.trigger()
        assert self.main_window.grid.model.shape == res
