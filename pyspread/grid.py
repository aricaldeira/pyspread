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

Pyspread's main grid

**Provides**

* :class:`Grid`: QTableView of the main grid
* :class:`GridHeaderView`: QHeaderView for the main grids headers
* :class:`GridTableModel`: QAbstractTableModel linking the view to code_array
  backend
* :class:`GridCellDelegate`: QStyledItemDelegate handling custom painting and
  editors
* :class:`TableChoice`: The TabBar below the main grid

"""

from ast import literal_eval
from contextlib import contextmanager
from datetime import datetime, date, time
from io import BytesIO
from typing import Any, Iterable, List, Tuple, Union

import numpy

from PyQt6.QtWidgets \
    import (QTableView, QStyledItemDelegate, QTabBar, QWidget, QMainWindow,
            QStyleOptionViewItem, QApplication, QStyle, QAbstractItemDelegate,
            QHeaderView, QFontDialog, QInputDialog, QLineEdit,
            QAbstractItemView)
from PyQt6.QtGui \
    import (QColor, QBrush, QFont, QPainter, QPalette, QImage, QKeyEvent,
            QTextOption, QAbstractTextDocumentLayout, QTextDocument,
            QWheelEvent, QContextMenuEvent, QTextCursor)
from PyQt6.QtCore \
    import (Qt, QAbstractTableModel, QModelIndex, QVariant, QEvent, QSize,
            QRect, QRectF, QItemSelectionModel, QObject, QAbstractItemModel,
            QByteArray, pyqtSignal)

from PyQt6.QtSvg import QSvgRenderer

try:
    import matplotlib
    import matplotlib.figure
except ImportError:
    matplotlib = None

try:
    from moneyed import Money
except ImportError:
    Money = None

try:
    from pyspread import commands
    from pyspread.dialogs import DiscardDataDialog
    from pyspread.grid_renderer import (painter_save, CellRenderer,
                                        QColorCache, BorderWidthBottomCache,
                                        BorderWidthRightCache,
                                        EdgeBordersCache,
                                        BorderColorRightCache,
                                        BorderColorBottomCache)
    from pyspread.model.model import (CodeArray, CellAttribute,
                                      DefaultCellAttributeDict,
                                      class_format_functions)
    from pyspread.lib.attrdict import AttrDict
    from pyspread.interfaces.pys import (qt52qt6_fontweights,
                                         qt62qt5_fontweights)
    from pyspread.lib.selection import Selection
    from pyspread.lib.string_helpers import quote, wrap_text
    from pyspread.lib.qimage2ndarray import array2qimage
    from pyspread.lib.typechecks import is_svg, check_shape_validity
    from pyspread.menus import (GridContextMenu, TableChoiceContextMenu,
                                HorizontalHeaderContextMenu,
                                VerticalHeaderContextMenu)
    from pyspread.themes import ColorRole
    from pyspread.widgets import CellButton
except ImportError:
    import commands
    from dialogs import DiscardDataDialog
    from grid_renderer import (painter_save, CellRenderer, QColorCache,
                               BorderWidthBottomCache, BorderWidthRightCache,
                               EdgeBordersCache, BorderColorRightCache,
                               BorderColorBottomCache)
    from model.model import (CodeArray, CellAttribute,
                             DefaultCellAttributeDict, class_format_functions)
    from lib.attrdict import AttrDict
    from interfaces.pys import qt52qt6_fontweights, qt62qt5_fontweights
    from lib.selection import Selection
    from lib.string_helpers import quote, wrap_text
    from lib.qimage2ndarray import array2qimage
    from lib.typechecks import is_svg, check_shape_validity
    from menus import (GridContextMenu, TableChoiceContextMenu,
                       HorizontalHeaderContextMenu, VerticalHeaderContextMenu)
    from themes import ColorRole
    from widgets import CellButton

FONTSTYLES = (QFont.Style.StyleNormal,
              QFont.Style.StyleItalic,
              QFont.Style.StyleOblique)


class Grid(QTableView):
    """The main grid of pyspread"""

    def __init__(self, main_window: QMainWindow, model=None):
        """
        :param main_window: Application main window
        :param model: GridTableModel for grid

        """

        super().__init__()

        self.main_window = main_window

        shape = main_window.settings.shape

        if model is None:
            self.model = GridTableModel(main_window, shape)
        else:
            self.model = model

        self.setModel(self.model)

        self.qcolor_cache = QColorCache(self)
        self.borderwidth_bottom_cache = BorderWidthBottomCache(self)
        self.borderwidth_right_cache = BorderWidthRightCache(self)
        self.edge_borders_cache = EdgeBordersCache()
        self.border_color_bottom_cache = BorderColorBottomCache(self)
        self.border_color_right_cache = BorderColorRightCache(self)

        self.table_choice = main_window.table_choice

        self.widget_indices = []  # Store each index with an indexWidget here

        # Signals
        self.model.dataChanged.connect(self.on_data_changed)
        self.selectionModel().currentChanged.connect(self.on_current_changed)
        self.selectionModel().selectionChanged.connect(
            self.on_selection_changed)

        self.setHorizontalHeader(GridHeaderView(Qt.Orientation.Horizontal,
                                                self))
        self.setVerticalHeader(GridHeaderView(Qt.Orientation.Vertical, self))

        self.verticalHeader().setDefaultSectionSize(
            self.main_window.settings.default_row_height)
        self.horizontalHeader().setDefaultSectionSize(
            self.main_window.settings.default_column_width)

        self.verticalHeader().setMinimumSectionSize(0)
        self.horizontalHeader().setMinimumSectionSize(0)

        self.setCornerButtonEnabled(False)

        self._zoom = 1.0  # Initial zoom level for the grid

        self.current_selection_mode_start = None
        self.selection_mode_exiting = False  # True only during exit

        self.verticalHeader().sectionResized.connect(self.on_row_resized)
        self.horizontalHeader().sectionResized.connect(self.on_column_resized)

        self.setShowGrid(False)

        self.delegate = GridCellDelegate(main_window, self,
                                         self.model.code_array)
        self.setItemDelegate(self.delegate)

        # Select upper left cell because initial selection behaves strange
        self.reset_selection()

        # Locking states for operations by undo and redo operations
        self.__undo_resizing_row = False
        self.__undo_resizing_column = False

        # Initially, select top left cell on table 0
        self.current = 0, 0, 0

        # Store initial viewport
        self.table_scrolls = {0: (self.verticalScrollBar().value(),
                                  self.horizontalScrollBar().value())}

    @contextmanager
    def undo_resizing_row(self):
        """Sets self.__undo_resizing_row to True for context"""

        self.__undo_resizing_row = True
        yield
        self.__undo_resizing_row = False

    @contextmanager
    def undo_resizing_column(self):
        """Sets self.__undo_resizing_column to True for context"""

        self.__undo_resizing_column = True
        yield
        self.__undo_resizing_column = False

    @property
    def row(self) -> int:
        """Current row"""

        return self.currentIndex().row()

    @row.setter
    def row(self, value: int):
        """Sets current row to value

        :param value: Row to be made current

        """

        self.current = value, self.column

    @property
    def column(self) -> int:
        """Current column"""

        return self.currentIndex().column()

    @column.setter
    def column(self, value: int):
        """Sets current column to value

        :param value: Column to be made current

        """

        self.current = self.row, value

    @property
    def table(self) -> int:
        """Current table"""

        return self.table_choice.table

    @table.setter
    def table(self, value: int):
        """Sets current table

        :param value: Table to be made current

        """

        if 0 <= value < self.model.shape[2]:
            self.table_choice.table = value

    @property
    def current(self) -> Tuple[int, int, int]:
        """Tuple of row, column, table of the current index"""

        return self.row, self.column, self.table

    @current.setter
    def current(self, value: Union[Tuple[int, int, int], Tuple[int, int]]):
        """Sets the current index to row, column and if given table

        :param value: Key of cell to be made current

        """

        if len(value) not in (2, 3):
            msg = "Current cell must be defined with a tuple " + \
                  "(row, column) or (rol, column, table)."
            raise ValueError(msg)

        row, column, *table_list = value

        if not 0 <= row < self.model.shape[0]:
            row = self.row

        if not 0 <= column < self.model.shape[1]:
            column = self.column

        if table_list:
            self.table = table_list[0]

        index = self.model.index(row, column, QModelIndex())
        self.setCurrentIndex(index)

    @property
    def row_heights(self) -> List[Tuple[int, float]]:
        """Returns list of tuples (row_index, row height) for current table"""

        row_heights = self.model.code_array.row_heights
        return [(row, row_heights[row, tab]) for row, tab in row_heights
                if tab == self.table]

    @property
    def column_widths(self) -> List[Tuple[int, float]]:
        """Returns list of tuples (col_index, col_width) for current table"""

        col_widths = self.model.code_array.col_widths
        return [(col, col_widths[col, tab]) for col, tab in col_widths
                if tab == self.table]

    @property
    def selection(self) -> Selection:
        """Pyspread selection based on self's QSelectionModel"""

        if len(self.selected_idx) == 1:
            # Return current cell selection to get accurate results
            current = tuple(self.main_window.focused_grid.current[:2])
            return Selection([], [], [], [], [current])

        selection = self.main_window.focused_grid.selectionModel().selection()

        block_top_left = []
        block_bottom_right = []
        rows = []
        columns = []
        cells = []

        # Selection are made of selection ranges that we call span

        for span in selection:
            top, bottom = span.top(), span.bottom()
            left, right = span.left(), span.right()

            if top == bottom and left == right:
                # The span is a single cell
                cells.append((top, right))
            elif left == 0 and right == self.model.shape[1] - 1:
                # The span consists of selected rows
                rows += list(range(top, bottom + 1))
            elif top == 0 and bottom == self.model.shape[0] - 1:
                # The span consists of selected columns
                columns += list(range(left, right + 1))
            else:
                # Otherwise append a block
                block_top_left.append((top, left))
                block_bottom_right.append((bottom, right))

        return Selection(block_top_left, block_bottom_right,
                         rows, columns, cells)

    @property
    def selected_idx(self) -> List[QModelIndex]:
        """Currently selected indices"""

        return self.main_window.focused_grid.selectionModel().selectedIndexes()

    @property
    def zoom(self) -> float:
        """Returns zoom level"""

        return self._zoom

    @zoom.setter
    def zoom(self, zoom: float):
        """Updates _zoom property and zoom visualization of the grid

        Does nothing if not between minimum and maximum of settings.zoom_levels

        :param zoom: Zoom level to be set

        """

        zoom_levels = self.main_window.settings.zoom_levels
        if min(zoom_levels) <= zoom <= max(zoom_levels):
            self._zoom = zoom
            self.update_zoom()

    @property
    def selection_mode(self) -> bool:
        """In selection mode, cells cannot be edited"""

        return self.editTriggers() \
            == QAbstractItemView.EditTrigger.NoEditTriggers

    @selection_mode.setter
    def selection_mode(self, on: bool):
        """Sets or unsets selection mode for this grid

        In selection mode, cells cannot be edited.
        This triggers the selection_mode icon in the statusbar.

        :param on: If True, selection mode is set, if False unset

        """

        grid = self.main_window.focused_grid

        if on:
            self.current_selection_mode_start = tuple(grid.current)
            self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.main_window.selection_mode_widget.show()
        else:
            self.selection_mode_exiting = True
            if self.current_selection_mode_start is not None:
                grid.current = self.current_selection_mode_start
                self.current_selection_mode_start = None
            self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                 | QAbstractItemView.EditTrigger.EditKeyPressed
                                 | QAbstractItemView.EditTrigger.AnyKeyPressed)
            self.selection_mode_exiting = False
            self.main_window.selection_mode_widget.hide()
            self.main_window.entry_line.setFocus()

    def set_selection_mode(self, value=True):
        """Setter for selection mode for all grids

        :param value: If True, selection mode is set, if False unset

        """

        # All grids must simultaneously got into or out of selection mode
        for grid in self.main_window.grids:
            grid.selection_mode = value

        # Adjust the menu
        main_window_actions = self.main_window.main_window_actions
        toggle_selection_mode = main_window_actions.toggle_selection_mode
        toggle_selection_mode.setChecked(value)

    def toggle_selection_mode(self):
        """Toggle selection mode for all grids

        This method is required for accessing selection mode from QActions.

        """

        main_window_actions = self.main_window.main_window_actions
        toggle_selection_mode = main_window_actions.toggle_selection_mode
        value = toggle_selection_mode.toggled

        for grid in self.main_window.grids:
            grid.selection_mode = value

    # Overrides

    def focusInEvent(self, event):
        """Overrides focusInEvent storing last focused grid in main_window"""

        self.main_window._last_focused_grid = self

        super().focusInEvent(event)

    def closeEditor(self, editor: QWidget,
                    hint: QAbstractItemDelegate.EndEditHint):
        """Overrides QTableView.closeEditor

        Changes to overridden behavior:
         * Data is submitted when a cell is changed without pressing <Enter>
           e.g. by mouse click or arrow keys.

        :param editor: Editor to be closed
        :param hint: Hint to be overridden if == `QAbstractItemDelegate.NoHint`

        """

        if hint == QAbstractItemDelegate.EndEditHint.NoHint:
            hint = QAbstractItemDelegate.EndEditHint.SubmitModelCache

        super().closeEditor(editor, hint)

    def keyPressEvent(self, event: QKeyEvent):
        """Overrides QTableView.keyPressEvent

        Changes to overridden behavior:
         * If Shift is pressed, the cell in the next column is selected.
         * If Shift is not pressed, the cell in the next row is selected.

        :param event: Key event

        """

        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            if self.selection_mode:
                # Return exits selection mode
                self.selection_mode = False
                self.main_window.entry_line.setFocus()
            elif event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.current = self.row, self.column + 1
            else:
                self.current = self.row + 1, self.column
        elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.main_window.workflows.delete()
        elif (event.key() == Qt.Key.Key_Escape
              and self.editTriggers()
              == QAbstractItemView.EditTrigger.NoEditTriggers):
            # Leave cell selection mode
            self.selection_mode = False
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """Overrides mouse wheel event handler

        :param event: Mouse wheel event

        """

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.on_zoom_in()
            else:
                self.on_zoom_out()
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Overrides contextMenuEvent to install GridContextMenu

        :param event: Context menu event

        """

        menu = GridContextMenu(self.main_window.main_window_actions)
        menu.exec(self.mapToGlobal(event.pos()))

    # Helpers

    def reset_selection(self):
        """Select upper left cell"""

        self.setSelection(QRect(1, 1, 1, 1),
                          QItemSelectionModel.SelectionFlag.Select)

    def gui_update(self):
        """Emits gui update signal"""

        attributes = self.model.code_array.cell_attributes[self.current]
        self.main_window.gui_update.emit(attributes)

    def adjust_size(self):
        """Adjusts size to header maxima"""

        horizontal_header = self.horizontalHeader()
        vertical_header = self.verticalHeader()

        width = horizontal_header.length() + vertical_header.width()
        height = vertical_header.length() + horizontal_header.height()

        self.resize(width, height)

    def _selected_idx_to_str(self, selected_idx: Iterable[QModelIndex]) -> str:
        """Converts selected_idx to string with cell indices

        :param selected_idx: Indices of selected cells

        """

        if len(selected_idx) <= 6:
            return ", ".join(str(self.model.current(idx))
                             for idx in selected_idx)

        return ", ".join(str(self.model.current(idx))
                         for idx in selected_idx[:6]) + "..."

    def update_zoom(self):
        """Updates the zoom level visualization to the current zoom factor"""

        self.verticalHeader().update_zoom()
        self.horizontalHeader().update_zoom()

    def has_selection(self) -> bool:
        """Returns True if more than one cell is selected, else False

        This method handles spanned/merged cells. One single cell that is
        selected is considered as no cell being selected.

        """

        cell_attributes = self.model.code_array.cell_attributes
        merge_area = cell_attributes[self.current].merge_area

        if merge_area is None:
            merge_sel = Selection([], [], [], [], [])
        else:
            top, left, bottom, right = merge_area
            merge_sel = Selection([(top, left)], [(bottom, right)], [], [], [])

        return not (self.selection.single_cell_selected()
                    or merge_sel.get_bbox() == self.selection.get_bbox())

    # Event handlers

    def on_data_changed(self):
        """Event handler for data changes"""

        self.qcolor_cache.clear()
        self.borderwidth_bottom_cache.clear()
        self.borderwidth_right_cache.clear()
        self.edge_borders_cache.clear()
        self.border_color_bottom_cache.clear()
        self.border_color_right_cache.clear()

        if not self.main_window.settings.changed_since_save:
            self.main_window.settings.changed_since_save = True
            main_window_title = "* " + self.main_window.windowTitle()
            self.main_window.setWindowTitle(main_window_title)

    def on_current_changed(self, *_: Any):
        """Event handler for change of current cell"""

        if self.selection_mode_exiting:
            # Do not update entry_line to preserve selection
            return

        if self.selection_mode:
            cursor = self.main_window.entry_line.textCursor()
            text_anchor = cursor.anchor()
            text_position = cursor.position()
            if QApplication.queryKeyboardModifiers() \
               == Qt.KeyboardModifier.MetaModifier:
                text = self.selection.get_absolute_access_string(
                    self.model.shape, self.table)
            else:
                text = self.selection.get_relative_access_string(
                    self.model.shape, self.current_selection_mode_start)

            self.main_window.entry_line.insertPlainText(text)
            cursor.setPosition(min(text_anchor, text_position))
            cursor.setPosition(min(text_anchor, text_position) + len(text),
                               QTextCursor.MoveMode.KeepAnchor)
            self.main_window.entry_line.setTextCursor(cursor)
        else:
            code = self.model.code_array(self.current)
            self.main_window.entry_line.setPlainText(code)
            self.gui_update()

    def on_selection_changed(self):
        """Selection changed event handler"""

        if not self.main_window.settings.show_statusbar_sum:
            return

        try:
            selection = self.selection
            code_array = self.model.code_array
            single_cell_selected = selection.single_cell_selected()
        except AttributeError:
            return

        if not selection or single_cell_selected:
            self.main_window.statusBar().clearMessage()
            return

        selected_cell_list = list(selection.cell_generator(self.model.shape,
                                                           self.table))

        res_gen = (code_array[key] for key in selected_cell_list
                   if code_array(key))
        sum_list = [res for res in res_gen if res is not None]

        msg_tpl = "     " + "     ".join(["Σ={}", "max={}", "min={}"])
        msg = f"Selection: {len(selected_cell_list)} cells"
        if sum_list:
            try:
                msg += msg_tpl.format(sum(sum_list), max(sum_list),
                                      min(sum_list))
            except Exception:
                pass

        self.main_window.statusBar().showMessage(msg)

    def on_row_resized(self, row: int, old_height: float, new_height: float):
        """Row resized event handler

        :param row: Row that is resized
        :param old_height: Row height before resizing
        :param new_height: Row height after resizing

        """

        if self.__undo_resizing_row:  # Resize from undo or redo command
            return

        (top, _), (bottom, _) = self.selection.get_grid_bbox(self.model.shape)
        if bottom - top > 1 and top <= row <= bottom:
            rows = list(range(top, bottom + 1))
        else:
            rows = [row]

        description = f"Resize rows {rows} to {new_height}"
        command = commands.SetRowsHeight(self, rows, self.table,
                                         old_height / self.zoom,
                                         new_height / self.zoom, description)
        self.main_window.undo_stack.push(command)

    def on_column_resized(self, column: int, old_width: float,
                          new_width: float):
        """Column resized event handler

        :param row: Column that is resized
        :param old_width: Column width before resizing
        :param new_width: Column width after resizing

        """

        if self.__undo_resizing_column:  # Resize from undo or redo command
            return

        (_, left), (_, right) = self.selection.get_grid_bbox(self.model.shape)
        if right - left > 1 and left <= column <= right:
            columns = list(range(left, right + 1))
        else:
            columns = [column]

        description = f"Resize columns {columns} to {new_width}"
        command = commands.SetColumnsWidth(self, columns, self.table,
                                           old_width / self.zoom,
                                           new_width / self.zoom, description)
        self.main_window.undo_stack.push(command)

    def on_zoom_in(self):
        """Zoom in event handler"""

        grid = self.main_window.focused_grid

        zoom_levels = self.main_window.settings.zoom_levels
        larger_zoom_levels = [zl for zl in zoom_levels if zl > grid.zoom]
        if larger_zoom_levels:
            grid.zoom = min(larger_zoom_levels)

    def on_zoom_out(self):
        """Zoom out event handler"""

        grid = self.main_window.focused_grid

        zoom_levels = self.main_window.settings.zoom_levels
        smaller_zoom_levels = [zl for zl in zoom_levels if zl < grid.zoom]
        if smaller_zoom_levels:
            grid.zoom = max(smaller_zoom_levels)

    def on_zoom_1(self):
        """Sets zoom level ot 1.0"""

        grid = self.main_window.focused_grid
        grid.zoom = 1.0

    def _refresh_frozen_cell(self, key: Tuple[int, int, int]):
        """Refreshes the frozen cell key

        Does neither emit dataChanged nor clear _attr_cache or _table_cache.

        :param key: Key of cell to be refreshed

        """

        if self.model.code_array.cell_attributes[key].frozen:
            code = self.model.code_array(key)
            result = self.model.code_array._eval_cell(key, code)
            self.model.code_array.frozen_cache[repr(key)] = result

    def refresh_frozen_cells(self):
        """Refreshes all frozen cells"""

        frozen_cache = self.model.code_array.frozen_cache
        cell_attributes = self.model.code_array.cell_attributes

        for repr_key in frozen_cache:
            key = literal_eval(repr_key)
            self._refresh_frozen_cell(key)

        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def refresh_selected_frozen_cells(self):
        """Refreshes selected frozen cells"""

        for idx in self.selected_idx:
            self._refresh_frozen_cell((idx.row(), idx.column(), self.table))

        self.model.code_array.cell_attributes._attr_cache.clear()
        self.model.code_array.cell_attributes._table_cache.clear()
        self.model.code_array.result_cache.clear()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def on_show_frozen_pressed(self, toggled: bool):
        """Show frozen cells event handler

        :param toggled: Toggle state

        """

        self.main_window.settings.show_frozen = toggled

    def on_format_default(self):
        """Reset cell format to system theme by setting values to None

        The merge status of cells is unaffected

        """

        attr_dict = DefaultCellAttributeDict()
        attr_dict.pop("merge_area")  # Merged cells are not undone
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Reset cell format for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_font_dialog(self):
        """Font dialog event handler"""

        # Determine currently active font as dialog preset
        font = self.model.font(self.current)
        font, ok = QFontDialog().getFont(font, self.main_window)
        if ok:
            attr_dict = AttrDict()
            attr_dict.textfont = font.family()
            attr_dict.pointsize = font.pointSizeF()
            attr_dict.fontweight = qt62qt5_fontweights(font.weight())
            attr_dict.fontstyle = FONTSTYLES.index(font.style())
            attr_dict.underline = font.underline()
            attr_dict.strikethrough = font.strikeOut()
            attr = CellAttribute(self.selection, self.table, attr_dict)
            idx_string = self._selected_idx_to_str(self.selected_idx)
            description = f"Set font {font} for indices {idx_string}"
            command = commands.SetCellFormat(attr, self.model,
                                             self.currentIndex(),
                                             self.selected_idx, description)
            self.main_window.undo_stack.push(command)

    def on_font(self):
        """Font change event handler"""

        font = self.main_window.widgets.font_combo.font
        attr_dict = AttrDict([("textfont", font)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set font {font} for indices {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_font_size(self):
        """Font size change event handler"""

        size = self.main_window.widgets.font_size_combo.size
        attr_dict = AttrDict([("pointsize", size)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set font size {size} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_bold_pressed(self, toggled: bool):
        """Bold button pressed event handler

        :param toggled: Toggle state

        """

        fontweight = QFont.Weight.Bold if toggled else QFont.Weight.Normal
        attr_dict = AttrDict([("fontweight", qt62qt5_fontweights(fontweight))])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set font weight {fontweight} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_italics_pressed(self, toggled: bool):
        """Italics button pressed event handler

        :param toggled: Toggle state

        """

        fontstyle = QFont.Style.StyleItalic \
            if toggled else QFont.Style.StyleNormal
        attr_dict = AttrDict([("fontstyle", FONTSTYLES.index(fontstyle))])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set font style {fontstyle} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_underline_pressed(self, toggled: bool):
        """Underline button pressed event handler

        :param toggled: Toggle state

        """

        attr_dict = AttrDict([("underline", toggled)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set font underline {toggled} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_strikethrough_pressed(self, toggled: bool):
        """Strikethrough button pressed event handler

        :param toggled: Toggle state

        """

        attr_dict = AttrDict([("strikethrough", toggled)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = \
            f"Set font strikethrough {toggled} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_text_renderer_pressed(self):
        """Text renderer button pressed event handler"""

        attr_dict = AttrDict([("renderer", "text")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set text renderer for cells {idx_string}"
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_image_renderer_pressed(self):
        """Image renderer button pressed event handler"""

        attr_dict = AttrDict([("renderer", "image")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set image renderer for cells {idx_string}"
        entry_line = self.main_window.entry_line
        command = commands.SetCellRenderer(attr, self.model, entry_line, None,
                                           self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_markup_renderer_pressed(self):
        """Markup renderer button pressed event handler"""

        attr_dict = AttrDict([("renderer", "markup")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set markup renderer for cells {idx_string}"
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_matplotlib_renderer_pressed(self):
        """Matplotlib renderer button pressed event handler"""

        attr_dict = AttrDict([("renderer", "matplotlib")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set matplotlib renderer for cells {idx_string}"
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_lock_pressed(self, toggled: bool):
        """Lock button pressed event handler

        :param toggled: Toggle state

        """

        attr_dict = AttrDict([("locked", toggled)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set locked state to {toggled} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_0(self):
        """Set cell rotation to 0° left button pressed event handler"""

        attr_dict = AttrDict([("angle", 0.0)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set cell rotation to 0° for cells {idx_string}"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_90(self):
        """Set cell rotation to 90° left button pressed event handler"""

        attr_dict = AttrDict([("angle", 90.0)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set cell rotation to 90° for cells {idx_string}"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_180(self):
        """Set cell rotation to 180° left button pressed event handler"""

        attr_dict = AttrDict([("angle", 180.0)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set cell rotation to 180° for cells {idx_string}"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_270(self):
        """Set cell rotation to 270° left button pressed event handler"""

        attr_dict = AttrDict([("angle", 270.0)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set cell rotation to 270° for cells {idx_string}"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_left(self):
        """Justify left button pressed event handler"""

        attr_dict = AttrDict([("justification", "justify_left")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Justify cells {idx_string} left"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_fill(self):
        """Justify fill button pressed event handler"""

        attr_dict = AttrDict([("justification", "justify_fill")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Justify cells {idx_string} filled"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_center(self):
        """Justify center button pressed event handler"""

        attr_dict = AttrDict([("justification", "justify_center")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Justify cells {idx_string} centered"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_right(self):
        """Justify right button pressed event handler"""

        attr_dict = AttrDict([("justification", "justify_right")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Justify cells {idx_string} right"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_top(self):
        """Align top button pressed event handler"""

        attr_dict = AttrDict([("vertical_align", "align_top")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Align cells {idx_string} to top"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_middle(self):
        """Align centere button pressed event handler"""

        attr_dict = AttrDict([("vertical_align", "align_center")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Align cells {idx_string} to center"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_bottom(self):
        """Align bottom button pressed event handler"""

        attr_dict = AttrDict([("vertical_align", "align_bottom")])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Align cells {idx_string} to bottom"
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_border_choice(self):
        """Border choice style event handler"""

        self.main_window.settings.border_choice = self.sender().text()
        self.gui_update()

    def on_text_color(self):
        """Text color change event handler"""

        text_color = self.main_window.widgets.text_color_button.color
        text_color_rgb = text_color.getRgb()
        attr_dict = AttrDict([("textcolor", text_color_rgb)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = \
            f"Set text color to {text_color_rgb} for cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_line_color(self):
        """Line color change event handler"""

        border_choice = self.main_window.settings.border_choice
        bottom_selection = \
            self.selection.get_bottom_borders_selection(border_choice,
                                                        self.model.shape)
        right_selection = \
            self.selection.get_right_borders_selection(border_choice,
                                                       self.model.shape)

        line_color = self.main_window.widgets.line_color_button.color
        line_color_rgb = line_color.getRgb()

        attr_dict_bottom = AttrDict([("bordercolor_bottom", line_color_rgb)])
        attr_bottom = CellAttribute(bottom_selection, self.table,
                                    attr_dict_bottom)
        attr_dict_right = AttrDict([("bordercolor_right", line_color_rgb)])
        attr_right = CellAttribute(right_selection, self.table,
                                   attr_dict_right)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set line color {line_color_rgb} for cells {idx_string}"
        command = commands.SetCellFormat(attr_bottom, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = commands.SetCellFormat(attr_right, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_background_color(self):
        """Background color change event handler"""

        bg_color = self.main_window.widgets.background_color_button.color
        bg_color_rgb = bg_color.getRgb()
        self.gui_update()

        attr_dict = AttrDict([("bgcolor", bg_color_rgb)])
        attr = CellAttribute(self.selection, self.table, attr_dict)
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set cell background color to {bg_color_rgb} for " +\
                      f"cells {idx_string}"
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_borderwidth(self):
        """Border width change event handler"""

        width = int(self.sender().text().split()[-1])

        border_choice = self.main_window.settings.border_choice
        bottom_selection = \
            self.selection.get_bottom_borders_selection(border_choice,
                                                        self.model.shape)
        right_selection = \
            self.selection.get_right_borders_selection(border_choice,
                                                       self.model.shape)

        attr_dict_bottom = AttrDict([("borderwidth_bottom", width)])
        attr_bottom = CellAttribute(bottom_selection, self.table,
                                    attr_dict_bottom)
        attr_dict_right = AttrDict([("borderwidth_right", width)])
        attr_right = CellAttribute(right_selection, self.table,
                                   attr_dict_right)

        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = f"Set border width to {width} for cells {idx_string}"
        command = commands.SetCellFormat(attr_bottom, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = commands.SetCellFormat(attr_right, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def update_cell_spans(self):
        """Update cell spans from model data"""

        self.clearSpans()

        spans = {}  # Dict of (top, left): (bottom, right)

        for _, table, attrs in self.model.code_array.cell_attributes:
            if table == self.table:
                try:
                    if "merge_area" in attrs and attrs.merge_area is not None:
                        top, left, bottom, right = attrs["merge_area"]
                        spans[(top, left)] = bottom, right
                except (KeyError, TypeError):
                    pass

        for top, left in spans:
            try:
                bottom, right = spans[(top, left)]
                self.setSpan(top, left, bottom-top+1, right-left+1)
            except TypeError:
                pass

    def update_index_widgets(self):
        """Remove old index widgets from model data"""

        # Remove old button cells
        for index in self.widget_indices:
            self.setIndexWidget(index, None)
        self.widget_indices.clear()

        # Get button cell candidates
        code_array = self.model.code_array
        button_cell_candidates = []
        for selection, table, attr in code_array.cell_attributes:
            if table == self.table and 'button_cell' in attr \
               and attr['button_cell']:
                row, column = selection.get_bbox()[0]
                button_cell_candidates.append((row, column, table))

        # Add button cells for current table
        for key in set(button_cell_candidates):
            text = code_array.cell_attributes[key]['button_cell']
            if text is not False:  # False would be deleted button cell
                row, column, table = key
                index = self.model.index(row, column, QModelIndex())
                button = CellButton(text, self, key)
                self.setIndexWidget(index, button)
                self.widget_indices.append(index)

    def on_freeze_pressed(self, toggled: bool):
        """Freeze cell event handler

        :param toggled: Toggle state

        """

        grid = self.main_window.focused_grid

        current_attr = self.model.code_array.cell_attributes[grid.current]
        if current_attr.frozen == toggled:
            return  # Something is wrong with the GUI update

        cells = list(self.selection.cell_generator(shape=self.model.shape,
                                                   table=self.table))
        if toggled:
            # We have an non-frozen cell that has to be frozen
            description = f"Freeze cells {cells}"
            command = commands.FreezeCell(self.model, cells, description)
        else:
            # We have an frozen cell that has to be unfrozen
            description = f"Thaw cells {cells}"
            command = commands.ThawCell(self.model, cells, description)
        self.main_window.undo_stack.push(command)

    def on_button_cell_pressed(self, toggled: bool):
        """Button cell event handler

        :param toggled: Toggle state

        """

        grid = self.main_window.focused_grid

        current_attr = grid.model.code_array.cell_attributes[grid.current]
        if not toggled and current_attr.button_cell is False \
           or toggled and current_attr.button_cell is not False:
            # Something is not synchronized in the menu
            return

        if toggled:
            # Get button text from user
            text, accept = QInputDialog.getText(
                self.main_window, "Make button cell", "Button text:",
                QLineEdit.EchoMode.Normal, "")
            if accept and text:
                description = f"Make cell {grid.current} a button cell"
                command = commands.MakeButtonCell(self, text,
                                                  grid.currentIndex(),
                                                  description)
                self.main_window.undo_stack.push(command)
        else:
            description = f"Make cell {grid.current} a non-button cell"
            command = commands.RemoveButtonCell(self, grid.currentIndex(),
                                                description)
            self.main_window.undo_stack.push(command)

    def on_merge_pressed(self):
        """Merge cells button pressed event handler"""

        grid = self.main_window.focused_grid

        # This is not done in the model because setSpan does not work there

        shape = list(self.model.shape)
        shape[0] -= 1
        shape[1] -= 1
        bbox = self.selection.get_grid_bbox(shape)
        (top, left), (bottom, right) = bbox

        # Check if current cell is already merged
        if self.columnSpan(top, left) > 1 or self.rowSpan(top, left) > 1:
            selection = Selection([], [], [], [], [(top, left)])
            attr_dict = AttrDict([("merge_area", None)])
            attr = CellAttribute(selection, self.table, attr_dict)
            description = f"Unmerge cells with top-left cell {(top, left)}"
        elif bottom > top or right > left:
            # Merge and store the current selection
            merging_selection = Selection([], [], [], [], [(top, left)])
            attr_dict = AttrDict([("merge_area", (top, left, bottom, right))])
            attr = CellAttribute(merging_selection, self.table, attr_dict)
            description = "Merge cells with top-left cell {(top, left)}"
        else:
            # Cells are not merged because the span is one
            return

        command = commands.SetCellMerge(attr, self.model, self.currentIndex(),
                                        self.selected_idx, description)
        self.main_window.undo_stack.push(command)

        grid.current = top, left

    def on_quote(self):
        """Quote cells event handler"""

        description = f"Quote code for cell selection {id(self.selection)}"

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            code = self.model.code_array((row, column, self.table))
            quoted_code = quote(code)
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(quoted_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def on_money(self):
        """Make cell money object event handler using default currency"""

        description = f"Money type for cell selection {id(self.selection)}"

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            key = row, column, self.table
            code = self.model.code_array(key)
            res = self.model.code_array[key]
            if isinstance(res, Money):
                return
            if isinstance(res, float):
                code = quote(code)
            currency_iso_code = self.main_window.settings.currency_iso_code
            moneyed_code = f'Money({code}, "{currency_iso_code}")'
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(moneyed_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def on_datetime(self):
        """Make cell datetime object event handler"""

        description = f"Datetime type for cell selection {id(self.selection)}"

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            key = row, column, self.table
            code = self.model.code_array(key)
            res = self.model.code_array[key]
            if isinstance(res, datetime):
                return
            if not isinstance(res, str):
                code = quote(code)
            datetime_code = f'dateutil.parser.parse({code})'
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(datetime_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def on_date(self):
        """Make cell date object event handler"""

        description = f"Date type for cell selection {id(self.selection)}"

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            key = row, column, self.table
            code = self.model.code_array(key)
            res = self.model.code_array[key]
            if isinstance(res, date):
                return
            if not isinstance(res, str):
                code = quote(code)
            datetime_code = f'dateutil.parser.parse({code}).date()'
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(datetime_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def on_time(self):
        """Make cell time object event handler"""

        description = f"Time type for cell selection {id(self.selection)}"

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            key = row, column, self.table
            code = self.model.code_array(key)
            res = self.model.code_array[key]
            if isinstance(res, time):
                return
            if not isinstance(res, str):
                code = quote(code)
            datetime_code = f'dateutil.parser.parse({code}).time()'
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(datetime_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def is_row_data_discarded(self, count: int) -> bool:
        """True if row data is to be discarded on row insertion

        :param count: Rows to be inserted

        """

        no_rows = self.model.shape[0]
        rows = list(range(no_rows-count, no_rows+1))
        selection = Selection([], [], rows, [], [])
        sel_cell_gen = selection.cell_generator(self.model.shape, self.table)
        return any(self.model.code_array(key) is not None
                   for key in sel_cell_gen)

    def is_column_data_discarded(self, count: int) -> bool:
        """True if column data is to be discarded on column insertion

        :param count: Columns to be inserted

        """

        no_columns = self.model.shape[1]
        columns = list(range(no_columns-count, no_columns+1))
        selection = Selection([], [], [], columns, [])
        sel_cell_gen = selection.cell_generator(self.model.shape, self.table)
        return any(self.model.code_array(key) is not None
                   for key in sel_cell_gen)

    def is_table_data_discarded(self, count: int) -> bool:
        """True if table data is to be discarded  on table insertion

        :param count: Tables to be inserted

        """

        no_tables = self.model.shape[2]
        tables = list(range(no_tables-count, no_tables+1))
        return any(key[2] in tables and self.model.code_array(key) is not None
                   for key in self.model.code_array)

    def on_shift_cells_down(self, *,
                            description_tpl: str = "Shift selection {} down"):
        """Insert shift cells down event handler

        :param description_tpl: Description template for `QUndoCommand`

        """

        try:
            (top, left), (bottom, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
            left = right = self.column
        count = bottom - top + 1

        if self.is_row_data_discarded(count):
            text = ("Shifting cells down will discard data.\n \n"
                    "You may want to resize the grid before shifting.")
            if DiscardDataDialog(self.main_window, text).choice is not True:
                return

        selection1 = Selection([(top, left)], [(None, right)], [], [], [])
        self.main_window.workflows.edit_cut(description_tpl=description_tpl,
                                            selection=selection1)

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        selection2 = Selection([(bottom+1, left)], [(None, right)],
                               [], [], [])
        self.main_window.workflows._paste_to_selection(
            selection2, data,
            description_tpl=description_tpl.format(selection1))

    def on_shift_cells_right(
            self, *, description_tpl: str = "Shift selection {} right"):
        """Insert shift cells right event handler

        :param description_tpl: Description template for `QUndoCommand`

        """

        try:
            (top, left), (bottom, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
            left = right = self.column
        count = right - left + 1

        if self.is_column_data_discarded(count):
            text = ("Shifting cells right will discard data.\n \n"
                    "You may want to resize the grid before shifting.")
            if DiscardDataDialog(self.main_window, text).choice is not True:
                return

        selection1 = Selection([(top, left)], [(bottom, None)], [], [], [])
        self.main_window.workflows.edit_cut(description_tpl=description_tpl,
                                            selection=selection1)

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        selection2 = Selection([(top, right+1)], [(bottom, None)],
                               [], [], [])
        self.main_window.workflows._paste_to_selection(
            selection2, data,
            description_tpl=description_tpl.format(selection1))

    def on_delete_shift_cells_up(
            self, *,
            description_tpl: str = "Delete selection {} and shift cells up"):
        """Delete cells and shift below cells up event handler

        :param description_tpl: Description template for `QUndoCommand`

        """

        try:
            (top, left), (bottom, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
            left = right = self.column

        selection1 = Selection([(bottom+1, left)], [(None, right)], [], [], [])
        self.main_window.workflows.edit_cut(description_tpl=description_tpl,
                                            selection=selection1)

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        selection2 = Selection([(top, left)], [(None, right)], [], [], [])
        self.main_window.workflows._paste_to_selection(
            selection2, data,
            description_tpl=description_tpl.format(selection1))

    def on_delete_shift_cells_left(
            self, *,
            description_tpl: str = "Delete selection {} and shift cells left"):
        """Delete cells and shift right cells left event handler

        :param description_tpl: Description template for `QUndoCommand`

        """

        try:
            (top, left), (bottom, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
            left = right = self.column

        selection1 = Selection([(top, right+1)], [(bottom, None)], [], [], [])
        self.main_window.workflows.edit_cut(description_tpl=description_tpl,
                                            selection=selection1)

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        selection2 = Selection([(top, left)], [(bottom, None)],
                               [], [], [])
        self.main_window.workflows._paste_to_selection(
            selection2, data,
            description_tpl=description_tpl.format(selection1))

    def on_insert_rows(self):
        """Insert rows event handler"""

        try:
            (top, _), (bottom, _) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
        count = bottom - top + 1

        if self.is_row_data_discarded(count):
            text = ("Inserting rows will discard data.\n \n"
                    "You may want to resize the grid before insertion.\n"
                    "Note that row insertion can be undone.")
            if DiscardDataDialog(self.main_window, text).choice is not True:
                return

        index = self.currentIndex()
        description = f"Insert {count} rows above row {top}"
        command = commands.InsertRows(self, self.model, index, top, count,
                                      description)
        self.main_window.undo_stack.push(command)

    def on_delete_rows(self):
        """Delete rows event handler"""

        try:
            (top, _), (bottom, _) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
        count = bottom - top + 1

        index = self.currentIndex()
        description = f"Delete {count} rows starting from row {top}"
        command = commands.DeleteRows(self, self.model, index, top, count,
                                      description)
        self.main_window.undo_stack.push(command)

    def on_insert_columns(self):
        """Insert columns event handler"""

        try:
            (_, left), (_, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            left = right = self.column
        count = right - left + 1

        if self.is_column_data_discarded(count):
            text = ("Inserting columns will discard data.\n \n"
                    "You may want to resize the grid before insertion.\n"
                    "Note that column insertion can be undone.")
            if DiscardDataDialog(self.main_window, text).choice is not True:
                return

        index = self.currentIndex()
        description = f"Insert {count} columns left of column {left}"
        command = commands.InsertColumns(self, self.model, index, left, count,
                                         description)
        self.main_window.undo_stack.push(command)

    def on_delete_columns(self):
        """Delete columns event handler"""

        try:
            (_, left), (_, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            left = right = self.column
        count = right - left + 1

        index = self.currentIndex()
        description = \
            f"Delete {count} columns starting from column {self.column}"
        command = commands.DeleteColumns(self, self.model, index, left, count,
                                         description)
        self.main_window.undo_stack.push(command)

    def on_insert_table(self):
        """Insert table event handler"""

        if self.is_table_data_discarded(1):
            text = ("Inserting tables will discard data.\n \n"
                    "You may want to resize the grid before insertion.\n"
                    "Note that table insertion can be undone.")
            if DiscardDataDialog(self.main_window, text).choice is not True:
                return

        description = f"Insert table in front of table {self.table}"
        command = commands.InsertTable(self, self.model, self.table,
                                       description)
        self.main_window.undo_stack.push(command)

    def on_delete_table(self):
        """Delete table event handler"""

        description = f"Delete table {self.table}"
        command = commands.DeleteTable(self, self.model, self.table,
                                       description)
        self.main_window.undo_stack.push(command)


class GridHeaderView(QHeaderView):
    """QHeaderView with zoom support"""

    def __init__(self, orientation: Qt.Orientation, grid: Grid):
        """
        :param orientation: Orientation of the `QHeaderView`
        :param grid: The main grid widget

        """

        super().__init__(orientation, grid)
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.default_section_size = self.defaultSectionSize()
        self.grid = grid

    # Overrides

    def sizeHint(self) -> QSize:
        """Overrides sizeHint, which supports zoom"""

        unzoomed_size = super().sizeHint()
        return QSize(int(unzoomed_size.width() * self.grid.zoom),
                     int(unzoomed_size.height() * self.grid.zoom))

    def sectionSizeHint(self, logicalIndex: int) -> int:
        """Overrides sectionSizeHint, which supports zoom

        :param logicalIndex: Index of the section for the size hint

        """

        unzoomed_size = super().sectionSizeHint(logicalIndex)
        return int(unzoomed_size * self.grid.zoom)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        """Overrides paintSection, which supports zoom

        :param painter: Painter with which the section is drawn
        :param rect: Outer rectangle of the section to be drawn
        :param logicalIndex: Index of the section to be drawn

        """

        zoom = self.grid.zoom

        unzoomed_rect = QRect(0, 0,
                              int(round(rect.width()/zoom)),
                              int(round(rect.height()/zoom)))
        with painter_save(painter):
            painter.translate(rect.x()+1, rect.y()+1)
            painter.scale(zoom, zoom)
            super().paintSection(painter, unzoomed_rect, logicalIndex)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Overrides contextMenuEvent

        Installs HorizontalHeaderContextMenu or VerticalHeaderContextMenu
        depending on self.orientation().

        :param event: The triggering event

        """

        actions = self.grid.main_window.main_window_actions
        if self.orientation() == Qt.Orientation.Horizontal:
            menu = HorizontalHeaderContextMenu(actions)
        else:
            menu = VerticalHeaderContextMenu(actions)
        menu.exec(self.mapToGlobal(event.pos()))

    # End of overrides

    def update_zoom(self):
        """Updates zoom for the section sizes"""

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                default_size = int(self.default_section_size * self.grid.zoom)
                self.setDefaultSectionSize(default_size)

                # Fix for PyQt6 setDefaultSectionSize not working
                for section in range(self.count()):
                    self.resizeSection(section, default_size)

                if self.orientation() == Qt.Orientation.Horizontal:
                    section_sizes = self.grid.column_widths
                else:
                    section_sizes = self.grid.row_heights

                for section, size in section_sizes:
                    self.resizeSection(section, int(size * self.grid.zoom))


