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

import numpy
import sys

from PyQt5.QtGui import QImage


if sys.byteorder == 'little':
    _bgra = (0, 1, 2, 3)
else:
    _bgra = (3, 2, 1, 0)


validFormats_8bit = [getattr(QImage, name)
                     for name in ('Format_Indexed8', 'Format_Grayscale8')
                     if name in dir(QImage)]


validFormats_32bit = (QImage.Format_RGB32,
                      QImage.Format_ARGB32,
                      QImage.Format_ARGB32_Premultiplied)


def PyQt_data(image):
    # PyQt4/PyQt5's QImage.bits() returns a sip.voidptr that supports
    # conversion to string via asstring(size) or getting its base
    # address via int(...):
    return (int(image.bits()), False)


def qimageview(image):
    if not isinstance(image, QImage):
        raise TypeError("image argument must be a QImage instance")

    shape = image.height(), image.width()
    strides0 = image.bytesPerLine()

    format = image.format()
    if format in validFormats_8bit:
        dtype = "|u1"
        strides1 = 1
    elif format in validFormats_32bit:
        dtype = "|u4"
        strides1 = 4
    elif format == QImage.Format_Invalid:
        raise ValueError("qimageview got invalid QImage")
    else:
        tpl = ("qimageview can only handle 8- or 32-bit QImages "
               "(format was {})")
        raise ValueError(tpl.formnat(format))

    image.__array_interface__ = {
        'shape': shape,
        'typestr': dtype,
        'data': PyQt_data(image),
        'strides': (strides0, strides1),
        'version': 3,
    }

    result = numpy.asarray(image)
    del image.__array_interface__
    return result


def _qimage_or_filename_view(qimage):
    if isinstance(qimage, str):
        qimage = QImage(qimage)
    return qimageview(qimage)


def byte_view(qimage, byteorder='little'):
    """Returns raw 3D view of the given QImage_'s memory.

    This will always be a 3-dimensional numpy.ndarray with dtype numpy.uint8.

    Note that for 32-bit images, the last dimension will be in the
    [B,G,R,A] order (if little endian) due to QImage_'s memory layout
    (the alpha channel will be present for Format_RGB32 images, too).

    For 8-bit (indexed) images, the array will still be 3-dimensional,
    i.e. shape will be (height, width, 1).

    The order of channels in the last axis depends on the `byteorder`,
    which defaults to 'little', i.e. BGRA order.  You may set the
    argument `byteorder` to 'big' to get ARGB, or use None which means
    sys.byteorder here, i.e. return native order for the machine the
    code is running on.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_
    :param byteorder: specify order of channels in last axis
    :rtype: numpy.ndarray_ with shape (height, width, 1 or 4) and dtype uint8

    """

    raw = _qimage_or_filename_view(qimage)
    result = raw.view(numpy.uint8).reshape(raw.shape + (-1, ))
    if byteorder and byteorder != sys.byteorder:
        result = result[..., ::-1]
    return result


def rgb_view(qimage, byteorder='big'):
    """Returns RGB view of a given 32-bit color QImage_'s memory.

    Similarly to byte_view(), the result is a 3D numpy.uint8 array,
    but reduced to the rgb dimensions (without alpha), and reordered
    (using negative strides in the last dimension) to have the usual
    [R,G,B] order.  The image must have 32 bit pixel size, i.e. be
    RGB32, ARGB32, or ARGB32_Premultiplied.  (Note that in the latter
    case, the values are of course premultiplied with alpha.)

    The order of channels in the last axis depends on the `byteorder`,
    which defaults to 'big', i.e. RGB order.  You may set the argument
    `byteorder` to 'little' to get BGR, or use None which means
    sys.byteorder here, i.e. return native order for the machine the
    code is running on.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_ with 32-bit pixel type
    :param byteorder: specify order of channels in last axis
    :rtype: numpy.ndarray_ with shape (height, width, 3) and dtype uint8

    """

    if byteorder is None:
        byteorder = sys.byteorder
    bytes = byte_view(qimage, byteorder)
    if bytes.shape[2] != 4:
        msg = ("For rgb_view, the image must have 32 bit pixel size "
               "(use RGB32, ARGB32, or ARGB32_Premultiplied)")
        raise ValueError(msg)

    if byteorder == 'little':
        return bytes[..., :3]  # strip A off BGRA
    else:
        return bytes[..., 1:]  # strip A off ARGB


