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
    from ..grid import GridCellNavigator

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

    param_test_insertRows = [
        (0, 5, (0, 0, 0), "0", (5, 0, 0), "0"),
        (0, 5, (0, 0, 0), "0", (0, 0, 0), None),
        (0, 0, (0, 0, 0), "0", (0, 0, 0), "0"),
        (3, 5, (0, 0, 0), "0", (0, 0, 0), "0"),
        (0, 500, (0, 0, 0), "0", (500, 0, 0), "0"),
    ]

    @pytest.mark.parametrize("row, count, key, code, reskey, res",
                             param_test_insertRows)
    def test_insertRows(self, row, count, key, code, reskey, res):
        """Unit test for insertRows"""

        self.model.code_array[key] = code
        self.model.insertRows(row, count)
        assert self.model.code_array(reskey) == res

    param_test_removeRows = [
        (0, 5, (5, 0, 0), "0", (0, 0, 0), "0"),
        (0, 5, (0, 0, 0), "0", (0, 0, 0), None),
        (0, 0, (0, 0, 0), "0", (0, 0, 0), "0"),
        (3, 5, (0, 0, 0), "0", (0, 0, 0), "0"),
        (0, 499, (500, 0, 0), "0", (1, 0, 0), "0"),
    ]

    @pytest.mark.parametrize("row, count, key, code, reskey, res",
                             param_test_removeRows)
    def test_removeRows(self, row, count, key, code, reskey, res):
        """Unit test for removeRows"""

        self.model.code_array[key] = code
        self.model.removeRows(row, count)
        assert self.model.code_array(reskey) == res

    param_test_insertColumns = [
        (0, 5, (0, 0, 0), "0", (0, 5, 0), "0"),
        (0, 5, (0, 0, 0), "0", (0, 0, 0), None),
        (0, 0, (0, 0, 0), "0", (0, 0, 0), "0"),
        (3, 5, (0, 0, 0), "0", (0, 0, 0), "0"),
        (0, 50, (0, 0, 0), "0", (0, 50, 0), "0"),
    ]

    @pytest.mark.parametrize("column, count, key, code, reskey, res",
                             param_test_insertColumns)
    def test_insertColumns(self, column, count, key, code, reskey, res):
        """Unit test for insertColumns"""

        self.model.code_array[key] = code
        self.model.insertColumns(column, count)
        assert self.model.code_array(reskey) == res

    param_test_removeColumns = [
        (0, 2, (0, 2, 0), "0", (0, 0, 0), "0"),
        (0, 2, (0, 0, 0), "0", (0, 0, 0), None),
        (0, 0, (0, 0, 0), "0", (0, 0, 0), "0"),
        (3, 1, (0, 0, 0), "0", (0, 0, 0), "0"),
    ]

    @pytest.mark.parametrize("column, count, key, code, reskey, res",
                             param_test_removeColumns)
    def test_removeColumns(self, column, count, key, code, reskey, res):
        """Unit test for removeColumns"""

        self.model.code_array[key] = code
        self.model.removeColumns(column, count)
        assert self.model.code_array(reskey) == res

    param_test_insertTable = [
        (0, (0, 0, 0), "0", (0, 0, 1), "0"),
        (0, (0, 0, 0), "0", (0, 0, 0), None),
        (2, (0, 0, 0), "0", (0, 0, 0), "0"),
    ]

    @pytest.mark.parametrize("table, key, code, reskey, res",
                             param_test_insertTable)
    def test_insertTable(self, table, key, code, reskey, res):
        """Unit test for insertTable"""

        self.model.code_array[key] = code
        self.model.insertTable(table)
        assert self.model.code_array(reskey) == res

    param_test_removeTable = [
        (0, (0, 0, 1), "0", (0, 0, 0), "0"),
        (0, (0, 0, 0), "0", (0, 0, 0), None),
        (1, (0, 0, 2), "0", (0, 0, 1), "0"),
    ]

    @pytest.mark.parametrize("table, key, code, reskey, res",
                             param_test_removeTable)
    def test_removeTable(self, table, key, code, reskey, res):
        """Unit test for removeTable"""

        self.model.code_array[key] = code
        self.model.removeTable(table)
        assert self.model.code_array(reskey) == res

    def test_reset(self):
        """Unit test for reset"""

        self.model.reset()

        assert not self.model.code_array.dict_grid
        assert not self.model.code_array.dict_grid.cell_attributes
        assert not self.model.code_array.row_heights
        assert not self.model.code_array.col_widths
        assert not self.model.code_array.macros
        assert not self.model.code_array.result_cache


