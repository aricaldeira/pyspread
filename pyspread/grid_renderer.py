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

 * :class:`CellRenderer`

"""

from contextlib import contextmanager
from typing import List, Tuple

from PyQt5.QtCore import Qt, QModelIndex, QRectF, QLineF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPalette, QPen
from PyQt5.QtWidgets import QTableView, QStyleOptionViewItem


@contextmanager
def painter_save(painter: QPainter):
    """Saves and restores the painter during a context

    :param painter: Painter, for which the state is preserved

    """

    painter.save()
    yield
    painter.restore()


@contextmanager
def painter_zoom(painter: QPainter, zoom: float, rect: QRectF) -> QRectF:
    """Scales the painter during a context, (rect.x(), rect.y()) is invariant

    :param painter: Painter, for which the state is preserved
    :param zoom: Zoom factor
    :param rect: Rect for setting zoom invariant point (rect.x(), rect.y())

    """

    with painter_save(painter):
        painter.translate(rect.x(), rect.y())
        painter.scale(zoom, zoom)
        painter.translate(-rect.x() * zoom, -rect.y() * zoom)
        yield QRectF(rect.x() * zoom, rect.y() * zoom,
                     rect.width() / zoom, rect.height() / zoom)


@contextmanager
def painter_rotate(painter: QPainter, rect: QRectF, angle: int = 0) -> QRectF:
    """Saves and restores the painter during a context

    :param painter: Painter, which is rotated
    :param rect: Rect to be painted in
    :param angle: Rotataion angle must be in (0, 90, 180, 270)

    """

    supported_angles = 0, 90, 180, 270
    angle = int(angle)

    if angle not in supported_angles:
        msg = "Rotation angle {} not in {}".format(angle, supported_angles)
        raise Warning(msg)
        return

    center_x, center_y = rect.center().x(), rect.center().y()

    with painter_save(painter):
        painter.translate(center_x, center_y)
        painter.rotate(angle)

        if angle in (0, 180):
            painter.translate(-center_x, -center_y)
        elif angle in (90, 270):
            painter.translate(-center_y, -center_x)
            rect = QRectF(rect.y(), rect.x(), rect.height(), rect.width())
        yield rect


class GridCellNavigator:
    """Find neighbors of a cell"""

    def __init__(self, grid: QTableView, key: Tuple[int, int, int]):
        """
        :param grid: The main grid widget
        :param key: Key of cell fow which neighbors are identified

        """

        self.grid = grid
        self.code_array = grid.model.code_array
        self.row, self.column, self.table = self.key = key

    @property
    def borderwidth_bottom(self) -> float:
        """Width of bottom border line"""

        return self.code_array.cell_attributes[self.key].borderwidth_bottom

    @property
    def borderwidth_right(self) -> float:
        """Width of right border line"""

        return self.code_array.cell_attributes[self.key].borderwidth_right

    @property
    def border_qcolor_bottom(self) -> QColor:
        """Color of bottom border line"""

        color = self.code_array.cell_attributes[self.key].bordercolor_bottom
        if color is None:
            return self.grid.palette().color(QPalette.Mid)
        return QColor(*color)

    @property
    def border_qcolor_right(self) -> QColor:
        """Color of right border line"""

        color = self.code_array.cell_attributes[self.key].bordercolor_right
        if color is None:
            return self.grid.palette().color(QPalette.Mid)
        return QColor(*color)

    @property
    def merge_area(self) -> Tuple[int, int, int, int]:
        """Merge area of the key cell"""

        return self.code_array.cell_attributes[self.key].merge_area

    def _merging_key(self, key: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Merging cell if cell is merged else cell key

        :param key: Key of cell that is checked for being merged

        """

        merging_key = self.code_array.cell_attributes.get_merging_cell(key)
        return key if merging_key is None else merging_key

    def above_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells above the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key((self.row - 1, self.column, self.table))]
        _, left, _, right = merge_area
        return [self._merging_key((self.row - 1, col, self.table))
                for col in range(left, right + 1)]

    def below_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells below the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key((self.row + 1, self.column, self.table))]
        _, left, _, right = merge_area
        return [self._merging_key((self.row + 1, col, self.table))
                for col in range(left, right + 1)]

    def left_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells left of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key((self.row, self.column - 1, self.table))]
        top, _, bottom, _ = merge_area
        return [self._merging_key((row, self.column - 1, self.table))
                for row in range(top, bottom + 1)]

    def right_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells right of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key((self.row, self.column + 1, self.table))]
        top, _, bottom, _ = merge_area
        return [self._merging_key((row, self.column + 1, self.table))
                for row in range(top, bottom + 1)]

    def above_left_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell above left of the key cell"""

        return self._merging_key((self.row - 1, self.column - 1, self.table))

    def above_right_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell above right of the key cell"""

        return self._merging_key((self.row - 1, self.column + 1, self.table))

    def below_left_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell below left of the key cell"""

        return self._merging_key((self.row + 1, self.column - 1, self.table))

    def below_right_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell below right of the key cell"""

        return self._merging_key((self.row + 1, self.column + 1, self.table))


