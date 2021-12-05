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

**Unit tests for string_helpers.py**

"""

import pytest
from ..string_helpers import quote, wrap_text


param_test_quote = [
    (None, None),
    (1, 1),
    ("", ""),
    ("Test", "'Test'"),
    ("ü+", "'ü+'"),
    (u"ü+", "'ü+'"),
    (r"ü+", "'ü+'"),
    (b"Test", "b'Test'"),
    ("Test1\nTest2", "'Test1\\nTest2'"),
]


@pytest.mark.parametrize("code, res", param_test_quote)
def test_quote(code, res):
    """Unit test for quote"""

    assert quote(code) == res


param_test_wrap_text = [
    ("", 80, 2000, ""),
    ("."*81, 80, 2000, "."*80+"\n."),
    (r"."*81, 80, 2000, "."*80+"\n."),
    ("~"*81, 80, 2000, "~"*80+"\n~"),
    (u"\u2200"*81, 80, 2000, "\u2200"*80+"\n\u2200"),
    ("."*160, 80, 2000, "."*80+"\n"+"."*80),
    ("x"*160, 80, 2, "xx..."),
    ("."*10, 2, 2000, "\n".join([".."]*5)),
    (None, 2, 10, None)
]


@pytest.mark.parametrize("text, width, maxlen, res", param_test_wrap_text)
def test_wrap_text(text, width, maxlen, res):
    """Unit test for wrap_text"""

    assert wrap_text(text, width, maxlen) == res
