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

import pytest

from PyQt5.QtCore import QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QApplication, QAbstractItemView

PYSPREADPATH = abspath(join(dirname(__file__) + "/.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)

@contextmanager
def multi_selection_mode(grid):
    grid.clearSelection()
    old_selection_mode = grid.selectionMode()
    grid.setSelectionMode(QAbstractItemView.MultiSelection)
    yield
    grid.setSelectionMode(old_selection_mode)

with insert_path(PYSPREADPATH):
    from ..pyspread import MainWindow
    from ..lib.selection import Selection


app = QApplication.instance()
if app is None:
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

    def test_current_invalid(self):
        """Unit test for current getter and setter with invalid parameters"""

        with pytest.raises(ValueError):
            self.grid.current = 1,2,3,4

    param_test_row_heights = [
        ({0: 23}, {0: 23}),
        ({1: 3}, {1: 3.0}),
        ({0: 23, 12: 200}, {0: 23, 12: 200}),
    ]

    @pytest.mark.parametrize("heights, heights_res", param_test_row_heights)
    def test_row_heights(self, heights, heights_res):
        """Unit test for row_heights"""

        for row in heights:
            self.grid.setRowHeight(row, heights[row])

        row_heights = dict(self.grid.row_heights)
        for row in heights_res:
            assert row_heights[row] == heights_res[row]

    param_test_column_widths = [
        ({0: 23}, {0: 23}),
        ({1: 3}, {1: 3.0}),
        ({0: 23, 12: 200}, {0: 23, 12: 200}),
    ]

    @pytest.mark.parametrize("widths, widths_res", param_test_column_widths)
    def test_column_widths(self, widths, widths_res):
        """Unit test for column_widths"""

        for column in widths:
            self.grid.setColumnWidth(column, widths[column])

        column_widths = dict(self.grid.column_widths)
        for column in widths_res:
            assert column_widths[column] == widths_res[column]

    param_test_selection_cells = [
        (((0, 0),), Selection([], [], [], [], [(0, 0)])),
        (((0, 0), (1, 0)), Selection([], [], [], [], [(0, 0), (1, 0)])),
        (((0, 0), (999, 0)), Selection([], [], [], [], [(0, 0), (999, 0)])),
        (((0, 0), (1, 0), (0, 1), (1, 1)),
         Selection([], [], [], [], [(0, 0), (1, 0), (0, 1), (1, 1)])),
    ]

    @pytest.mark.parametrize("cells, res", param_test_selection_cells)
    def test_selection_cells(self, cells, res):
        """Unit test for selection getter using cells"""

        with multi_selection_mode(self.grid):
            for cell in cells:
                idx = self.grid.model.index(*cell)
                self.grid.selectionModel().select(idx,
                                                  QItemSelectionModel.Select)
            assert self.grid.selection == res

    param_test_selection_blocks = [
        ((0, 0, 1, 1), Selection([(0, 0)], [(1, 1)], [], [], [])),
        ((1, 2, 14, 19), Selection([(1, 2)], [(14, 19)], [], [], [])),
    ]

    @pytest.mark.parametrize("block, res", param_test_selection_blocks)
    def test_selection_blocks(self, block, res):
        """Unit test for selection getter using blocks"""

        with multi_selection_mode(self.grid):
            top, left, bottom, right = block
            idx_tl = self.grid.model.index(top, left)
            idx_br = self.grid.model.index(bottom, right)
            item_selection = QItemSelection(idx_tl, idx_br)
            self.grid.selectionModel().select(item_selection,
                                              QItemSelectionModel.Select)
            assert self.grid.selection == res


    param_test_selection_rows = [
        ((0,), Selection([], [], [0], [], [])),
        ((1, 2), Selection([], [], [1, 2], [], [])),
    ]

    @pytest.mark.parametrize("rows, res", param_test_selection_rows)
    def test_selection_rows(self, rows, res):
        """Unit test for selection getter using rows"""

        with multi_selection_mode(self.grid):
            for row in rows:
                self.grid.selectRow(row)
            assert self.grid.selection == res

    param_test_selection_columns = [
        ((0,), Selection([], [], [], [0], [])),
        ((1, 2), Selection([], [], [], [1, 2], [])),
    ]

    @pytest.mark.parametrize("columns, res", param_test_selection_columns)
    def test_selection_columns(self, columns, res):
        """Unit test for selection getter using columns"""

        with multi_selection_mode(self.grid):
            for column in columns:
                self.grid.selectColumn(column)
            assert self.grid.selection == res

    param_test_zoom = [(1, 1), (2, 2), (8, 8), (0, 1), (100, 1), (-1, 1)]

    @pytest.mark.parametrize("zoom, zoom_res", param_test_zoom)
    def test_zoom(self, zoom, zoom_res, monkeypatch):
        """Unit test for zoom getter and setter"""

        monkeypatch.setattr(self.grid, "zoom", zoom)
        assert self.grid.zoom == zoom_res

    param_test_set_selection_mode = [
        (True, (0, 0, 0), (0, 0, 0), QAbstractItemView.NoEditTriggers),
        (False, (1, 2, 3), None, QAbstractItemView.DoubleClicked
                                 | QAbstractItemView.EditKeyPressed
                                 | QAbstractItemView.AnyKeyPressed),
    ]

    @pytest.mark.parametrize("on, current, start, edit_mode",
                             param_test_set_selection_mode)
    def test_set_selection_mode(self, on, current, start, edit_mode):
        """Unit test for set_selection_mode"""

        self.grid.current = current
        self.grid.set_selection_mode(on)
        for grid in main_window.grids:
            assert grid.selection_mode == on
        assert self.grid.editTriggers() == edit_mode
        assert self.grid.current_selection_mode_start == start

    param_test_selected_idx_to_str = [
        ([grid.model.createIndex(2, 4)], "(2, 4, 0)"),
        ([grid.model.createIndex(2, 4), grid.model.createIndex(3, 4)],
         "(2, 4, 0), (3, 4, 0)"),
    ]

    @pytest.mark.parametrize("sel_idx, res", param_test_selected_idx_to_str)
    def test_selected_idx_to_str(self, sel_idx, res):
        """Unit test for _selected_idx_to_str"""

        assert self.grid._selected_idx_to_str(sel_idx) == res

    def test_has_selection(self):
        """Unit test for has_selection"""

        assert not self.grid.has_selection()
        self.grid.selectRow(2)
        assert self.grid.has_selection()


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


class TestGridCellDelegate:
    """Unit tests for GridCellDelegate in grid.py"""

    pass


class TestTableChoice:
    """Unit tests for TableChoice in grid.py"""

    pass