def alpha_view(qimage):
    """Returns alpha view of a given 32-bit color QImage_'s memory.

    The result is a 2D numpy.uint8 array, equivalent to
    byte_view(qimage)[...,3].  The image must have 32 bit pixel size,
    i.e. be RGB32, ARGB32, or ARGB32_Premultiplied.  Note that it is
    not enforced that the given qimage has a format that actually
    *uses* the alpha channel -- for Format_RGB32, the alpha channel
    usually contains 255 everywhere.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_ with 32-bit pixel type
    :rtype: numpy.ndarray_ with shape (height, width) and dtype uint8

    """

    bytes = byte_view(qimage, byteorder=None)
    if bytes.shape[2] != 4:
        msg = ("For alpha_view, the image must have 32 bit pixel size "
               "(use RGB32, ARGB32, or ARGB32_Premultiplied)")
        raise ValueError(msg)
    return bytes[..., _bgra[3]]


def _normalize255(array, normalize, clip=(0, 255)):
    if normalize:
        if normalize is True:
            normalize = array.min(), array.max()
            if clip == (0, 255):
                clip = None
        elif numpy.isscalar(normalize):
            normalize = (0, normalize)

        nmin, nmax = normalize

        if nmin:
            array = array - nmin

        if nmax != nmin:
            scale = 255. / (nmax - nmin)
            if scale != 1.0:
                array = array * scale

    if clip:
        low, high = clip
        numpy.clip(array, low, high, array)

    return array


def array2qimage(array, normalize=False):
    """Convert a 2D or 3D numpy array into a 32-bit QImage_.

    The first dimension represents the vertical image axis; the optional
    third dimension is supposed to contain 1-4 channels:

    ========= ===================
    #channels interpretation
    ========= ===================
            1 scalar/gray
            2 scalar/gray + alpha
            3 RGB
            4 RGB + alpha
    ========= ===================

    Scalar data will be converted into corresponding gray RGB triples;
    if you want to convert to an (indexed) 8-bit image instead, use
    `gray2qimage` (which cannot support an alpha channel though).

    The parameter `normalize` can be used to normalize an image's
    value range to 0..255:

    `normalize` = (nmin, nmax):
      scale & clip image values from nmin..nmax to 0..255

    `normalize` = nmax:
      lets nmin default to zero, i.e. scale & clip the range 0..nmax
      to 0..255

    `normalize` = True:
      scale image values to 0..255 (same as passing (array.min(),
      array.max()))

    If `array` contains masked values, the corresponding pixels will
    be transparent in the result.  Thus, the result will be of
    QImage.Format_ARGB32 if the input already contains an alpha
    channel (i.e. has shape (H,W,4)) or if there are masked pixels,
    and QImage.Format_RGB32 otherwise.

    :param array: image data which should be converted (copied) into a QImage_
    :type array: 2D or 3D numpy.ndarray_ or `numpy.ma.array <masked arrays>`_
    :param normalize: normalization parameter (default: no value changing)
    :type normalize: bool, scalar, or pair
    :rtype: QImage_ with RGB32 or ARGB32 format

    """

    if numpy.ndim(array) == 2:
        array = array[..., None]
    elif numpy.ndim(array) != 3:
        tpl = ("array2qimage can only convert 2D or 3D arrays "
               "(got {} dimensions)")
        raise ValueError(tpl.format(numpy.ndim(array)))
    if array.shape[2] not in (1, 2, 3, 4):
        msg = ("array2qimage expects the last dimension to contain exactly "
               "one (scalar/gray), two (gray+alpha), three (R,G,B), or four "
               "(R,G,B,A) channels")
        raise ValueError(msg)

    h, w, channels = array.shape

    hasAlpha = numpy.ma.is_masked(array) or channels in (2, 4)
    fmt = QImage.Format_ARGB32 if hasAlpha else QImage.Format_RGB32

    result = QImage(w, h, fmt)

    array = _normalize255(array, normalize)

    if channels >= 3:
        rgb_view(result)[:] = array[..., :3]
    else:
        rgb_view(result)[:] = array[..., :1]  # scalar data

    alpha = alpha_view(result)

    if channels in (2, 4):
        alpha[:] = array[..., -1]
    else:
        alpha[:] = 255

    if numpy.ma.is_masked(array):
        alpha[:] *= numpy.logical_not(numpy.any(array.mask, axis=-1))

    return result
