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

 * :func: `painter_save`: Context manager saving and restoring painter state
 * :func: `painter_zoom`: Context manager scaling and restoring the painter
 * :func: `painter_rotate`: Context manager rotating and restoring the painter
 * :class:`GridCellNavigator`: Find neighbors of a cell
 * :class:`EdgeBorders`: Dataclass for edge properties
 * :class:`CellEdgeRenderer`: Paints cell edges
 * :class:`QColorCache`: QColor cache
 * :class:`CellRenderer`: Paints cells

"""

from contextlib import contextmanager
try:
    from dataclasses import dataclass
except ImportError:
    from pyspread.lib.dataclasses import dataclass  # Python 3.6 compatibility
from typing import List, Tuple

try:
    from pyspread.themes import ColorRole
except ImportError:
    from themes import ColorRole

from PyQt6.QtCore import Qt, QModelIndex, QRectF, QPointF
from PyQt6.QtGui import (QBrush, QPainter, QPalette, QPen,
                         QPainterPath, QPolygonF, QPainterPathStroker)

from PyQt6.QtGui import QColor as __QColor
from PyQt6.QtWidgets import QTableView, QStyleOptionViewItem
from functools import lru_cache


@contextmanager
def painter_save(painter: QPainter):
    """Context manager saving and restoring painter state

    :param painter: Painter, for which the state is preserved

    """

    painter.save()
    yield
    painter.restore()


@contextmanager
def painter_zoom(painter: QPainter, zoom: float, rect: QRectF) -> QRectF:
    """Context manager scaling and restoring the painter

    (rect.x(), rect.y()) is invariant

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
    """Context manager rotating and restoring the painter

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


class QColor(__QColor):
    """Hashable QColor"""

    def __hash__(self):
        return self.rgba()


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

        self.borderwidth_bottom_cache = grid.borderwidth_bottom_cache
        self.borderwidth_right_cache = grid.borderwidth_right_cache

    @property
    def borderwidth_bottom(self) -> float:
        """Width of bottom border line"""

        return self.borderwidth_bottom_cache[self.key]

    @property
    def borderwidth_right(self) -> float:
        """Width of right border line"""

        return self.borderwidth_right_cache[self.key]

    @property
    def border_color_bottom(self) -> QColor:
        """Color of bottom border line"""

        return self.code_array.cell_attributes[self.key].bordercolor_bottom

    @property
    def border_color_right(self) -> QColor:
        """Color of right border line"""

        return self.code_array.cell_attributes[self.key].bordercolor_right

    @property
    def merge_area(self) -> Tuple[int, int, int, int]:
        """Merge area of the key cell"""

        return self.code_array.cell_attributes[self.key].merge_area

    def merging_key(self, key: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Merging cell if cell is merged else cell key

        :param key: Key of cell that is checked for being merged

        """

        merging_key = self.code_array.cell_attributes.get_merging_cell(key)
        return key if merging_key is None else merging_key

    def above_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells above the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self.merging_key((self.row - 1, self.column, self.table))]
        _, left, _, right = merge_area
        return [self.merging_key((self.row - 1, col, self.table))
                for col in range(left, right + 1)]

    def below_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells below the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self.merging_key((self.row + 1, self.column, self.table))]
        _, left, _, right = merge_area
        return [self.merging_key((self.row + 1, col, self.table))
                for col in range(left, right + 1)]

    def left_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells left of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self.merging_key((self.row, self.column - 1, self.table))]
        top, _, bottom, _ = merge_area
        return [self.merging_key((row, self.column - 1, self.table))
                for row in range(top, bottom + 1)]

    def right_keys(self) -> List[Tuple[int, int, int]]:
        """Key list of neighboring cells right of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self.merging_key((self.row, self.column + 1, self.table))]
        top, _, bottom, _ = merge_area
        return [self.merging_key((row, self.column + 1, self.table))
                for row in range(top, bottom + 1)]

    def above_left_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell above left of the key cell"""

        return self.merging_key((self.row - 1, self.column - 1, self.table))

    def above_right_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell above right of the key cell"""

        return self.merging_key((self.row - 1, self.column + 1, self.table))

    def below_left_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell below left of the key cell"""

        return self.merging_key((self.row + 1, self.column - 1, self.table))

    def below_right_key(self) -> Tuple[int, int, int]:
        """Key of neighboring cell below right of the key cell"""

        return self.merging_key((self.row + 1, self.column + 1, self.table))


