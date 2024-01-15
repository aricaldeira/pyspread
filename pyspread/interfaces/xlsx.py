#!/usr/bin/env python
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

This file contains interfaces to the xlsx file format.

XlsReader and XlsWriter classed are structured into the following sections:
 * shape
 * code
 * attributes
 * row_heights
 * col_widths
 * macros


**Provides**

 * :func:`wxcolor2rgb`
 * :dict:`wx2qt_fontweights`
 * :dict:`wx2qt_fontstyles`
 * :class:`XlsReader`
 * :class:`XlsWriter`

"""

# from builtins import str, map, object

import ast
from base64 import b64decode, b85encode
from collections import OrderedDict, defaultdict
from typing import Any, BinaryIO, Callable, Iterable, Tuple
from PyQt6.QtGui import QFont

try:
    import pycel
    from pycel import excelformula
except ImportError:
    pycel = None

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell

try:
    from pyspread.lib.attrdict import AttrDict
    from pyspread.lib.selection import Selection
    from pyspread.model.model import CellAttribute, CodeArray
except ImportError:
    from lib.attrdict import AttrDict
    from lib.selection import Selection
    from model.model import CellAttribute, CodeArray


BORDERWIDTH_XLSX2PYSU = {"hair": 0, "thin": 1, "medium": 4, "thick": 8}

# def wxcolor2rgb(wxcolor: int) -> Tuple[int, int, int]:
#     """Returns red, green, blue for given wxPython binary color value

#     :param wxcolor: Color value from wx.Color

#     """

#     red = wxcolor >> 16
#     green = wxcolor - (red << 16) >> 8
#     blue = wxcolor - (red << 16) - (green << 8)

#     return red, green, blue


# wx2qt_fontweights = {
#     90: 50,  # wx.FONTWEIGHT_NORMAL
#     91: 25,  # wx.FONTWEIGHT_LIGHT
#     92: 75,  # wx.FONTWEIGHT_BOLD
#     93: 87,  # wx.FONTWEIGHT_MAX
#     }

# wx2qt_fontstyles = {
#     90: 0,  # wx.FONTSTYLE_NORMAL
#     93: 1,  # wx.FONTSTYLE_ITALIC
#     94: 1,  # wx.FONTSTYLE_SLANT
#     95: 2,  # wx.FONTSTYLE_MAX
#     }


