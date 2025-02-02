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

Themes for pyspread

**Provides**

* :class:`ColorRoles`: Maps attribute names to theme color roles

"""


from PyQt6.QtGui import QPalette


class ColorRole:
    """Class attributes map cell_attributes to QPalette color roles"""

    text: int = QPalette.ColorRole.Text
    bg: int = QPalette.ColorRole.Base
    line: int = QPalette.ColorRole.PlaceholderText
    highlight: int = QPalette.ColorRole.Highlight
