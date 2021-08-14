# -*- coding: utf-8 -*-

"""

The functions in this file are extracted from the project qimage2ndarray
https://github.com/hmeine/qimage2ndarray
that has been publisched under the BSD-3-Clause License.


Copyright (c) 2009, Hans Meine <hans_meine@gmx.net>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from contextlib import contextmanager
from os.path import abspath, dirname, join
import numpy
import sys

import pytest

from PyQt5 import QtGui

from .compat import setNumColors, numBytes

PYSPREADPATH = abspath(join(dirname(__file__) + "/../.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)


with insert_path(PYSPREADPATH):
    try:
        from pyspread.lib.qimage2ndarray import qimageview as _qimageview
    except ImportError:
        from lib.qimage2ndarray import qimageview as _qimageview


def assert_equal(a, b):
    assert a == b


def test_viewcreation():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_RGB32)
    v = _qimageview(qimg)
    assert_equal(v.shape, (240, 320))
    assert v.base is not None
    del qimg
    if hasattr(v.base, 'width'):
        w, h = v.base.width(), v.base.height()  # should not segfault
        assert_equal((w, h), (320, 240))
    v[239] = numpy.arange(320)  # should not segfault


def test_qimageview_noargs():
    with pytest.raises(TypeError):
        _qimageview()


def test_qimageview_manyargs():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_Indexed8)
    with pytest.raises(TypeError):
        _qimageview(qimg, 1)


def test_qimageview_wrongarg():
    with pytest.raises(TypeError):
        _qimageview(42)


def test_data_access():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_Indexed8)
    setNumColors(qimg, 256)
    qimg.fill(42)
    v = _qimageview(qimg)
    assert_equal(v.shape, (240, 320))
    assert_equal(v[10, 10], 42)
    assert_equal(v.nbytes, numBytes(qimg))


def test_being_view():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_Indexed8)
    setNumColors(qimg, 256)
    qimg.fill(23)
    v = _qimageview(qimg)
    qimg.fill(42)
    assert_equal(v.shape, (240, 320))
    assert_equal(v[10, 10], 42)
    assert_equal(v.nbytes, numBytes(qimg))


def test_coordinate_access():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_Indexed8)
    setNumColors(qimg, 256)
    qimg.fill(0)
    v = _qimageview(qimg)
    qimg.fill(23)
    qimg.setPixel(12, 10, 42)
    assert_equal(v.shape, (240, 320))
    assert_equal(v[10, 10], 23)
    assert_equal(v[10, 12], 42)
    assert_equal(v.nbytes, numBytes(qimg))


def test_odd_size_8bit():
    qimg = QtGui.QImage(321, 240, QtGui.QImage.Format_Indexed8)
    setNumColors(qimg, 256)
    qimg.fill(0)
    v = _qimageview(qimg)
    qimg.setPixel(12, 10, 42)
    assert_equal(v.shape, (240, 321))
    assert_equal(v[10, 12], 42)
    assert_equal(v.strides[0], qimg.bytesPerLine())


def test_odd_size_32bit():
    qimg = QtGui.QImage(321, 240, QtGui.QImage.Format_ARGB32)
    qimg.fill(0)
    v = _qimageview(qimg)
    qimg.setPixel(12, 10, 42)
    assert_equal(v.shape, (240, 321))
    assert_equal(v[10, 12], 42)
    assert_equal(v.strides[0], qimg.bytesPerLine())


def test_odd_size_32bit_rgb():
    qimg = QtGui.QImage(321, 240, QtGui.QImage.Format_RGB32)
    qimg.fill(0)
    v = _qimageview(qimg)
    qimg.setPixel(12, 10, 42)
    assert_equal(v.shape, (240, 321))
    assert_equal(v[10, 12], 42 | 0xff000000)
    assert_equal(v.strides[0], qimg.bytesPerLine())
    assert_equal(v.strides[1], 4)


def test_mono():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_Mono)
    with pytest.raises(ValueError):
        _qimageview(qimg)


def test_rgb666():
    qimg = QtGui.QImage(320, 240, QtGui.QImage.Format_RGB666)
    with pytest.raises(ValueError):
        _qimageview(qimg)
