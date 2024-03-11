#!/bin/bash

xgettext -j -d pyspread -o locale/pyspread.pot *.py
xgettext -j -d pyspread -o locale/en/LC_MESSAGES/pyspread.po *.py
xgettext -j -d pyspread -o locale/bz/LC_MESSAGES/pyspread.po *.py
xgettext -j -d pyspread -o locale/pt/LC_MESSAGES/pyspread.po *.py
