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


from setuptools import setup, find_packages

from pyspread import VERSION

with open("README.md", "r", encoding='utf8') as readme_file:
    long_description = readme_file.read()

setup(
    name='pyspread',
    version=VERSION,
    author='Martin Manns',
    author_email='mmanns@gmx.net',
    description='Pyspread is a non-traditional spreadsheet application'
    ' that is based on and written in the programming language Python.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pyspread.gitlab.io",
    project_urls={
        "Bug Tracker": "https://gitlab.com/pyspread/pyspread/issues",
        "Documentation": "https://pyspread.gitlab.io/docs.html",
        "Source Code": "https://gitlab.com/pyspread/pyspread",
    },
    packages=find_packages(),
    entry_points={
        'console_scripts': {
            'pyspread = pyspread.pyspread:main'
        }
    },
    package_data={'pyspread': [
            'share/*',
            'share/*/*',
            'share/*/*/*',
            'share/*/*/*/*',
            'share/*/*/*/*/*',
        ]
    },
    data_files=[
        ('pyspread/share/applications',
         ['pyspread/share/applications/io.gitlab.pyspread.pyspread.desktop']),
    ],
    license='GPL v3 :: GNU General Public License',
    keywords=['spreadsheet', 'pyspread'],
    python_requires='>=3.6',
    install_requires=['numpy (>=1.1)',
                      'PyQt6 (>=6.4)',
                      'setuptools (>=40.0)',
                      'markdown2 (>=2.3)'],
    extras_require={
        'matplotlib': ['matplotlib (>=1.1.1)'],
        'pyenchant': ['pyenchant (>=1.1)'],
        'pip': ['pip (>=18)'],
        'python-dateutil': ['python-dateutil (>=2.7.0)'],
        'py-moneyed': ['py-moneyed (>=2.0)'],
        'rpy2': ['rpy2 (>=3.4)'],
        'plotnine': ['plotnine (>=0.8)'],
        'pycel': ['pycel (>=1.0b30)'],
        'openpyxl': ['openpyxl (>=3.0.7)'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Microsoft',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
        'Topic :: Scientific/Engineering',
    ],
)
