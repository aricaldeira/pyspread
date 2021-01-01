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
test_cli
========

Unit tests for cli.py

"""

from argparse import Namespace
from contextlib import contextmanager
from os.path import abspath, dirname, join
import sys
from unittest.mock import patch
from pathlib import PosixPath

import pytest

PYSPREADPATH = abspath(join(dirname(__file__) + "/.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)


with insert_path(PYSPREADPATH):
    from ..cli import PyspreadArgumentParser

param_test_cli = [
    (['pyspread'],
     Namespace(file=None, default_settings=False)),
    (['pyspread', 'test.pys'],
     Namespace(file=PosixPath("test.pys"), default_settings=False)),
    (['pyspread', '--help'],
     None),
    (['pyspread', '--version'],
     None),
    (['pyspread', '--default-settings'],
     Namespace(file=None, default_settings=True)),
]


@pytest.mark.parametrize("argv, res", param_test_cli)
def test_cli(argv, res):
    with patch('argparse._sys.argv', argv):
        parser = PyspreadArgumentParser()
        if res is None:
            with pytest.raises(SystemExit) as exc:
                args, unknown = parser.parse_known_args()
            assert exc.value.code == 0
        else:
            args, unknown = parser.parse_known_args()
            assert args == res