class XlsxReader:
    """Reads xlsx file from OpenPyXL into a code_array"""

    def __init__(self, xlsx_file: BinaryIO, code_array: CodeArray):
        """
        :param xlsx_file: The xlsx file to be read
        :param code_array: Target code_array

        """

        self.code_array = code_array
        self.wb = load_workbook(xlsx_file)

    def __iter__(self):
        """Iterates over self.xlsx_file, replacing everything in code_array"""

        sheet_attrs = defaultdict(list)

        for worksheet_name in self.wb.sheetnames:
            worksheet = self.wb[worksheet_name]
            # Row widths
            # Column widths
            table_idx = self.wb.sheetnames.index(worksheet_name)
            for row_idx, row in enumerate(worksheet.iter_rows()):
                for cell in row:
                    key = row_idx, cell.col_idx-1, table_idx

                    # Code
                    # ----

                    self._xlsx2code(key, cell)

                    # Cell attributes
                    # ---------------

                    self._xlsx2attributes(key, cell, sheet_attrs)


                    # print(cell.fill, cell.alignment, cell.border, cell.fill,
                    #       cell.font, cell.has_style, cell.hyperlink,
                    #       cell.is_date, cell.number_format, cell.protection)

                    yield key

            self.append_sheet_attributes(table_idx, sheet_attrs)
            sheet_attrs.clear()

    def append_sheet_attributes(self, table: int, sheet_attrs: dict):
        """Creates selections from attributes in  sheet_attrs and appends them

        :param table: Current table
        :param sheet_attrs: Dict mapping (attr_name, attr values) to key list

        """

        for sheet_attr in sheet_attrs:
            selection = Selection([], [], [], [], sheet_attrs[sheet_attr])
            attr_dict = AttrDict([sheet_attr])
            cell_attr = CellAttribute(selection, table, attr_dict)
            self.code_array.cell_attributes.append(cell_attr)

    @staticmethod
    def xlsx_rgba2rgb(rgb: str) -> (int, int, int):
        """Converts rgba string from xlsx to rgb tuple

        :param rgb: rgba string from xlsx

        """

        if rgb[:2] == "00":
            # Transparent cell
            raise ValueError("Color is transparent")

        r = int(rgb[2:4], 16)
        g = int(rgb[4:6], 16)
        b = int(rgb[6:8], 16)

        return r, g, b

    def _xlsx2code(self, key: (int, int, int),  cell: Cell):
        """Updates code in code_array

        :param key: Pyspread cell key
        :param cell: Cell object from openpyxl

        """

        if cell.data_type in ("n", "s") or pycel is None:
            code = repr(cell.value)
        elif cell.data_type == "f":
            # Convert formula via pycel
            ex = excelformula.ExcelFormula(cell.value)
            code = ex.python_code
        else:
            code = repr(cell.value)
            raise Warning(f"Excel data type {cell.data_type} unknown.")

        self.code_array.dict_grid[key] = code

    def _xlsx2attributes(self, key: (int, int, int), cell: Cell, sheet_attrs):
        """Updates attributes in code_array

        :param key: Pyspread cell key
        :param cell: Cell object from openpyxl
        :param sheet_attrs: Sheet attribute dict

        """

        skey = key[0], key[1]  # sheet key
        skey_above = key[0] - 1, key[1]
        skey_left = key[0], key[1] - 1

        # Cell background color
        try:
            bg_rgb = self.xlsx_rgba2rgb(cell.fill.bgColor.rgb)
            sheet_attrs[("bgcolor", bg_rgb)].append(skey)
        except ValueError:
            pass

        # Text color
        try:
            text_rgb = self.xlsx_rgba2rgb(cell.font.color.rgb)
            sheet_attrs[("textcolor", text_rgb)].append(skey)
        except (AttributeError, ValueError):
            pass


        # Text font
        try:
            sheet_attrs[("textfont", cell.font.name)].append(skey)
        except ValueError:
            pass

        # Text size
        try:
            sheet_attrs[("pointsize", cell.font.size)].append(skey)
        except ValueError:
            pass
        # Text weight
        try:
            if cell.font.bold:
                sheet_attrs[("fontweight", 75)].append(skey)
        except ValueError:
            pass
        # Text style
        try:
            if cell.font.italic:
                sheet_attrs[("fontstyle",
                             QFont.Style.StyleItalic)].append(skey)
        except ValueError:
            pass
        # Text underline
        try:
            if cell.font.underline:
                sheet_attrs[("underline", True)].append(skey)
        except ValueError:
            pass
        # Text strikethrough
        try:
            if cell.font.strike:
                sheet_attrs[("strikethrough", True)].append(skey)
        except ValueError:
            pass

        if cell.alignment.horizontal == "left":
            sheet_attrs[("justification",
                         "justify_left")].append(skey)
        elif cell.alignment.horizontal == "center":
            sheet_attrs[("justification",
                         "justify_center")].append(skey)
        elif cell.alignment.horizontal == "justify":
            sheet_attrs[("justification",
                         "justify_fill")].append(skey)
        elif cell.alignment.horizontal == "right":
            sheet_attrs[("justification",
                         "justify_right")].append(skey)

        if cell.alignment.vertical == "top":
            sheet_attrs[("vertical_align",
                         "align_top")].append(skey)
        elif cell.alignment.vertical == "center":
            sheet_attrs[("vertical_align",
                         "align_center")].append(skey)
        elif cell.alignment.vertical == "bottom":
            sheet_attrs[("vertical_align",
                         "align_bottom")].append(skey)

        if cell.border.bottom.style is not None:
            width = BORDERWIDTH_XLSX2PYSU[cell.border.bottom.style]
            sheet_attrs[("borderwidth_bottom", width)].append(skey)

        try:
            rgb = cell.border.bottom.color.rgb
            color = self.xlsx_rgba2rgb(rgb)
            sheet_attrs[("bordercolor_bottom", color)].append(skey)
        except AttributeError:
            if cell.border.bottom.style is not None and width is not None:
                color = 0, 0, 0
                sheet_attrs[("bordercolor_bottom", color)].append(skey)

        if cell.border.right.style is not None:
            width = BORDERWIDTH_XLSX2PYSU[cell.border.right.style]
            sheet_attrs[("borderwidth_right", width)].append(skey)

        try:
            rgb = cell.border.right.color.rgb
            color = self.xlsx_rgba2rgb(rgb)
            sheet_attrs[("bordercolor_right", color)].append(skey)
        except AttributeError:
            if cell.border.right.style is not None and width is not None:
                color = 0, 0, 0
                sheet_attrs[("bordercolor_right",
                             color)].append(skey)

        if cell.border.top.style is not None:
            width = BORDERWIDTH_XLSX2PYSU[cell.border.top.style]
            sheet_attrs[("borderwidth_bottom",
                         width)].append(skey_above)

        try:
            rgb = cell.border.top.color.rgb
            color = self.xlsx_rgba2rgb(rgb)
            sheet_attrs[("bordercolor_bottom",
                         color)].append(skey_above)
        except AttributeError:
            if cell.border.top.style is not None and width is not None:
                color = 0, 0, 0
                sheet_attrs[("bordercolor_bottom",
                             color)].append(skey_above)

        if cell.border.left.style is not None:
            width = BORDERWIDTH_XLSX2PYSU[cell.border.left.style]
            sheet_attrs[("borderwidth_right",
                         width)].append(skey_left)

        try:
            rgb = cell.border.left.color.rgb
            color = self.xlsx_rgba2rgb(rgb)
            sheet_attrs[("bordercolor_right",
                         color)].append(skey_left)
        except AttributeError:
            if cell.border.left.style is not None and width is not None:
                color = 0, 0, 0
                sheet_attrs[("bordercolor_right",
                             color)].append(skey_left)


    # def _attr_convert_1to2(self, key: str, value: Any) -> Tuple[str, Any]:
    #     """Converts key, value attribute pair from v1.0 to v2.0

    #     :param key: AttrDict key
    #     :param value: AttrDict value for key

    #     """

    #     color_attrs = ["bordercolor_bottom", "bordercolor_right", "bgcolor",
    #                    "textcolor"]
    #     if key in color_attrs:
    #         return key, wxcolor2rgb(value)

    #     elif key == "fontweight":
    #         return key, wx2qt_fontweights[value]

    #     elif key == "fontstyle":
    #         return key, wx2qt_fontstyles[value]

    #     elif key == "markup" and value:
    #         return "renderer", "markup"

    #     elif key == "angle" and value < 0:
    #         return "angle", 360 + value

    #     elif key == "merge_area":
    #         # Value in v1.0 None if the cell was merged
    #         # In v 2.0 this is no longer necessary
    #         return None, value

    #     # Update justifiaction and alignment values
    #     elif key in ["vertical_align", "justification"]:
    #         just_align_value_tansitions = {
    #                 "left": "justify_left",
    #                 "center": "justify_center",
    #                 "right": "justify_right",
    #                 "top": "align_top",
    #                 "middle": "align_center",
    #                 "bottom": "align_bottom",
    #         }
    #         return key, just_align_value_tansitions[value]

    #     return key, value

    # def _pys2attributes_10(self, line: str):
    #     """Updates attributes in code_array - for save file version 1.0

    #     :param line: Pys file line to be parsed

    #     """

    #     splitline = self._split_tidy(line)

    #     selection_data = list(map(ast.literal_eval, splitline[:5]))
    #     selection = Selection(*selection_data)

    #     tab = int(splitline[5])

    #     attr_dict = AttrDict()

    #     old_merged_cells = {}

    #     for col, ele in enumerate(splitline[6:]):
    #         if not (col % 2):
    #             # Odd entries are keys
    #             key = ast.literal_eval(ele)

    #         else:
    #             # Even cols are values
    #             value = ast.literal_eval(ele)

    #             # Convert old wx color values and merged cells
    #             key_, value_ = self._attr_convert_1to2(key, value)

    #             if key_ is None and value_ is not None:
    #                 # We have a merged cell
    #                 old_merged_cells[value_[:2]] = value_
    #             try:
    #                 attr_dict.pop("merge_area")
    #             except KeyError:
    #                 pass
    #             attr_dict[key_] = value_

    #     attr = CellAttribute(selection, tab, attr_dict)
    #     self.code_array.cell_attributes.append(attr)

    #     for key in old_merged_cells:
    #         selection = Selection([], [], [], [], [key])
    #         attr_dict = AttrDict([("merge_area", old_merged_cells[key])])
    #         attr = CellAttribute(selection, tab, attr_dict)
    #         self.code_array.cell_attributes.append(attr)
    #     old_merged_cells.clear()

    # @version_handler
    # def _pys2attributes(self, line: str):
    #     """Updates attributes in code_array

    #     :param line: Pys file line to be parsed

    #     """

    #     splitline = self._split_tidy(line)

    #     selection_data = list(map(ast.literal_eval, splitline[:5]))
    #     selection = Selection(*selection_data)

    #     tab = int(splitline[5])

    #     attr_dict = AttrDict()

    #     for col, ele in enumerate(splitline[6:]):
    #         if not (col % 2):
    #             # Odd entries are keys
    #             key = ast.literal_eval(ele)

    #         else:
    #             # Even cols are values
    #             value = ast.literal_eval(ele)
    #             attr_dict[key] = value

    #     if attr_dict:  # Ignore empty attribute settings
    #         attr = CellAttribute(selection, tab, attr_dict)
    #         self.code_array.cell_attributes.append(attr)

    # def _pys2row_heights(self, line: str):
    #     """Updates row_heights in code_array

    #     :param line: Pys file line to be parsed

    #     """

    #     # Split with maxsplit 3
    #     split_line = self._split_tidy(line)
    #     key = row, tab = self._get_key(*split_line[:2])
    #     height = float(split_line[2])

    #     shape = self.code_array.shape

    #     try:
    #         if row < shape[0] and tab < shape[2]:
    #             self.code_array.row_heights[key] = height

    #     except ValueError:
    #         pass

    # def _pys2col_widths(self, line: str):
    #     """Updates col_widths in code_array

    #     :param line: Pys file line to be parsed

    #     """

    #     # Split with maxsplit 3
    #     split_line = self._split_tidy(line)
    #     key = col, tab = self._get_key(*split_line[:2])
    #     width = float(split_line[2])

    #     shape = self.code_array.shape

    #     try:
    #         if col < shape[1] and tab < shape[2]:
    #             self.code_array.col_widths[key] = width

    #     except ValueError:
    #         pass

    # def _pys2macros(self, line: str):
    #     """Updates macros in code_array

    #     :param line: Pys file line to be parsed

    #     """

    #     self.code_array.macros += line

