# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Copyright Seongyong Park
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
parsers
======

Provides parsers to apply on expressions that are not pure Python expressions

Provides
--------

* spreadsheet_formula_to_code: Spreadsheet formula parser

"""

try:
    import pycel
    from pycel import excelformula
except ImportError:
    pycel = None


def spreadsheet_formula_to_code(formula: str) -> str:
    """ Converts spreadsheet formula into Python code via pycel """
    if pycel is None:
        return formula

    ex = excelformula.ExcelFormula(formula)
    return ex.python_code
