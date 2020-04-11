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
test_grid
=========

Unit tests for grid.py

"""

from contextlib import contextmanager
from os.path import abspath, dirname, join
import sys
from typing import NamedTuple

import pytest

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

app = QApplication([])
main_window = MainWindow()


class TestGrid:
    """Unit tests for Grid in grid.py"""

    grid = main_window.grid

    param_test_row = [(0, 0), (1, 1), (100, 100), (1000, 0), (10000, 0),
                      (-1, 0)]

    @pytest.mark.parametrize("row, res", param_test_row)
    def test_row(self, row, res, monkeypatch):
        """Unit test for row getter and setter"""

        monkeypatch.setattr(self.grid, "row", row)
        assert self.grid.row == res

    param_test_column = [(0, 0), (1, 1), (100, 0), (1000, 0), (10000, 0),
                         (-1, 0)]

    @pytest.mark.parametrize("column, res", param_test_column)
    def test_column(self, column, res, monkeypatch):
        """Unit test for column getter and setter"""

        monkeypatch.setattr(self.grid, "column", column)
        assert self.grid.column == res

    param_test_table = [(0, 0), (1, 1), (3, 0), (-1, 0)]

    @pytest.mark.parametrize("table, res", param_test_table)
    def test_table(self, table, res, monkeypatch):
        """Unit test for table getter and setter"""

        monkeypatch.setattr(self.grid, "table", table)
        assert self.grid.table == res

    @pytest.mark.parametrize("row, row_res", param_test_row)
    @pytest.mark.parametrize("column, column_res", param_test_column)
    def test_current2(self, row, row_res, column, column_res, monkeypatch):
        """Unit test for current getter and setter with 2 parameters"""

        monkeypatch.setattr(self.grid, "current", (row, column))
        assert self.grid.current == (row_res, column_res, 0)

    @pytest.mark.parametrize("row, row_res", param_test_row)
    @pytest.mark.parametrize("column, column_res", param_test_column)
    @pytest.mark.parametrize("table, table_res", param_test_table)
    def test_current3(self, row, row_res, column, column_res, table, table_res,
                      monkeypatch):
        """Unit test for current getter and setter with 3 parameters"""

        monkeypatch.setattr(self.grid, "current", (row, column, table))
        assert self.grid.current == (row_res, column_res, table_res)

    param_test_zoom = [(1.0, 1.0), (2.0, 2.0), (8.0, 8.0), (0.0, 1.0),
                       (100.0, 1.0), (-1.0, 1.0)]

    @pytest.mark.parametrize("zoom, zoom_res", param_test_zoom)
    def test_zoom(self, zoom, zoom_res, monkeypatch):
        """Unit test for zoom getter and setter"""

        monkeypatch.setattr(self.grid, "zoom", zoom)
        assert self.grid.zoom == zoom_res


class TestGridHeaderView:
    """Unit tests for GridHeaderView in grid.py"""

    pass


class TestGridTableModel:
    """Unit tests for GridTableModel in grid.py"""

    model = main_window.grid.model

    param_test_shape = [
        ((1, 1, 1), (1, 1, 1), None),
        ((0, 0, 0), (1000, 100, 3), ValueError),
        ((9999999999, 0, 0), (1000, 100, 3), ValueError),
        ((1000000, 10000, 10), (1000000, 10000, 10), None),
        ((1000, 100, 3), (1000, 100, 3), None),
    ]

    @pytest.mark.parametrize("shape, res, error", param_test_shape)
    def test_shape(self, shape, res, error, monkeypatch):
        """Unit test for shape getter and setter"""

        try:
            monkeypatch.setattr(self.model, "shape", shape)
        except ValueError:
            assert error == ValueError
        else:
            assert error is None
        assert self.model.shape == res

    param_test_code = [
        (0, 0, "", None),
        (0, 0, "None", "None"),
        (0, 0, "2+6", "2+6"),
        (1, 1, "test", "test"),
    ]

    @pytest.mark.parametrize("row, column, code, res", param_test_code)
    def test_code(self, row, column, code, res):
        """Unit test for code"""

        class Index:
            def __init__(self, row: int, column: int):
                self._row = row
                self._column = column

            def row(self) -> int:
                return self._row

            def column(self) -> int:
                return self._column

        self.model.code_array[(row, column, 0)] = code
        index = Index(row, column)
        assert self.model.code(index) == res

    def test_insertRows(self):
        pass

    def test_removeRows(self):
        pass

    def test_insertColumns(self):
        pass

    def test_removeColumns(self):
        pass

    def test_insertTable(self):
        pass

    def test_removeTable(self):
        pass

    def test_font(self):
        pass

    def test_data(self):
        """Unit test for data and setData"""

        pass

    def test_reset(self):
        pass


class TestGridCellNavigator:
    """Unit tests for GridCellNavigator in grid.py"""

    def test_above_keys(self):
        pass

    def test_below_keys(self):
        pass

    def test_left_keys(self):
        pass

    def test_right_keys(self):
        pass

    def test_above_left_key(self):
        pass

    def test_above_right_key(self):
        pass

    def test_below_left_key(self):
        pass

    def test_below_right_key(self):
        pass


class TestGridCellDelegate:
    """Unit tests for GridCellDelegate in grid.py"""

    pass


class TestTableChoice:
    """Unit tests for TableChoice in grid.py"""

    pass