class GridTableModel(QAbstractTableModel):
    """QAbstractTableModel for Grid"""

    cell_to_update = pyqtSignal(tuple)

    def __init__(self, main_window: QMainWindow,
                 shape: Tuple[int, int, int]):
        """
        :param main_window: Application main window
        :param shape: Grid shape `(rows, columns, tables)`

        """

        super().__init__()

        self.main_window = main_window
        self.code_array = CodeArray(shape, main_window.settings)

    @contextmanager
    def model_reset(self):
        """Context manager for handle changing/resetting model data"""

        self.beginResetModel()
        yield
        self.endResetModel()

    @contextmanager
    def inserting_rows(self, index: QModelIndex, first: int, last: int):
        """Context manager for inserting rows

        see `QAbstractItemModel.beginInsertRows`

        :param index: Parent into which the new rows are inserted
        :param first: Row number that first row will have after insertion
        :param last: Row number that last row will have after insertion

        """

        self.beginInsertRows(index, first, last)
        yield
        self.endInsertRows()

    @contextmanager
    def inserting_columns(self, index: QModelIndex, first: int, last: int):
        """Context manager for inserting columns

        see `QAbstractItemModel.beginInsertColumns`

        :param index: Parent into which the new columns are inserted
        :param first: Column number that first column will have after insertion
        :param last: Column number that last column will have after insertion

        """

        self.beginInsertColumns(index, first, last)
        yield
        self.endInsertColumns()

    @contextmanager
    def removing_rows(self, index: QModelIndex, first: int, last: int):
        """Context manager for removing rows

        see `QAbstractItemModel.beginRemoveRows`

        :param index: Parent from which rows are removed
        :param first: Row number of the first row to be removed
        :param last: Row number of the last row to be removed

        """

        self.beginRemoveRows(index, first, last)
        yield
        self.endRemoveRows()

    @contextmanager
    def removing_columns(self, index: QModelIndex, first: int, last: int):
        """Context manager for removing columns

        see `QAbstractItemModel.beginRemoveColumns`

        :param index: Parent from which columns are removed
        :param first: Column number of the first column to be removed
        :param last: Column number of the last column to be removed

        """

        self.beginRemoveColumns(index, first, last)
        yield
        self.endRemoveColumns()

    @property
    def grid(self) -> Grid:
        """The main grid"""

        return self.main_window.grid

    @property
    def shape(self) -> Tuple[int, int, int]:
        """Returns 3-tuple of rows, columns and tables"""

        return self.code_array.shape

    @shape.setter
    def shape(self, value: Tuple[int, int, int]):
        """Sets the shape in the code array and adjusts the table_choice

        :param value: Grid shape `(rows, columns, tables)`

        """

        check_shape_validity(value, self.main_window.settings.maxshape)

        with self.model_reset():
            self.code_array.shape = value
            self.grid.table_choice.no_tables = value[2]

    def current(self, index: QModelIndex) -> Tuple[int, int, int]:
        """Tuple of row, column, table of given index

        :param index: Index of the cell to be made the current cell

        """

        return index.row(), index.column(), self.main_window.grid.table

    def code(self, index: QModelIndex) -> str:
        """Code in cell index

        :param index: Index of the cell for which the code is returned

        """

        return self.code_array(self.current(index))

    def rowCount(self, _: QModelIndex = QModelIndex()) -> int:
        """Overloaded `QAbstractItemModel.rowCount` for code_array backend"""

        return self.shape[0]

    def columnCount(self, _: QModelIndex = QModelIndex()) -> int:
        """Overloaded `QAbstractItemModel.columnCount` for code_array backend
        """

        return self.shape[1]

    def insertRows(self, row: int, count: int) -> bool:
        """Overloaded `QAbstractItemModel.insertRows` for code_array backend

        :param row: Row at which rows are inserted
        :param count: Number of rows to be inserted

        """

        self.code_array.insert(row, count, axis=0, tab=self.grid.table)
        return True

    def removeRows(self, row: int, count: int) -> bool:
        """Overloaded `QAbstractItemModel.removeRows` for code_array backend

        :param row: Row at which rows are removed
        :param count: Number of rows to be removed

        """

        try:
            self.code_array.delete(row, count, axis=0, tab=self.grid.table)
        except ValueError:
            return False
        return True

    def insertColumns(self, column: int, count: int) -> bool:
        """Overloaded `QAbstractItemModel.insertColumns` for code_array backend

        :param column: Column at which columns are inserted
        :param count: Number of columns to be inserted

        """

        self.code_array.insert(column, count, axis=1, tab=self.grid.table)
        return True

    def removeColumns(self, column: int, count: int) -> bool:
        """Overloaded `QAbstractItemModel.removeColumns` for code_array backend

        :param column: Column at which columns are removed
        :param count: Number of columns to be removed

        """

        try:
            self.code_array.delete(column, count, axis=1, tab=self.grid.table)
        except ValueError:
            return False
        return True

    def insertTable(self, table: int, count: int = 1):
        """Inserts tables

        :param table: Table at which tables are inserted
        :param count: Number of tables to be inserted

        """

        self.code_array.insert(table, count, axis=2)

    def removeTable(self, table: int, count: int = 1):
        """Removes tables

        :param table: Table at which tables are removed
        :param count: Number of tables to be removed

        """

        self.code_array.delete(table, count, axis=2)

    def font(self, key: Tuple[int, int, int]) -> QFont:
        """Returns font for given key

        :param key: Key of cell, for which font is returned

        """

        attr = self.code_array.cell_attributes[key]
        font = QFont()
        if attr.textfont is not None:
            font.setFamily(attr.textfont)
        if attr.pointsize is not None:
            font.setPointSizeF(attr.pointsize)
        if attr.fontweight is not None:
            font.setWeight(qt52qt6_fontweights(attr.fontweight))
        if attr.fontstyle is not None:
            fontstyle = attr.fontstyle
            if isinstance(fontstyle, int):
                fontstyle = FONTSTYLES[fontstyle]
            font.setStyle(fontstyle)
        if attr.underline is not None:
            font.setUnderline(attr.underline)
        if attr.strikethrough is not None:
            font.setStrikeOut(attr.strikethrough)
        return font

    def data(self, index: QModelIndex,
             role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        """Overloaded data for code_array backend

        :param index: Index of the cell, for which data is returned
        :param role: Role of data to be returned

        """

        def safe_str(obj) -> str:
            """Returns str(obj), on RecursionError returns error message"""
            try:
                if obj.__class__ in class_format_functions:
                    format_function = class_format_functions[obj.__class__]
                    return format_function(obj)

                return str(obj)
            except Exception as err:
                return str(err)

        key = self.current(index)

        if role == Qt.ItemDataRole.DisplayRole:
            value = self.code_array[key]
            renderer = self.code_array.cell_attributes[key].renderer
            if renderer == "image" or value is None:
                return ""
            return safe_str(value)

        if role == Qt.ItemDataRole.ToolTipRole:
            value = self.code_array[key]
            if value is None:
                return ""
            return wrap_text(safe_str(value))

        if role == Qt.ItemDataRole.DecorationRole:
            renderer = self.code_array.cell_attributes[key].renderer
            if renderer == "image":
                value = self.code_array[key]
                if isinstance(value, QImage):
                    return value
                try:
                    arr = numpy.array(value)
                    return array2qimage(arr)
                except Exception:
                    return value

        if role == Qt.ItemDataRole.BackgroundRole:
            if self.main_window.settings.show_frozen \
               and self.code_array.cell_attributes[key].frozen:
                pattern_rgb = self.grid.palette().color(ColorRole.highlight)
                bg_color = QBrush(pattern_rgb, Qt.BrushStyle.BDiagPattern)
            else:
                bg_color_rgb = self.code_array.cell_attributes[key].bgcolor
                if bg_color_rgb is None:
                    bg_color = self.grid.palette().color(ColorRole.bg)
                else:
                    bg_color = QColor(*bg_color_rgb)
            return bg_color

        if role == Qt.ItemDataRole.ForegroundRole:
            text_color_rgb = self.code_array.cell_attributes[key].textcolor
            if text_color_rgb is None:
                text_color = self.grid.palette().color(ColorRole.text)
            else:
                text_color = QColor(*text_color_rgb)
            return text_color

        if role == Qt.ItemDataRole.FontRole:
            return self.font(key)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            pys2qt = {
                "justify_left": Qt.AlignmentFlag.AlignLeft,
                "justify_center": Qt.AlignmentFlag.AlignHCenter,
                "justify_right": Qt.AlignmentFlag.AlignRight,
                "justify_fill": Qt.AlignmentFlag.AlignJustify,
                "align_top": Qt.AlignmentFlag.AlignTop,
                "align_center": Qt.AlignmentFlag.AlignVCenter,
                "align_bottom": Qt.AlignmentFlag.AlignBottom,
            }
            attr = self.code_array.cell_attributes[key]
            alignment = pys2qt[attr.vertical_align]
            justification = pys2qt[attr.justification]
            alignment |= justification
            return alignment

        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole,
                raw: bool = False, table: int = None) -> bool:
        """Overloaded setData for code_array backend

        :param index: Index of the cell, for which data is set
        :param value: Value of data to be set
        :param role: Role of data to be set
        :param raw: Sets raw data without string formatting in `EditRole`
        :param table: Table for which data shall is set

        """

        if role == Qt.ItemDataRole.EditRole:
            if table is None:
                key = self.current(index)
            else:
                key = index.row(), index.column(), table

            if raw:
                if value is None:
                    try:
                        self.code_array.pop(key)
                    except KeyError:
                        pass
                else:
                    self.code_array[key] = value
            else:
                self.code_array[key] = f"{value}"

            if not self.main_window.prevent_updates:
                self.dataChanged.emit(index, index)

            return True

        if role in (Qt.ItemDataRole.DecorationRole,
                    Qt.ItemDataRole.TextAlignmentRole):
            if not isinstance(value[2], AttrDict):
                raise Warning(f"{value[2]} has type {type(value[2])} that "
                              "is not instance of AttrDict")
            self.code_array.cell_attributes.append(value)
            # We have a selection and no single cell
            with self.main_window.workflows.busy_cursor():
                with self.main_window.entry_line.disable_updates():
                    with self.main_window.workflows.prevent_updates():
                        for idx in index:
                            self.dataChanged.emit(idx, idx)
            return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Overloaded, makes items editable

        :param index: Index of cell for which flags are returned

        """

        return QAbstractTableModel.flags(self,
                                         index) | Qt.ItemFlag.ItemIsEditable

    def headerData(self, idx: QModelIndex, _, role: Qt.ItemDataRole) -> str:
        """Overloaded for displaying numbers in header

        :param idx: Index of header for which data is returned
        :param role: Role of data to be returned

        """

        if role == Qt.ItemDataRole.DisplayRole:
            return str(idx)

    def reset(self):
        """Deletes all grid data including undo data"""

        with self.model_reset():
            # Clear cells
            self.code_array.dict_grid.clear()

            # Clear attributes
            del self.code_array.dict_grid.cell_attributes[:]

            # Clear row heights and column widths
            self.code_array.row_heights.clear()
            self.code_array.col_widths.clear()

            # Clear macros
            self.code_array.macros = ""

            # Clear caches
            # self.main_window.undo_stack.clear()
            self.code_array.result_cache.clear()

            # Clear globals
            self.code_array.clear_globals()
            self.code_array.reload_modules()


class GridCellDelegate(QStyledItemDelegate):
    """QStyledItemDelegate for main grid QTableView"""

    def __init__(self, main_window: QMainWindow, grid: Grid,
                 code_array: CodeArray):
        """
        :param main_window: Application main window
        :param grid: Grid, i.e. QTableView instance
        :param code_array: Main backend model instance

        """

        super().__init__()

        self.main_window = main_window
        self.grid = grid
        self.code_array = code_array
        self.cell_attributes = self.code_array.cell_attributes

    def _get_render_text_document(self, rect: QRectF,
                                  option: QStyleOptionViewItem,
                                  index: QModelIndex) -> QTextDocument:
        """Returns styled QTextDocument that is ready for setting content

        :param rect: Cell rect of the cell to be painted
        :param option: Style option for rendering
        :param index: Index of cell for which markup is rendered

        """

        doc = QTextDocument()

        font = self.grid.model.data(index, role=Qt.ItemDataRole.FontRole)
        doc.setDefaultFont(font)

        alignment = self.grid.model.data(
            index, role=Qt.ItemDataRole.TextAlignmentRole)
        doc.setDefaultTextOption(QTextOption(alignment))

        bg_color = self.grid.model.data(index,
                                        role=Qt.ItemDataRole.BackgroundRole)
        css = f"background-color: {bg_color};"
        doc.setDefaultStyleSheet(css)

        doc.setTextWidth(rect.width())

        doc.setUseDesignMetrics(True)

        text_option = doc.defaultTextOption()
        text_option.setWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        doc.setDefaultTextOption(text_option)

        return doc

    def _render_text_document(self, doc: QTextDocument,
                              painter: QPainter, rect: QRectF,
                              option: QStyleOptionViewItem,
                              index: QModelIndex):
        """QTextDocument renderer

        :param doc: Text document to be painted
        :param painter: Painter with which markup is rendered
        :param rect: Cell rect of the cell to be painted
        :param option: Style option for rendering
        :param index: Index of cell for which markup is rendered

        """

        style = option.widget.style()
        option.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option,
                          painter, option.widget)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        text_color = self.grid.model.data(index,
                                          role=Qt.ItemDataRole.ForegroundRole)
        ctx.palette.setColor(ColorRole.text, text_color)

        key = index.row(), index.column(), self.grid.table
        vertical_align = self.cell_attributes[key].vertical_align

        y_offset = 0
        if vertical_align == 'align_center':
            y_offset += rect.height() / 2 - doc.size().height() / 2
        elif vertical_align == 'align_bottom':
            y_offset += rect.height() - doc.size().height()

        with painter_save(painter):
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.documentLayout().draw(painter, ctx)

    def _render_text(self, painter: QPainter, rect: QRectF,
                     option: QStyleOptionViewItem, index: QModelIndex):
        """Text renderer

        :param painter: Painter with which markup is rendered
        :param rect: Cell rect of the cell to be painted
        :param option: Style option for rendering
        :param index: Index of cell for which markup is rendered

        """

        self.initStyleOption(option, index)

        doc = self._get_render_text_document(rect, option, index)
        doc.setPlainText(option.text)
        self._render_text_document(doc, painter, rect, option, index)

    def _render_markup(self, painter: QPainter, rect: QRectF,
                       option: QStyleOptionViewItem, index: QModelIndex):
        """HTML markup renderer

        :param painter: Painter with which markup is rendered
        :param rect: Cell rect of the cell to be painted
        :param option: Style option for rendering
        :param index: Index of cell for which markup is rendered

        """

        self.initStyleOption(option, index)

        doc = self._get_render_text_document(rect, option, index)
        doc.setHtml(option.text)
        self._render_text_document(doc, painter, rect, option, index)

    def _get_aligned_image_rect(
            self, rect: QRectF, index: QModelIndex,
            image_width: Union[int, float],
            image_height: Union[int, float]) -> QRectF:
        """Returns image rect dependent on alignment and justification

        :param rect: Rect to be aligned
        :param image_width: Width of image [px]
        :param image_height: Height of image [px]

        """

        def scale_size(inner_width: Union[int, float],
                       inner_height: Union[int, float],
                       outer_width: Union[int, float],
                       outer_height: Union[int, float]) -> Tuple[float, float]:
            """Scales up inner_rect to fit in outer_rect

            Returns width, height tuple that maintains aspect ratio.

            :param inner_width: Width of inner rect (scaled to outer rect)
            :param inner_height: Height of inner rect (scaled to outer rect)
            :param outer_width: Width of outer rect
            :param outer_height: Height of outer rect

            """

            if inner_width and inner_height and outer_width and outer_height:
                inner_aspect = inner_width / inner_height
                outer_aspect = outer_width / outer_height

                if outer_aspect < inner_aspect:
                    inner_width *= outer_width / inner_width
                    inner_height = inner_width / inner_aspect
                else:
                    inner_height *= outer_height / inner_height
                    inner_width = inner_height * inner_aspect

            return inner_width, inner_height

        key = index.row(), index.column(), self.grid.table

        justification = self.cell_attributes[key].justification
        vertical_align = self.cell_attributes[key].vertical_align

        if justification == "justify_fill":
            return rect

        try:
            image_width, image_height = scale_size(image_width, image_height,
                                                   rect.width(), rect.height())
        except ZeroDivisionError:
            pass

        image_x, image_y = rect.x(), rect.y()

        if justification == "justify_center":
            image_x = rect.x() + rect.width() / 2 - image_width / 2
        elif justification == "justify_right":
            image_x = rect.x() + rect.width() - image_width

        if vertical_align == "align_center":
            image_y = rect.y() + rect.height() / 2 - image_height / 2
        elif vertical_align == "align_bottom":
            image_y = rect.y() + rect.height() - image_height

        return QRectF(image_x, image_y, image_width, image_height)

    def _render_qimage(self, painter: QPainter, rect: QRectF,
                       index: QModelIndex, qimage: QImage = None):
        """QImage renderer

        :param painter: Painter with which qimage is rendered
        :param rect: Cell rect of the cell to be painted
        :param index: Index of cell for which qimage is rendered
        :param qimage: Image to be rendered, decoration drawn if not provided

        """

        if qimage is None:
            qimage = index.data(Qt.ItemDataRole.DecorationRole)

        if not isinstance(qimage, QImage):
            raise TypeError(f"{qimage} not of type QImage")

        img_width, img_height = qimage.width(), qimage.height()

        img_rect = self._get_aligned_image_rect(rect, index,
                                                img_width, img_height)
        if img_rect is None:
            return

        key = index.row(), index.column(), self.grid.table
        justification = self.cell_attributes[key].justification

        if justification == "justify_fill":
            qimage = qimage.scaled(int(img_width), int(img_height),
                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        else:
            try:
                qimage = qimage.scaled(int(img_width), int(img_height),
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)

            except AttributeError:
                qimage = qimage.scaled(int(img_width), int(img_height))

        with painter_save(painter):
            try:
                scale_x = img_rect.width() / img_width
            except ZeroDivisionError:
                scale_x = 1
            try:
                scale_y = img_rect.height() / img_height
            except ZeroDivisionError:
                scale_y = 1
            painter.translate(img_rect.x(), img_rect.y())
            painter.scale(scale_x, scale_y)
            painter.drawImage(0, 0, qimage)

    def _render_svg(self, painter: QPainter, rect: QRectF, index: QModelIndex,
                    svg_str: str = None):
        """SVG renderer

        :param painter: Painter with which qimage is rendered
        :param rect: Cell rect of the cell to be painted
        :param index: Index of cell for which qimage is rendered
        :param svg_str: SVG string

        """

        if svg_str is None:
            svg_str = index.data(Qt.ItemDataRole.DecorationRole)

        if svg_str is None:
            return
        try:
            svg_bytes = bytes(svg_str)
        except TypeError:
            try:
                svg_bytes = bytes(svg_str, encoding='utf-8')
            except TypeError:
                return

        if not is_svg(svg_bytes):
            return

        key = index.row(), index.column(), self.grid.table
        justification = self.cell_attributes[key].justification

        svg = QSvgRenderer(QByteArray(svg_bytes))

        if justification == "justify_fill":
            svg.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
            svg_rect = rect
            svg.render(painter, svg_rect)
            return

        try:
            svg.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        except AttributeError:
            pass

        svg_size = svg.defaultSize()

        try:
            svg_aspect = svg_size.width() / svg_size.height()
        except ZeroDivisionError:
            svg_aspect = 1
        try:
            rect_aspect = rect.width() / rect.height()
        except ZeroDivisionError:
            rect_aspect = 1

        if svg_aspect > rect_aspect:
            # svg is wider than rect
            svg_width = rect.width()
            svg_height = rect.width() / svg_aspect
        else:
            # svg is taller than rect
            svg_width = rect.height() * svg_aspect
            svg_height = rect.height()

        svg_rect = self._get_aligned_image_rect(rect, index,
                                                svg_width, svg_height)

        if svg_rect is None:
            return

        svg.render(painter, svg_rect)

    def _render_matplotlib(self, painter: QPainter, rect: QRectF,
                           index: QModelIndex):
        """Matplotlib renderer

        :param painter: Painter with which the matplotlib image is rendered
        :param rect: Cell rect of the cell to be painted
        :param index: Index of cell for which the matplotlib image is rendered

        """

        if matplotlib is None:
            # matplotlib is not installed
            return

        key = index.row(), index.column(), self.grid.table
        figure = self.code_array[key]

        if isinstance(figure, bytes) or isinstance(figure, str):
            # We try rendering the content as SVG
            return self._render_svg(painter, rect, index, figure)

        if not isinstance(figure, matplotlib.figure.Figure):
            return

        # Save SVG in a fake file object.
        with BytesIO() as filelike:
            try:
                figure.savefig(filelike, format="svg", bbox_inches="tight")
            except Exception:
                return
            svg_str = filelike.getvalue().decode()

        self._render_svg(painter, rect, index, svg_str=svg_str)

    def paint_(self, painter: QPainter, rect: QRectF,
               option: QStyleOptionViewItem, index: QModelIndex):
        """Calls the overloaded paint function or creates html delegate

        :param painter: Painter with which borders are drawn
        :param rect: Cell rect of the cell to be painted
        :param option: Style option for rendering
        :param index: Index of cell for which borders are drawn

        """

        painter.setRenderHints(QPainter.RenderHint.LosslessImageRendering
                               | QPainter.RenderHint.Antialiasing
                               | QPainter.RenderHint.TextAntialiasing
                               | QPainter.RenderHint.SmoothPixmapTransform)

        key = index.row(), index.column(), self.grid.table
        renderer = self.cell_attributes[key].renderer

        old_rect = option.rect
        option.rect = QRect(int(rect.x()), int(rect.y()),
                            int(rect.width() + 1.5),
                            int(rect.height() + 1.5))

        if renderer == "text":
            self._render_text(painter, rect, option, index)

        elif renderer == "markup":
            self._render_markup(painter, rect, option, index)

        elif renderer == "image":
            image = index.data(Qt.ItemDataRole.DecorationRole)
            if isinstance(image, QImage):
                self._render_qimage(painter, rect, index)
            elif isinstance(image, str):
                self._render_svg(painter, rect, index)

        elif renderer == "matplotlib":
            self._render_matplotlib(painter, rect, index)

        option.rect = old_rect

    def sizeHint(self, option: QStyleOptionViewItem,
                 index: QModelIndex) -> QSize:
        """Overloads SizeHint

        :param option: Style option for rendering
        :param index: Index of the cell for the size hint

        """

        key = index.row(), index.column(), self.grid.table
        if not self.cell_attributes[key].renderer == "markup":
            return super().sizeHint(option, index)

        # HTML
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())

        return QSize(doc.idealWidth(), doc.size().height())

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex):
        """Overloads `QStyledItemDelegate` to add cell border painting

        :param painter: Painter with which borders are drawn
        :param option: Style option for rendering
        :param index: Index of cell to be rendered

        """

        renderer = CellRenderer(self.grid, painter, option, index)
        renderer.paint()

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        """Overloads `QStyledItemDelegate`

        Disables editor in locked cells
        Switches to chart dialog in chart cells

        :param parent: Parent widget for the cell editor to be returned
        :param option: Style option for the cell editor
        :param index: Index of cell for which a cell editor is created

        """

        key = index.row(), index.column(), self.grid.table

        if self.cell_attributes[key].locked:
            return

        if self.cell_attributes[key].renderer == "matplotlib":
            self.main_window.workflows.macro_insert_chart()
            return

        self.editor = super().createEditor(parent, option, index)
        self.editor.setPalette(self.editor.style().standardPalette())
        self.editor.installEventFilter(self)
        return self.editor

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Overloads `eventFilter`. Overrides QLineEdit default shortcut.

        Quotes cell editor content for <Ctrl>+<Enter> and <Ctrl>+<Return>.
        Counts as undoable action.

        :param source: Source widget of event
        :param event: Any QEvent

        """

        if event.type() == QEvent.Type.ShortcutOverride \
           and source is self.editor \
           and event.modifiers() == Qt.KeyboardModifier.ControlModifier \
           and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

            code = quote(source.text())
            index = self.grid.currentIndex()
            description = f"Quote code for cell {index}"
            cmd = commands.SetCellCode(code, self.grid.model, index,
                                       description)
            self.main_window.undo_stack.push(cmd)
        return super().eventFilter(source, event)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        """Overloads `setEditorData` to use code_array data

        :param editor: Cell editor, in which data is set
        :param index: Index of cell from which the cell editor data is set

        """

        row = index.row()
        column = index.column()
        table = self.grid.table

        value = self.code_array((row, column, table))
        editor.setText(value)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel,
                     index: QModelIndex):
        """Overloads `setModelData` to use code_array data

        :param editor: Cell editor, from which data is retrieved
        :param model: `GridTableModel`
        :param index: Index of cell for which data is set

        """

        description = f"Set code for cell {model.current(index)}"
        command = commands.SetCellCode(editor.text(), model, index,
                                       description)
        self.main_window.undo_stack.push(command)

    def updateEditorGeometry(self, editor: QWidget,
                             option: QStyleOptionViewItem, _: QModelIndex):
        """Overloads `updateEditorGeometry` to update editor geometry to cell

        :param editor: Cell editor, for which geometry is retrieved
        :param option: Style option of the editor

        """

        editor.setGeometry(option.rect)