@dataclass
class EdgeBorders:
    """Holds border data for an edge and provides effective edge properties"""

    left_width: float
    right_width: float
    top_width: float
    bottom_width: float

    left_color: QColor
    right_color: QColor
    top_color: QColor
    bottom_color: QColor

    left_x: float
    right_x: float
    top_y: float
    bottom_y: float

    _color_cache = None

    @property
    def _border_widths(self) -> Tuple[float, float, float, float]:
        """Tuple of border widths in order left, right, top, bottom"""

        return (self.left_width, self.right_width,
                self.top_width, self.bottom_width)

    @property
    def _border_colors(self) -> Tuple[QColor, QColor, QColor, QColor]:
        """Tuple of border colors in order left, right, top, bottom"""

        return (self.left_color, self.right_color,
                self.top_color, self.bottom_color)

    @property
    def width(self) -> float:
        """Edge width, i.e. thickest vertical border"""

        return max(self.top_width, self.bottom_width)

    @property
    def height(self) -> float:
        """Edge height, i.e. thickest horizontal border"""

        return max(self.left_width, self.right_width)

    @property
    def color(self) -> QColor:
        """Edge color, i.e. darkest color of thickest edge border"""

        if self._color_cache is not None:
            return self._color_cache

        max_border_width = max(self.width, self.height)
        colors = []
        for width, color in zip(self._border_widths, self._border_colors):
            if width == max_border_width:
                colors.append(color)
        colors.sort(key=lambda color: color.lightnessF())
        color = colors[0]

        self._color_cache = color

        return color


class CellEdgeRenderer:
    """Paints cell edges"""

    intersection_cache = {}

    def __init__(self, painter: QPainter, center: QPointF,
                 borders: EdgeBorders, rect: QRectF, clip_path: QPainterPath,
                 zoom: float):
        """

        Borders are provided by EdgeBorders in order: left, right, top, bottom

        :param painter: Painter with which edge is drawn
        :param center: Edge center
        :param borders: Border widths and colors
        :param rect: Rect of the clip_path
        :param clip_path: Clip rectangle that is required for QtSVG clipping
        :param zoom: Current zoom level

        """

        self.painter = painter
        self.center = center
        self.borders = borders
        self.rect = rect
        self.clip_path = clip_path
        self.zoom = zoom

    def paint(self):
        """Paints the edge"""

        if not self.borders.width or not self.borders.height:
            return  # Invisible edge

        x, y = self.center.x(), self.center.y()
        width = self.borders.width * self.zoom
        height = self.borders.height * self.zoom

        cache_key = (self.rect.x(), self.rect.y(),
                     self.rect.width(), self.rect.height(),
                     x, y, width, height)

        color = self.borders.color
        self.painter.setPen(QPen(Qt.PenStyle.NoPen))
        self.painter.setBrush(QBrush(color))

        try:
            intersection = self.intersection_cache[cache_key]
        except KeyError:
            rect = QRectF(x-width/2, y-height/2, width, height)
            rect_path = QPainterPath()  # Required for clipping in SVG export
            rect_path.addRect(rect)

            intersection = self.clip_path.intersected(rect_path)

            self.intersection_cache[cache_key] = intersection

        self.painter.drawPath(intersection)
        self.painter.setPen(QPen(Qt.PenStyle.SolidLine))


class QColorCache(dict):
    """QColor cache that returns placeholder text color for None"""

    def __init__(self, grid, *args, **kwargs):
        self.grid = grid
        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        if key is None:
            qcolor = QColor(self.grid.palette().color(ColorRole.line))
        else:
            qcolor = QColor(*key)

        self[key] = qcolor

        return qcolor