class CellRenderer:
    """Renders a cell

    Cell rendering governs the area of a cell inside its borders.
    It is done in a  vector oriented way.
    Therefore, the following conventions shall apply:
     * Cell borders of width 1 shall be painted so that they appear only in the
       bottom and right edge of the cell.
     * Cell borders of all widths have the same center line.
     * Cell borders that are thicker than 1 are painted on all borders.
     * At the edges, borders are painted in the following order:
        1. Thin borders are painted first
        2. If border width is equal, lighter colors are painted first

    """

    def __init__(self, grid: QTableView, painter: QPainter,
                 option: QStyleOptionViewItem, index: QModelIndex):
        """
        :param grid: The main grid widget
        :param painter: Painter with which borders are drawn
        :param option: Style option for rendering
        :param index: Index of cell to be rendered
        """

        self.grid = grid
        self.painter = painter
        self.option = option
        self.index = index

        self.cell_attributes = grid.model.code_array.cell_attributes
        self.key = index.row(), index.column(), self.grid.table

        self.cell_nav = GridCellNavigator(grid, self.key)

    def inner_rect(self, rect: QRectF, zoom: float) -> QRectF:
        """Returns inner rect that is shrunk by border widths

        For merged cells, minimum top/left border widths are taken into account

        :param rect: Cell rect to be shrunk
        :param zoom: Zoom level of the cell

        """

        above_keys = self.cell_nav.above_keys()
        left_keys = self.cell_nav.left_keys()

        width_top = min(self.cell_attributes[above_key].borderwidth_bottom
                        for above_key in above_keys)
        width_left = min(self.cell_attributes[left_key].borderwidth_right
                         for left_key in left_keys)
        width_bottom = self.cell_nav.borderwidth_bottom
        width_right = self.cell_nav.borderwidth_right

        width_top *= zoom
        width_left *= zoom
        width_bottom *= zoom
        width_right *= zoom

        rect_x = rect.x() + width_left / 2
        rect_y = rect.y() + width_top / 2
        rect_width = rect.width() - width_left / 2 - width_right / 2
        rect_height = rect.height() - width_top / 2 - width_bottom / 2

        return QRectF(rect_x, rect_y, rect_width, rect_height)

    def paint_content(self, rect: QRectF):
        """"""

        with painter_zoom(self.painter, self.grid.zoom, rect) as rect:
            pass

    def paint_bottom_border(self, rect: QRectF):
        """Paint bottom border of cell

        :param rect: Cell rect of the cell to be painted

        """

        if not self.cell_nav.borderwidth_bottom:
            return

        line_color = self.cell_nav.border_qcolor_bottom
        line_width = self.cell_nav.borderwidth_bottom * self.grid.zoom
        self.painter.setPen(QPen(QBrush(line_color), line_width))

        bottom_border_line = QLineF(rect.x(),
                                    rect.y() + rect.height(),
                                    rect.x() + rect.width(),
                                    rect.y() + rect.height())
        self.painter.drawLine(bottom_border_line)

    def paint_right_border(self, rect: QRectF):
        """Paint right border of cell

        :param rect: Cell rect of the cell to be painted

        """

        if not self.cell_nav.borderwidth_right:
            return

        line_color = self.cell_nav.border_qcolor_right
        line_width = self.cell_nav.borderwidth_right * self.grid.zoom
        self.painter.setPen(QPen(QBrush(line_color), line_width))

        right_border_line = QLineF(rect.x() + rect.width(),
                                   rect.y(),
                                   rect.x() + rect.width(),
                                   rect.y() + rect.height())
        self.painter.drawLine(right_border_line)

    def paint_above_borders(self, rect: QRectF):
        """Paint lower borders of all above cells

        :param rect: Cell rect of below cell, in which the borders are painted

        """

        for above_key in self.cell_nav.above_keys():
            above_cell_nav = GridCellNavigator(self.grid, above_key)
            merge_area = above_cell_nav.merge_area
            if merge_area is None:
                columns = [above_key[1]]
            else:
                _, left, _, right = merge_area
                columns = list(range(left, right + 1))
            above_rect_x = self.grid.columnViewportPosition(columns[0])
            above_rect_width = sum(self.grid.columnWidth(column)
                                   for column in columns)

            line_color = above_cell_nav.border_qcolor_bottom
            line_width = above_cell_nav.borderwidth_bottom * self.grid.zoom
            self.painter.setPen(QPen(QBrush(line_color), line_width))

            above_border_line = QLineF(above_rect_x,
                                       rect.y(),
                                       above_rect_x + above_rect_width,
                                       rect.y())
            self.painter.drawLine(above_border_line)

    def paint_left_borders(self, rect: QRectF):
        """Paint right borders of all left cells

        :param rect: Cell rect of right cell, in which the borders are painted

        """

        for left_key in self.cell_nav.left_keys():
            left_cell_nav = GridCellNavigator(self.grid, left_key)
            merge_area = left_cell_nav.merge_area
            if merge_area is None:
                rows = [left_key[0]]
            else:
                top, _, bottom, _ = merge_area
                rows = list(range(top, bottom + 1))
            left_rect_y = self.grid.rowViewportPosition(rows[0])
            left_rect_height = sum(self.grid.rowHeight(row) for row in rows)

            line_color = left_cell_nav.border_qcolor_right
            line_width = left_cell_nav.borderwidth_right
            self.painter.setPen(QPen(QBrush(line_color), line_width))

            above_border_line = QLineF(rect.x(),
                                       left_rect_y,
                                       rect.x(),
                                       left_rect_y + left_rect_height)
            self.painter.drawLine(above_border_line)

    def paint_borders(self, rect):
        """Paint cell borders"""

        self.paint_bottom_border(rect)
        self.paint_right_border(rect)
        self.paint_above_borders(rect)
        self.paint_left_borders(rect)

        # Above left edge
        # Above right edge
        # Below left edge
        # Below right edge

#        pen = QPen(Qt.black, self.grid.zoom, Qt.SolidLine, Qt.SquareCap,
#                   Qt.MiterJoin)
#        self.painter.setPen(pen)
#
#        self.painter.drawRect(rect)

    def paint_cursor(self, rect):
        """"""

    def paint(self):
        """Paints the cell"""

        rect = QRectF(self.option.rect)

        self.painter.setClipRect(self.option.rect)

        angle = self.cell_attributes[self.key].angle

        with painter_rotate(self.painter, rect, angle) as rrect:
            self.paint_content(rrect)

        self.paint_borders(rect)
        self.paint_cursor(rect)