class TableChoice(QTabBar):
    """The TabBar below the main grid"""

    def __init__(self, main_window: QMainWindow, no_tables: int):
        """
        :param main_window: Application main window
        :param no_tables: Number of tables to be initially created

        """

        super().__init__(shape=QTabBar.Shape.RoundedSouth)
        self.setExpanding(False)

        self.main_window = main_window
        self.no_tables = no_tables

        self.last = 0

        self.currentChanged.connect(self.on_table_changed)

    @property
    def no_tables(self) -> int:
        """Returns the number of tables in the table_choice"""

        return self._no_tables

    @no_tables.setter
    def no_tables(self, value: int):
        """Sets the number of tables in the table_choice

        :param value: Number of tables

        """
        self._no_tables = value

        if value > self.count():
            # Insert
            for i in range(self.count(), value):
                self.addTab(str(i))

        elif value < self.count():
            # Remove
            for i in range(self.count()-1, value-1, -1):
                self.removeTab(i)

    @property
    def table(self) -> int:
        """Returns current table from table_choice that is displayed"""

        return self.currentIndex()

    @table.setter
    def table(self, value: int):
        """Sets a new table to be displayed

        :param value: Number of the table

        """

        self.setCurrentIndex(value)

    # Overrides

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Overrides contextMenuEvent to install GridContextMenu

        :param event: Triggering event

        """

        actions = self.main_window.main_window_actions

        menu = TableChoiceContextMenu(actions)
        menu.exec(self.mapToGlobal(event.pos()))

    # Event handlers

    def on_table_changed(self, current: int):
        """Event handler for table changes

        :param current: The current table to be displayed

        """

        for grid in self.main_window.grids:
            grid.table = current
            grid.table_scrolls[self.last] = \
                (grid.verticalScrollBar().value(),
                 grid.horizontalScrollBar().value())

            with grid.undo_resizing_row():
                with grid.undo_resizing_column():
                    grid.update_cell_spans()
                    grid.update_zoom()

            grid.update_index_widgets()
            grid.gui_update()
            try:
                v_pos, h_pos = grid.table_scrolls[current]
            except KeyError:
                v_pos = h_pos = 0
            grid.verticalScrollBar().setValue(v_pos)
            grid.horizontalScrollBar().setValue(h_pos)

        self.last = current

        # Update entryline
        try:
            self.main_window.grid.on_current_changed()
        except AttributeError:
            pass