class TestGridCellNavigator:
    """Unit tests for GridCellNavigator in grid.py"""

    param_test_above_keys = [
        ((0, 0, 0), [(-1, 0, 0)]),
        ((20, 0, 0), [(19, 0, 0)]),
        ((20, 0, 2), [(19, 0, 2)]),
        ((20, 2, 2), [(19, 2, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_keys)
    def test_above_keys(self, key, res):
        """Unit test for above_keys"""

        cell = GridCellNavigator(main_window, key)
        assert set(cell.above_keys()) == set(res)

    param_test_below_keys = [
        ((0, 0, 0), [(1, 0, 0)]),
        ((1000, 0, 0), [(1001, 0, 0)]),
        ((20, 0, 2), [(21, 0, 2)]),
        ((20, 2, 2), [(21, 2, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_keys)
    def test_below_keys(self, key, res):
        """Unit test for below_keys"""

        cell = GridCellNavigator(main_window, key)
        assert set(cell.below_keys()) == set(res)

    param_test_left_keys = [
        ((0, 0, 0), [(0, -1, 0)]),
        ((20, 0, 0), [(20, -1, 0)]),
        ((20, 0, 2), [(20, -1, 2)]),
        ((20, 2, 2), [(20, 1, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_left_keys)
    def test_left_keys(self, key, res):
        """Unit test for left_keys"""

        cell = GridCellNavigator(main_window, key)
        assert set(cell.left_keys()) == set(res)

    param_test_right_keys = [
        ((0, 0, 0), [(0, 1, 0)]),
        ((20, 0, 0), [(20, 1, 0)]),
        ((20, 0, 2), [(20, 1, 2)]),
        ((20, 2, 2), [(20, 3, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_right_keys)
    def test_right_keys(self, key, res):
        """Unit test for right_keys"""

        cell = GridCellNavigator(main_window, key)
        assert set(cell.right_keys()) == set(res)

    param_test_above_left_key = [
        ((0, 0, 0), (-1, -1, 0)),
        ((20, 0, 0), (19, -1, 0)),
        ((20, 0, 2), (19, -1, 2)),
        ((20, 2, 2), (19, 1, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_left_key)
    def test_above_left_key(self, key, res):
        """Unit test for above_left_key"""

        cell = GridCellNavigator(main_window, key)
        assert cell.above_left_key() == res

    param_test_above_right_key = [
        ((0, 0, 0), (-1, 1, 0)),
        ((20, 0, 0), (19, 1, 0)),
        ((20, 0, 2), (19, 1, 2)),
        ((20, 2, 2), (19, 3, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_right_key)
    def test_above_right_key(self, key, res):
        """Unit test for above_right_key"""

        cell = GridCellNavigator(main_window, key)
        assert cell.above_right_key() == res

    param_test_below_left_key = [
        ((0, 0, 0), (1, -1, 0)),
        ((20, 0, 0), (21, -1, 0)),
        ((20, 0, 2), (21, -1, 2)),
        ((20, 2, 2), (21, 1, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_left_key)
    def test_below_left_key(self, key, res):
        """Unit test for below_left_key"""

        cell = GridCellNavigator(main_window, key)
        assert cell.below_left_key() == res

    param_test_below_right_key = [
        ((0, 0, 0), (1, 1, 0)),
        ((20, 0, 0), (21, 1, 0)),
        ((20, 0, 2), (21, 1, 2)),
        ((20, 2, 2), (21, 3, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_right_key)
    def test_below_right_key(self, key, res):
        """Unit test for below_right_key"""

        cell = GridCellNavigator(main_window, key)
        assert cell.below_right_key() == res


class TestGridCellDelegate:
    """Unit tests for GridCellDelegate in grid.py"""

    pass


class TestTableChoice:
    """Unit tests for TableChoice in grid.py"""

    pass