class BorderWidthBottomCache(dict):
    """BorderWidthBottom cache"""

    def __init__(self, grid, *args, **kwargs):
        self.grid = grid
        self.cell_attributes = grid.model.code_array.cell_attributes

        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        borderwidth_bottom = self.cell_attributes[key].borderwidth_bottom
        self[key] = borderwidth_bottom

        return borderwidth_bottom


class BorderWidthRightCache(BorderWidthBottomCache):
    """BorderWidthRight cache"""

    def __missing__(self, key):
        borderwidth_right = self.cell_attributes[key].borderwidth_right
        self[key] = borderwidth_right

        return borderwidth_right


class EdgeBordersCache(dict):
    """Cache of all EdgeBorders objects"""

    def __missing__(self, key):
        self[key] = edge_border = EdgeBorders(*key)

        return edge_border


class BorderColorBottomCache(BorderWidthBottomCache):
    """BorderColorBottomCache cache"""

    def __missing__(self, key):
        border_color_bottom = self.cell_attributes[key].border_color_bottom
        self[key] = border_color_bottom

        return border_color_bottom


class BorderColorRightCache(BorderWidthBottomCache):
    """BorderColorBottomCache cache"""

    def __missing__(self, key):
        border_color_right = self.cell_attributes[key].border_color_right
        self[key] = border_color_right

        return border_color_right


