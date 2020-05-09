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

from PyQt5.QtCore import Qt, QModelIndex, QRectF
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QTableView


@contextmanager
def painter_save(painter: QPainter):
    """Saves and restores the painter during a context

    :param painter: Painter, for which the state is preserved

    """

    painter.save()
    yield
    painter.restore()


@contextmanager
def painter_rotate(painter: QPainter, rect: QRectF, angle: int = 0) -> QRectF:
    """Saves and restores the painter during a context

    :param painter: Painter, which is rotated
    :param rect: `Rect to be painted in
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


class CellBackgroundRenderer:
    """Renders a cell's background

    The background changes if the cell is selected

    """


class CellBorderRenderer:
    """Renders a cell's borders"""


class CellCursorRenderer:
    """Renders the current cell's cursor"""


class CellContentRenderer:
    """Renders a cell's content"""


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

    def __init__(self, grid: QTableView, painter: QPainter, rect: QRectF,
                 index: QModelIndex):
        self.grid = grid
        self.cell_attributes = grid.model.code_array.cell_attributes
        self.painter = painter
        self.rect = QRectF(rect)
        self.index = index
        self.key = index.row(), index.column(), self.grid.table

    def paint(self):
        """Paints the cell"""

        zoom = self.grid.zoom
        angle = self.cell_attributes[self.key].angle

        with painter_rotate(self.painter, self.rect, angle) as rect:
            self.painter.setClipRect(rect)

            pen = QPen(Qt.black, zoom, Qt.SolidLine, Qt.SquareCap,
                       Qt.MiterJoin)
            self.painter.setPen(pen)
            self.painter.drawRect(rect)
