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
from PyQt5.QtGui import QFont, QColor, QFontDatabase, QFontInfo


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
    from ..commands import MakeButtonCell, RemoveButtonCell
    from ..lib.selection import Selection


app = QApplication.instance()
if app is None:
    app = QApplication([])
main_window = MainWindow()
zoom_levels = main_window.settings.zoom_levels


class TestGrid:
    """Unit tests for Grid in grid.py"""

    grid = main_window.grid
    cell_attributes = grid.model.code_array.cell_attributes

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
            self.grid.current = 1, 2, 3, 4

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
        (False, (1, 2, 3), None,
         QAbstractItemView.DoubleClicked
         | QAbstractItemView.EditKeyPressed
         | QAbstractItemView.AnyKeyPressed),
    ]

    @pytest.mark.parametrize("on, current, start, edit_mode",
                             param_test_set_selection_mode)
    def test_set_selection_mode(self, on, current, start, edit_mode):
        """Unit test for set_selection_mode"""

        self.grid.set_selection_mode(False)
        self.grid.current = current
        self.grid.set_selection_mode(on)
        for grid in main_window.grids:
            assert grid.selection_mode == on
        assert self.grid.editTriggers() == edit_mode
        assert self.grid.current_selection_mode_start == start

    def test_focusInEvent(self):
        """Unit test for focusInEvent"""

        main_window.grids[0].setFocus()
        main_window.grids[1].setFocus()
        assert main_window._last_focused_grid == main_window.grids[0]

    def test_adjust_size(self):
        """Unit test for adjust_size"""

        w = self.grid.horizontalHeader().length() + \
            self.grid.verticalHeader().width()
        h = self.grid.verticalHeader().length() + \
            self.grid.horizontalHeader().height()

        self.grid.resize(200, 200)
        self.grid.adjust_size()
        assert self.grid.size().width() == w
        assert self.grid.size().height() == h

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
        self.grid.clearSelection()
        assert not self.grid.has_selection()
        self.grid.selectColumn(2)
        self.grid.on_merge_pressed()
        self.grid.selectRow(2)
        assert self.grid.has_selection()
        self.grid.current = 2, 2, 0
        self.grid.selectColumn(2)
        assert self.grid.has_selection()

    def test_on_current_changed(self):
        """Unit test for on_current_changed"""

        main_window.entry_line.setPlainText("Test")
        self.grid.selection_mode_exiting = True
        self.grid.current = 0, 1, 0
        assert main_window.entry_line.toPlainText() == "Test"
        self.grid.selection_mode_exiting = False

        self.grid.selection_mode = True
        self.grid.current = 2, 1, 0
        assert main_window.entry_line.toPlainText() == "S[X + 2, Y + 0, Z]Test"
        self.grid.selection_mode = False
        main_window.entry_line.setPlainText("")

    def test_on_selection_changed(self):
        """Unit test for on_selection_changed"""

        main_window.settings.show_statusbar_sum = False
        self.grid.model.code_array[1, 0, 0] = "23"
        self.grid.model.code_array[2, 0, 0] = "2"
        self.grid.current = 0, 0, 0
        idx_tl = self.grid.model.index(0, 0)
        idx_br = self.grid.model.index(5, 0)
        item_selection = QItemSelection(idx_tl, idx_br)
        self.grid.selectionModel().select(item_selection,
                                          QItemSelectionModel.Select)
        assert main_window.statusBar().currentMessage() == ""

        self.grid.clearSelection()
        main_window.settings.show_statusbar_sum = True
        idx_tl = self.grid.model.index(0, 0)
        idx_br = self.grid.model.index(4, 0)
        item_selection = QItemSelection(idx_tl, idx_br)
        self.grid.selectionModel().select(item_selection,
                                          QItemSelectionModel.Select)
        assert main_window.statusBar().currentMessage() == \
               "Selection: 5 cells     Σ=25     max=23     min=2"

    def test_on_row_resized(self):
        """Unit test for on_row_resized"""

        self.grid.setRowHeight(2, 45)
        self.grid.setRowHeight(6, 45)

        row_heights = dict(self.grid.row_heights)
        assert row_heights[2] == 45
        assert row_heights[6] == 45

        self.grid.current = 3, 1, 0
        idx_tl = self.grid.model.index(3, 1)
        idx_br = self.grid.model.index(5, 2)
        item_selection = QItemSelection(idx_tl, idx_br)
        self.grid.selectionModel().select(item_selection,
                                          QItemSelectionModel.Select)

        self.grid.setRowHeight(3, 48)
        row_heights = dict(self.grid.row_heights)
        assert row_heights[2] == 45
        assert row_heights[3] == 48
        assert row_heights[4] == 48
        assert row_heights[5] == 48
        assert row_heights[6] == 45

        self.grid.clearSelection()

    def test_on_column_resized(self):
        """Unit test for on_column_resized"""

        self.grid.setColumnWidth(2, 45)
        self.grid.setColumnWidth(6, 45)

        col_widths = dict(self.grid.column_widths)
        assert col_widths[2] == 45
        assert col_widths[6] == 45

        self.grid.current = 1, 3, 0
        idx_tl = self.grid.model.index(1, 3)
        idx_br = self.grid.model.index(2, 5)
        item_selection = QItemSelection(idx_tl, idx_br)
        self.grid.selectionModel().select(item_selection,
                                          QItemSelectionModel.Select)

        self.grid.setColumnWidth(3, 48)
        col_widths = dict(self.grid.column_widths)
        assert col_widths[2] == 45
        assert col_widths[3] == 48
        assert col_widths[4] == 48
        assert col_widths[5] == 48
        assert col_widths[6] == 45

        self.grid.clearSelection()

    param_test_on_zoom_in = list(zip(zoom_levels[:-1], zoom_levels[1:]))
    param_test_on_zoom_in += [(max(zoom_levels), max(zoom_levels))]

    @pytest.mark.parametrize("zoom, res", param_test_on_zoom_in)
    def test_on_zoom_in(self, zoom, res):
        """Unit test for on_zoom_in"""

        for grid in main_window.grids:
            main_window._last_focused_grid = grid
            grid.zoom = zoom
            self.grid.on_zoom_in()
            assert grid.zoom == res
        main_window._last_focused_grid = self.grid

    param_test_on_zoom_out = list(zip(zoom_levels[1:], zoom_levels[:-1]))
    param_test_on_zoom_out += [(min(zoom_levels), min(zoom_levels))]

    @pytest.mark.parametrize("zoom, res", param_test_on_zoom_out)
    def test_on_zoom_out(self, zoom, res):
        """Unit test for on_zoom_out"""

        for grid in main_window.grids:
            main_window._last_focused_grid = grid
            grid.zoom = zoom
            self.grid.on_zoom_out()
            assert grid.zoom == res
        main_window._last_focused_grid = self.grid

    @pytest.mark.parametrize("zoom", zoom_levels)
    def test_on_zoom_1(self, zoom):
        """Unit test for on_zoom_1"""

        for grid in main_window.grids:
            main_window._last_focused_grid = grid
            grid.zoom = zoom
            grid.on_zoom_1()
            assert grid.zoom == 1.0
        main_window._last_focused_grid = self.grid

    def test_refresh_frozen_cell(self):
        """Unit test for _refresh_frozen_cell"""

        self.grid.current = 1, 0, 0
        self.grid.model.code_array[1, 0, 0] = "23"
        self.grid.on_freeze_pressed(True)
        self.grid.model.code_array[1, 0, 0] = "'Test'"
        assert self.grid.model.code_array.frozen_cache == {'(1, 0, 0)': 23}
        assert self.grid.model.code_array[1, 0, 0] == 23

        self.grid._refresh_frozen_cell((1, 0, 0))
        assert self.grid.model.code_array[1, 0, 0] == "Test"

        self.grid.on_freeze_pressed(False)

    def test_refresh_frozen_cells(self):
        """Unit test for refresh_frozen_cells"""

        self.grid.current = 1, 0, 0
        self.grid.model.code_array[1, 0, 0] = "23"
        self.grid.on_freeze_pressed(True)
        self.grid.current = 2, 0, 0
        self.grid.model.code_array[2, 0, 0] = "24"
        self.grid.on_freeze_pressed(True)

        assert self.grid.model.code_array[1, 0, 0] == 23
        assert self.grid.model.code_array[2, 0, 0] == 24

        self.grid.model.code_array[1, 0, 0] = "'Test1'"
        self.grid.model.code_array[2, 0, 0] = "'Test2'"

        assert self.grid.model.code_array[1, 0, 0] == 23
        assert self.grid.model.code_array[2, 0, 0] == 24

        self.grid.refresh_frozen_cells()

        assert self.grid.model.code_array[1, 0, 0] == "Test1"
        assert self.grid.model.code_array[2, 0, 0] == "Test2"

        self.grid.current = 1, 0, 0
        self.grid.on_freeze_pressed(False)
        self.grid.current = 2, 0, 0
        self.grid.on_freeze_pressed(False)

    def test_refresh_selected_frozen_cells(self):
        """Unit test for refresh_selected_frozen_cells"""

        self.grid.current = 1, 0, 0
        self.grid.model.code_array[1, 0, 0] = "23"
        self.grid.on_freeze_pressed(True)
        self.grid.current = 2, 0, 0
        self.grid.model.code_array[2, 0, 0] = "24"
        self.grid.on_freeze_pressed(True)

        assert self.grid.model.code_array[1, 0, 0] == 23
        assert self.grid.model.code_array[2, 0, 0] == 24

        self.grid.model.code_array[1, 0, 0] = "'Test1'"
        self.grid.model.code_array[2, 0, 0] = "'Test2'"

        assert self.grid.model.code_array[1, 0, 0] == 23
        assert self.grid.model.code_array[2, 0, 0] == 24

        self.grid.selectRow(1)
        self.grid.refresh_selected_frozen_cells()

        assert self.grid.model.code_array[1, 0, 0] == "Test1"
        assert self.grid.model.code_array[2, 0, 0] == 24

        self.grid.current = 1, 0, 0
        self.grid.on_freeze_pressed(False)
        self.grid.current = 2, 0, 0
        self.grid.on_freeze_pressed(False)

    def test_on_show_frozen_pressed(self):
        """Unit test for on_show_frozen_pressed"""

        self.grid.on_show_frozen_pressed(True)
        assert main_window.settings.show_frozen
        self.grid.on_show_frozen_pressed(False)
        assert not main_window.settings.show_frozen

    def test_on_font(self):
        """Unit test for on_font"""

        self.grid.selectRow(2)

        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
        # systemFont might return only an alias, instantiate it to get the
        # effective font name to check on later
        effective_font = QFontInfo(QFont(fixed_font)).family()

        main_window.widgets.font_combo.font = fixed_font
        self.grid.on_font()
        assert self.cell_attributes[(2, 0, 0)]["textfont"] == effective_font
        assert self.grid.model.font((2, 0, 0)).family() == effective_font

        self.grid.clearSelection()

    def test_on_font_size(self):
        """Unit test for on_font_size"""

        self.grid.selectRow(2)

        main_window.widgets.font_size_combo.size = 14
        assert main_window.widgets.font_size_combo.size == 14
        self.grid.on_font_size()
        assert self.cell_attributes[(2, 0, 0)]["pointsize"] == 14

        self.grid.clearSelection()

    def test_on_bold_pressed(self):
        """Unit test for on_bold_pressed"""

        self.grid.selectRow(2)

        self.grid.on_bold_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["fontweight"] == QFont.Bold
        self.grid.on_bold_pressed(False)
        assert self.cell_attributes[(2, 0, 0)]["fontweight"] == QFont.Normal

        self.grid.clearSelection()

    def test_on_italics_pressed(self):
        """Unit test for on_italics_pressed"""

        self.grid.selectRow(2)

        self.grid.on_italics_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["fontstyle"] \
            == QFont.StyleItalic
        self.grid.on_italics_pressed(False)
        assert self.cell_attributes[(2, 0, 0)]["fontstyle"] \
            == QFont.StyleNormal

        self.grid.clearSelection()

    def test_on_underline_pressed(self):
        """Unit test for on_underline_pressed"""

        self.grid.selectRow(2)

        self.grid.on_underline_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["underline"]
        self.grid.on_underline_pressed(False)
        assert not self.cell_attributes[(2, 0, 0)]["underline"]

        self.grid.clearSelection()

    def test_on_strikethrough_pressed(self):
        """Unit test for on_strikethrough_pressed"""

        self.grid.selectRow(2)

        self.grid.on_strikethrough_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["strikethrough"]
        self.grid.on_strikethrough_pressed(False)
        assert not self.cell_attributes[(2, 0, 0)]["strikethrough"]

        self.grid.clearSelection()

    def test_on_text_renderer_pressed(self):
        """Unit test for on_text_renderer_pressed"""

        self.grid.selectRow(2)

        self.grid.on_text_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "text"
        self.grid.on_text_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "text"

        self.grid.clearSelection()

    def test_on_image_renderer_pressed(self):
        """Unit test for on_image_renderer_pressed"""

        self.grid.selectRow(2)

        self.grid.on_image_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "image"
        self.grid.on_text_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "text"

        self.grid.clearSelection()

    def test_on_markup_renderer_pressed(self):
        """Unit test for on_markup_renderer_pressed"""

        self.grid.selectRow(2)

        self.grid.on_markup_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "markup"
        self.grid.on_text_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "text"

        self.grid.clearSelection()

    def test_on_matplotlib_renderer_pressed(self):
        """Unit test for on_matplotlib_renderer_pressed"""

        self.grid.selectRow(2)

        self.grid.on_matplotlib_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "matplotlib"
        self.grid.on_text_renderer_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["renderer"] == "text"

        self.grid.clearSelection()

    def test_on_lock_pressed(self):
        """Unit test for on_lock_pressed"""

        self.grid.selectRow(2)

        self.grid.on_lock_pressed(True)
        assert self.cell_attributes[(2, 0, 0)]["locked"]
        self.grid.on_lock_pressed(False)
        assert not self.cell_attributes[(2, 0, 0)]["locked"]

        self.grid.clearSelection()

    def test_on_rotate_0(self):
        """Unit test for on_rotate_0"""

        self.grid.selectRow(2)

        self.grid.on_rotate_0(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 0.0

        self.grid.clearSelection()

    def test_on_rotate_90(self):
        """Unit test for on_rotate_90"""

        self.grid.selectRow(2)

        self.grid.on_rotate_90(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 90.0
        self.grid.on_rotate_0(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 0.0

        self.grid.clearSelection()

    def test_on_rotate_180(self):
        """Unit test for on_rotate_180"""

        self.grid.selectRow(2)

        self.grid.on_rotate_180(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 180.0
        self.grid.on_rotate_0(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 0.0

        self.grid.clearSelection()

    def test_on_rotate_270(self):
        """Unit test for on_rotate_270"""

        self.grid.selectRow(2)

        self.grid.on_rotate_270(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 270.0
        self.grid.on_rotate_0(True)
        assert self.cell_attributes[(2, 0, 0)]["angle"] == 0.0

        self.grid.clearSelection()

    def test_on_justify_left(self):
        """Unit test for on_justify_left"""

        self.grid.selectRow(2)

        self.grid.on_justify_left(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_left"

        self.grid.clearSelection()

    def test_on_justify_fill(self):
        """Unit test for on_justify_fill"""

        self.grid.selectRow(2)

        self.grid.on_justify_fill(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_fill"
        self.grid.on_justify_left(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_left"

        self.grid.clearSelection()

    def test_on_justify_center(self):
        """Unit test for on_justify_center"""

        self.grid.selectRow(2)

        self.grid.on_justify_center(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_center"
        self.grid.on_justify_left(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_left"

        self.grid.clearSelection()

    def test_on_justify_right(self):
        """Unit test for on_justify_right"""

        self.grid.selectRow(2)

        self.grid.on_justify_right(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_right"
        self.grid.on_justify_left(True)
        assert self.cell_attributes[(2, 0, 0)]["justification"] \
            == "justify_left"

        self.grid.clearSelection()

    def test_on_align_top(self):
        """Unit test for on_align_top"""

        self.grid.selectRow(2)

        self.grid.on_align_top(True)
        assert self.cell_attributes[(2, 0, 0)]["vertical_align"] == "align_top"

    def test_on_align_middle(self):
        """Unit test for on_align_middle"""

        self.grid.selectRow(2)

        self.grid.on_align_middle(True)
        assert self.cell_attributes[(2, 0, 0)]["vertical_align"] \
            == "align_center"
        self.grid.on_align_top(True)
        assert self.cell_attributes[(2, 0, 0)]["vertical_align"] == "align_top"

    def test_on_align_bottom(self):
        """Unit test for on_align_bottom"""

        self.grid.selectRow(2)

        self.grid.on_align_bottom(True)
        assert self.cell_attributes[(2, 0, 0)]["vertical_align"] \
            == "align_bottom"
        self.grid.on_align_top(True)
        assert self.cell_attributes[(2, 0, 0)]["vertical_align"] == "align_top"

    def test_on_text_color(self):
        """Unit test for on_text_color"""

        self.grid.selectRow(2)
        main_window.widgets.text_color_button.color = QColor(100, 100, 50)

        self.grid.on_text_color()

        assert self.cell_attributes[(2, 0, 0)]["textcolor"] \
            == (100, 100, 50, 255)

        self.grid.clearSelection()

    def test_on_line_color(self):
        """Unit test for on_line_color"""

        self.grid.selectRow(2)
        main_window.widgets.line_color_button.color = QColor(100, 100, 50)

        self.grid.on_line_color()

        assert self.cell_attributes[(2, 0, 0)]["bordercolor_bottom"] \
            == (100, 100, 50, 255)

        assert self.cell_attributes[(2, 99, 0)]["bordercolor_right"] \
            == (100, 100, 50, 255)

        self.grid.clearSelection()

    def test_on_background_color(self):
        """Unit test for on_background_color"""

        self.grid.selectRow(2)
        main_window.widgets.background_color_button.color = QColor(100, 10, 5)

        self.grid.on_background_color()

        assert self.cell_attributes[(2, 0, 0)]["bgcolor"] == (100, 10, 5, 255)

        self.grid.clearSelection()

    def test_update_cell_spans(self):
        """Unit test for update_cell_spans"""

        self.cell_attributes.clear()
        self.grid.clearSelection()
        self.grid.selectRow(2)
        self.grid.on_merge_pressed()
        self.grid.table = 1
        self.grid.update_cell_spans()
        self.grid.table = 0
        self.grid.update_cell_spans()

        assert self.grid.columnSpan(2, 0) == 100

        self.grid.selectRow(2)
        self.grid.on_merge_pressed()
        self.grid.clearSelection()
        self.grid.selectColumn(1)
        self.grid.on_merge_pressed()
        self.grid.update_cell_spans()

        assert self.grid.rowSpan(0, 1) == 1000

        self.grid.selectColumn(1)
        self.grid.on_merge_pressed()
        self.grid.update_cell_spans()

    def test_update_index_widgets(self):
        """Unit test for update_index_widgets"""

        self.grid.current = 2, 2, 0
        description_tpl = "Make cell {} a button cell"
        description = description_tpl.format(self.grid.current)
        command = MakeButtonCell(self.grid, "TestButton",
                                 self.grid.currentIndex(), description)
        main_window.undo_stack.push(command)

        self.grid.update_index_widgets()
        assert self.grid.widget_indices

        description_tpl = "Make cell {} a non-button cell"
        description = description_tpl.format(self.grid.current)
        command = RemoveButtonCell(self.grid, self.grid.currentIndex(),
                                   description)
        main_window.undo_stack.push(command)

        self.grid.update_index_widgets()
        assert not self.grid.widget_indices

    def test_on_freeze_pressed(self):
        """Unit test for on_freeze_pressed"""

        self.grid.current = 1, 0, 0
        self.grid.model.code_array[1, 0, 0] = "23"
        self.grid.on_freeze_pressed(False)
        assert not self.cell_attributes[self.grid.current]["frozen"]
        self.grid.on_freeze_pressed(True)
        assert self.cell_attributes[self.grid.current]["frozen"]
        self.grid.on_freeze_pressed(False)
        assert not self.cell_attributes[self.grid.current]["frozen"]

    def test_on_merge_pressed(self):
        """Unit test for on_merge_pressed"""

        self.grid.clearSelection()
        self.grid.current = 1, 0, 0
        self.grid.on_merge_pressed()

        assert not self.cell_attributes[self.grid.current]["merge_area"]

    def test_on_quote(self):
        """Unit test for on_quote"""

        self.grid.model.code_array[1, 0, 0] = "42"

        self.grid.clearSelection()
        self.grid.selectRow(1)

        self.grid.on_quote()
        assert self.grid.model.code_array((1, 0, 0)) == "'42'"

    def test_is_row_data_discarded(self):
        """Unit test for is_row_data_discarded"""

        self.grid.model.code_array[998, 0, 0] = "Edge data"

        assert not self.grid.is_row_data_discarded(0)
        assert not self.grid.is_row_data_discarded(1)
        assert self.grid.is_row_data_discarded(2)

        self.grid.model.code_array[998, 0, 0] = None

    def test_is_column_data_discarded(self):
        """Unit test for is_column_data_discarded"""

        self.grid.model.code_array[0, 98, 0] = "Edge data"

        assert not self.grid.is_column_data_discarded(0)
        assert not self.grid.is_column_data_discarded(1)
        assert self.grid.is_column_data_discarded(2)

        self.grid.model.code_array[0, 98, 0] = None

    def test_is_table_data_discarded(self):
        """Unit test for is_table_data_discarded"""

        self.grid.model.code_array[0, 0, 1] = "Edge data"

        assert not self.grid.is_table_data_discarded(0)
        assert not self.grid.is_table_data_discarded(1)
        assert self.grid.is_table_data_discarded(2)

        self.grid.model.code_array[0, 0, 1] = None

    def test_on_insert_rows(self):
        """Unit test for on_insert_rows"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[1, 0, 0] = "'Test data'"
        self.grid.selectRow(0)
        self.grid.on_insert_rows()
        assert self.grid.model.code_array[1, 0, 0] is None
        assert self.grid.model.code_array[2, 0, 0] == "Test data"

        self.grid.clearSelection()
        self.grid.selectRow(1)
        self.grid.on_insert_rows()
        assert self.grid.model.code_array[3, 0, 0] == "Test data"

    def test_on_delete_rows(self):
        """Unit test for on_delete_rows"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[1, 0, 0] = "'Test data'"
        self.grid.selectRow(0)
        self.grid.on_delete_rows()
        assert self.grid.model.code_array[1, 0, 0] is None
        assert self.grid.model.code_array[0, 0, 0] == "Test data"

    def test_on_insert_columns(self):
        """Unit test for on_insert_columns"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[0, 1, 0] = "'Test data'"
        self.grid.selectColumn(0)
        self.grid.on_insert_columns()
        assert self.grid.model.code_array[0, 1, 0] is None
        assert self.grid.model.code_array[0, 2, 0] == "Test data"

        self.grid.clearSelection()
        self.grid.selectColumn(1)
        self.grid.on_insert_columns()
        assert self.grid.model.code_array[0, 3, 0] == "Test data"

    def test_on_delete_columns(self):
        """Unit test for on_delete_columns"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[0, 1, 0] = "'Test data'"
        self.grid.selectColumn(0)
        self.grid.on_delete_columns()
        assert self.grid.model.code_array[0, 1, 0] is None
        assert self.grid.model.code_array[0, 0, 0] == "Test data"

    def test_on_insert_table(self):
        """Unit test for on_insert_table"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[0, 0, 1] = "'Test data'"
        self.grid.on_insert_table()
        assert self.grid.model.code_array[0, 0, 1] is None
        assert self.grid.model.code_array[0, 0, 2] == "Test data"

    def test_on_delete_table(self):
        """Unit test for on_delete_table"""

        self.grid.clearSelection()
        self.grid.model.reset()

        self.current = 0, 0, 0
        self.grid.model.code_array[0, 0, 1] = "'Test data'"
        self.grid.on_delete_table()
        assert self.grid.model.code_array[0, 0, 1] is None
        assert self.grid.model.code_array[0, 0, 0] == "Test data"


class TestGridHeaderView:
    """Unit tests for GridHeaderView in grid.py"""

    def test_sectionSizeHint(self):
        """Unit test for sectionSizeHint"""

        hghview = main_window.grid.horizontalHeader()
        size1 = hghview.sectionSizeHint(0)
        main_window.grid.zoom = 2.0
        assert hghview.sectionSizeHint(0) == 2 * size1


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