class CellRenderer:
    """Paints cells

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

        self.painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering,
                                   True)
        self.painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,
                                   True)

        self.cell_attributes = grid.model.code_array.cell_attributes
        self.key = index.row(), index.column(), self.grid.table

        self.cell_nav = GridCellNavigator(grid, self.key)

        self.qcolor_cache = grid.qcolor_cache
        self.borderwidth_bottom_cache = grid.borderwidth_bottom_cache
        self.borderwidth_right_cache = grid.borderwidth_right_cache

    def inner_rect(self, rect: QRectF) -> QRectF:
        """Returns inner rect that is shrunk by border widths

        For merged cells, minimum top/left border widths are taken into account

        :param rect: Cell rect to be shrunk

        """

        above_keys = self.cell_nav.above_keys()
        left_keys = self.cell_nav.left_keys()

        width_top = min(self.borderwidth_bottom_cache[above_key]
                        for above_key in above_keys)
        width_left = min(self.borderwidth_right_cache[left_key]
                         for left_key in left_keys)
        width_bottom = self.cell_nav.borderwidth_bottom
        width_right = self.cell_nav.borderwidth_right

        width_top *= self.grid.zoom
        width_left *= self.grid.zoom
        width_bottom *= self.grid.zoom
        width_right *= self.grid.zoom

        rect_x = rect.x() + width_left / 2
        rect_y = rect.y() + width_top / 2
        rect_width = rect.width() - width_left / 2 - width_right / 2
        rect_height = rect.height() - width_top / 2 - width_bottom / 2

        return QRectF(rect_x, rect_y, rect_width, rect_height)

    def paint_content(self, rect: QRectF):
        """
        :param rect: Cell rect of the cell to be painted

        """

        with painter_zoom(self.painter, self.grid.zoom, rect) as zrect:
            self.grid.delegate.paint_(self.painter, zrect, self.option,
                                      self.index)

    @staticmethod
    @lru_cache(maxsize=65536)
    def _get_border_pen(width, zoom):
        """Gets zoomed border pen, white, fully transparent

        :param width: Unzoomed line width
        :param zoom: Current zoom level of grid

        """

        return QPen(QColor(255, 255, 255, 0), zoom*width,
                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap,
                    Qt.PenJoinStyle.MiterJoin)

    def _draw_line(self, point1: QPointF, point2: QPointF, width: float,
                   color: QColor, clip_path: QPainterPath):
        """Draws line

        Uses drawLine for screen painting and QPainterPathStroker for
        svg painting.

        :param point1: Start point of line
        :param point2: End point of line
        :param width: Line width
        :param color: Line color
        :param clip_path: Clip rectangle

        """

        zoom = self.grid.zoom
        alpha = max(0, round(255 - 255 * width * zoom))

        if width * zoom > 1.01:
            self.painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        screen_painting = self.grid.main_window.print_area is None

        if screen_painting:
            # Rendering for the screen
            pen = QPen(color)
            pen.setWidthF(width * zoom)
            self.painter.setPen(pen)
            self.painter.drawLine(point1, point2)
        else:
            # Rendering for the printer
            pen = self._get_border_pen(width, zoom)

            line_polygon = QPolygonF((point1, point2))
            line_path = QPainterPath()
            line_path.addPolygon(line_polygon)

            stroker = QPainterPathStroker(pen)
            stroked_path = stroker.createStroke(line_path)

            self.painter.setPen(QPen(QColor(255, 255, 255, alpha)))
            self.painter.setBrush(QBrush(color))
            self.painter.drawPath(clip_path.intersected(stroked_path))

        self.painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def paint_bottom_border(self, rect: QRectF, clip_path: QPainterPath):
        """Paint bottom border of cell

        :param rect: Cell rect of the cell to be painted
        :param clip_path: Clip rectangle that is required for QtSVG clipping

        """

        if not self.cell_nav.borderwidth_bottom:
            return

        point1 = QPointF(rect.x(), rect.y() + rect.height())
        point2 = QPointF(rect.x() + rect.width(), rect.y() + rect.height())

        width = self.cell_nav.borderwidth_bottom
        color = self.qcolor_cache[self.cell_nav.border_color_bottom]

        self._draw_line(point1, point2, width, color, clip_path)

    def paint_right_border(self, rect: QRectF, clip_path: QPainterPath):
        """Paint right border of cell

        :param rect: Cell rect of the cell to be painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

        """

        if not self.cell_nav.borderwidth_right:
            return

        point1 = QPointF(rect.x() + rect.width(), rect.y())
        point2 = QPointF(rect.x() + rect.width(), rect.y() + rect.height())

        width = self.cell_nav.borderwidth_right
        color = self.qcolor_cache[self.cell_nav.border_color_right]

        self._draw_line(point1, point2, width, color, clip_path)

    def paint_above_borders(self, rect: QRectF, clip_path: QPainterPath):
        """Paint lower borders of all above cells

        :param rect: Cell rect of below cell, in which the borders are painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

        """

        for above_key in self.cell_nav.above_keys():
            above_cell_nav = GridCellNavigator(self.grid, above_key)
            if not above_cell_nav.borderwidth_bottom:
                continue

            merge_area = above_cell_nav.merge_area
            if merge_area is None:
                columns = [above_key[1]]
            else:
                _, left, _, right = merge_area
                columns = list(range(left, right + 1))
            above_rect_x = self.grid.columnViewportPosition(columns[0])
            above_rect_width = sum(self.grid.columnWidth(column)
                                   for column in columns)

            point1 = QPointF(above_rect_x, rect.y())
            point2 = QPointF(above_rect_x + above_rect_width, rect.y())

            width = above_cell_nav.borderwidth_bottom
            color = self.qcolor_cache[above_cell_nav.border_color_bottom]

            self._draw_line(point1, point2, width, color, clip_path)

    def paint_left_borders(self, rect: QRectF, clip_path: QPainterPath):
        """Paint right borders of all left cells

        :param rect: Cell rect of right cell, in which the borders are painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

        """

        for left_key in self.cell_nav.left_keys():
            left_cell_nav = GridCellNavigator(self.grid, left_key)
            if not left_cell_nav.borderwidth_right:
                continue

            merge_area = left_cell_nav.merge_area
            if merge_area is None:
                rows = [left_key[0]]
            else:
                top, _, bottom, _ = merge_area
                rows = list(range(top, bottom + 1))
            left_rect_y = self.grid.rowViewportPosition(rows[0])
            left_rect_height = sum(self.grid.rowHeight(row) for row in rows)

            point1 = QPointF(rect.x(), left_rect_y)
            point2 = QPointF(rect.x(), left_rect_y + left_rect_height)

            width = left_cell_nav.borderwidth_right
            color = self.qcolor_cache[left_cell_nav.border_color_right]

            self._draw_line(point1, point2, width, color, clip_path)

    def paint_top_left_edge(self, rect: QRectF, clip_path: QPainterPath):
        """Paints top left edge of the cell

        :param rect: Cell rect of cell, for which the edge is painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

                  top
               TL  |  T
        left ------------ right
               L   |  C
                 bottom

        """

        center = QPointF(rect.x(), rect.y())

        top_left_key = self.cell_nav.above_left_key()
        left_key = self.cell_nav.left_keys()[0]
        top_key = self.cell_nav.above_keys()[0]

        top_left_cell_nav = GridCellNavigator(self.grid, top_left_key)
        left_cell_nav = GridCellNavigator(self.grid, left_key)
        top_cell_nav = GridCellNavigator(self.grid, top_key)

        left_width = top_left_cell_nav.borderwidth_bottom
        right_width = top_cell_nav.borderwidth_bottom
        top_width = top_left_cell_nav.borderwidth_right
        bottom_width = left_cell_nav.borderwidth_right

        left_color = self.qcolor_cache[top_left_cell_nav.border_color_bottom]
        right_color = self.qcolor_cache[top_cell_nav.border_color_bottom]
        top_color = self.qcolor_cache[top_left_cell_nav.border_color_right]
        bottom_color = self.qcolor_cache[left_cell_nav.border_color_right]

        left_x = rect.x() - rect.width()
        right_x = rect.x()
        top_y = rect.y() - rect.height()
        bottom_y = rect.y()

        key = (left_width, right_width, top_width, bottom_width,
               left_color, right_color, top_color, bottom_color,
               left_x, right_x, top_y, bottom_y)

        borders = self.grid.edge_borders_cache[key]

        renderer = CellEdgeRenderer(self.painter, center, borders, rect,
                                    clip_path, self.grid.zoom)
        renderer.paint()

    def paint_top_right_edge(self, rect: QRectF, clip_path: QPainterPath):
        """Paints top right edge of the cell

        :param rect: Cell rect of cell, for which the edge is painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

                  top
                T  |  TR
        left ------------ right
                C  |  R
                 bottom

        """

        center = QPointF(rect.x() + rect.width(), rect.y())

        top_key = self.cell_nav.above_keys()[-1]
        top_right_key = self.cell_nav.above_right_key()

        top_cell_nav = GridCellNavigator(self.grid, top_key)
        top_right_cell_nav = GridCellNavigator(self.grid, top_right_key)

        left_width = top_cell_nav.borderwidth_bottom
        right_width = top_right_cell_nav.borderwidth_bottom
        top_width = top_cell_nav.borderwidth_right
        bottom_width = self.cell_nav.borderwidth_right

        left_color = self.qcolor_cache[top_cell_nav.border_color_bottom]
        right_color = self.qcolor_cache[top_right_cell_nav.border_color_bottom]
        top_color = self.qcolor_cache[top_cell_nav.border_color_right]
        bottom_color = self.qcolor_cache[self.cell_nav.border_color_right]

        left_x = rect.x() + rect.width()
        right_x = rect.x() + 2 * rect.width()
        top_y = rect.y() - rect.height()
        bottom_y = rect.y()

        key = (left_width, right_width, top_width, bottom_width,
               left_color, right_color, top_color, bottom_color,
               left_x, right_x, top_y, bottom_y)

        borders = self.grid.edge_borders_cache[key]

        renderer = CellEdgeRenderer(self.painter, center, borders, rect,
                                    clip_path, self.grid.zoom)
        renderer.paint()

    def paint_bottom_left_edge(self, rect: QRectF, clip_path: QPainterPath):
        """Paints bottom left edge of the cell

        :param rect: Cell rect of cell, for which the edge is painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

                  top
               L   |  C
        left ------------ right
               BL  |  B
                 bottom

        """

        center = QPointF(rect.x(), rect.y() + rect.height())

        left_key = self.cell_nav.left_keys()[-1]
        bottom_left_key = self.cell_nav.below_left_key()

        left_cell_nav = GridCellNavigator(self.grid, left_key)
        bottom_left_cell_nav = GridCellNavigator(self.grid, bottom_left_key)

        left_width = left_cell_nav.borderwidth_bottom
        right_width = self.cell_nav.borderwidth_bottom
        top_width = left_cell_nav.borderwidth_right
        bottom_width = bottom_left_cell_nav.borderwidth_right

        left_color = self.qcolor_cache[left_cell_nav.border_color_bottom]
        right_color = self.qcolor_cache[self.cell_nav.border_color_bottom]
        top_color = self.qcolor_cache[left_cell_nav.border_color_right]
        bottom_color = \
            self.qcolor_cache[bottom_left_cell_nav.border_color_right]

        left_x = rect.x() - rect.width()
        right_x = rect.x()
        top_y = rect.y() + rect.height()
        bottom_y = rect.y() + 2 * rect.height()

        key = (left_width, right_width, top_width, bottom_width,
               left_color, right_color, top_color, bottom_color,
               left_x, right_x, top_y, bottom_y)

        borders = self.grid.edge_borders_cache[key]

        renderer = CellEdgeRenderer(self.painter, center, borders, rect,
                                    clip_path, self.grid.zoom)
        renderer.paint()

    def paint_bottom_right_edge(self, rect: QRectF, clip_path: QPainterPath):
        """Paints bottom right edge of the cell

        :param rect: Cell rect of cell, for which the edge is painted
        :param clip_path: Clip rectangle that is requuired for QtSVG clipping

                 top
               C  |  R
        left ----------- right
               B  |  BR
                bottom

        """

        center = QPointF(rect.x() + rect.width(), rect.y() + rect.height())

        right_key = self.cell_nav.right_keys()[-1]
        bottom_key = self.cell_nav.below_keys()[-1]

        right_cell_nav = GridCellNavigator(self.grid, right_key)
        bottom_cell_nav = GridCellNavigator(self.grid, bottom_key)

        left_width = self.cell_nav.borderwidth_bottom
        right_width = right_cell_nav.borderwidth_bottom
        top_width = self.cell_nav.borderwidth_right
        bottom_width = bottom_cell_nav.borderwidth_right

        left_color = self.qcolor_cache[self.cell_nav.border_color_bottom]
        right_color = self.qcolor_cache[right_cell_nav.border_color_bottom]
        top_color = self.qcolor_cache[self.cell_nav.border_color_right]
        bottom_color = self.qcolor_cache[bottom_cell_nav.border_color_right]

        left_x = rect.x() + rect.width()
        right_x = rect.x() + 2 * rect.width()
        top_y = rect.y() + rect.height()
        bottom_y = rect.y() + 2 * rect.height()

        key = (left_width, right_width, top_width, bottom_width,
               left_color, right_color, top_color, bottom_color,
               left_x, right_x, top_y, bottom_y)

        borders = self.grid.edge_borders_cache[key]

        renderer = CellEdgeRenderer(self.painter, center, borders, rect,
                                    clip_path, self.grid.zoom)
        renderer.paint()

    def paint_borders(self, rect):
        """Paint cell borders"""

        clip_path = QPainterPath()  # Required for clipping in SVG export
        clip_path.addRect(rect)

        self.painter.save()

        self.paint_bottom_border(rect, clip_path)
        self.paint_right_border(rect, clip_path)
        self.paint_above_borders(rect, clip_path)
        self.paint_left_borders(rect, clip_path)

        self.paint_top_left_edge(rect, clip_path)
        self.paint_top_right_edge(rect, clip_path)
        self.paint_bottom_left_edge(rect, clip_path)
        self.paint_bottom_right_edge(rect, clip_path)

        self.painter.restore()

    def paint(self):
        """Paints the cell"""

        rect = QRectF(self.option.rect)

        with painter_save(self.painter):
            self.painter.setClipRect(self.option.rect)

            angle = self.cell_attributes[self.key].angle
            inner_rect = self.inner_rect(rect)

            with painter_rotate(self.painter, inner_rect, angle) as rrect:
                self.paint_content(rrect)

            self.paint_borders(rect)
