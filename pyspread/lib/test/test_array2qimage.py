# -*- coding: utf-8 -*-

from contextlib import contextmanager
from os.path import abspath, dirname, join
import numpy
import sys

import pytest

from PyQt5 import QtGui

from .compat import numBytes, numColors

PYSPREADPATH = abspath(join(dirname(__file__) + "/../.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)


with insert_path(PYSPREADPATH):
    try:
        import pyspread.lib.qimage2ndarray as qimage2ndarray
    except ImportError:
        import lib.qimage2ndarray as qimage2ndarray


def assert_equal(a, b):
    assert a == b


def test_rgb2qimage():
    a = numpy.zeros((240, 320, 3), dtype = float)
    a[12,10] = (42.42, 20, 14)
    a[13,10] = (-10, 0, -14)
    qImg = qimage2ndarray.array2qimage(a)
    assert not qImg.isNull()
    assert_equal(qImg.width(), 320)
    assert_equal(qImg.height(), 240)
    assert_equal(qImg.format(), QtGui.QImage.Format_RGB32)
    assert_equal(hex(qImg.pixel(10,12)), hex(QtGui.qRgb(42,20,14)))
    assert_equal(hex(qImg.pixel(10,13)), hex(QtGui.qRgb(0,0,0)))
    assert_equal(hex(qImg.pixel(10,14)), hex(QtGui.qRgb(0,0,0)))

def test_rgb2qimage_normalize():
    a = numpy.zeros((240, 320, 3), dtype = float)
    a[12,10] = (42.42, 20, 14)
    a[13,10] = (-10, 20, 0)
    qImg = qimage2ndarray.array2qimage(a, normalize = True)
    assert not qImg.isNull()
    assert_equal(qImg.width(), 320)
    assert_equal(qImg.height(), 240)
    assert_equal(qImg.format(), QtGui.QImage.Format_RGB32)
    assert_equal(hex(qImg.pixel(10,12)),
                 hex(QtGui.qRgb(255,int(255*30.0/52.42),int(255*24/52.42))))
    assert_equal(hex(qImg.pixel(10,13)),
                 hex(QtGui.qRgb(0,int(255*30.0/52.42),int(255*10/52.42))))
    x = int(255 * 10.0 / 52.42)
    assert_equal(hex(qImg.pixel(10,14)), hex(QtGui.qRgb(x,x,x)))       # zero pixel
