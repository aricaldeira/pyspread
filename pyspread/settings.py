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

**Provides**

 * :class:`Settings`

"""


from os.path import abspath, dirname, join
from pathlib import Path
from platform import system
from typing import Any

from PyQt6.QtCore import QSettings, QLocale
from PyQt6.QtWidgets import QToolBar, QWidget

try:
    from pyspread.__init__ import VERSION, APP_NAME
except ImportError:
    from __init__ import VERSION, APP_NAME

PYSPREAD_DIRNAME = abspath(join(dirname(__file__), ".."))
PYSPREAD_PATH = Path(PYSPREAD_DIRNAME)
DOC_PATH = PYSPREAD_PATH / "pyspread/share/doc"
TUTORIAL_PATH = DOC_PATH / "tutorial"
MANUAL_PATH = DOC_PATH / "manual"
MPL_TEMPLATE_PATH = PYSPREAD_PATH / 'pyspread/share/templates/matplotlib'
RPY2_TEMPLATE_PATH = PYSPREAD_PATH / 'pyspread/share/templates/rpy2'
PLOT9_TEMPLATE_PATH = PYSPREAD_PATH / 'pyspread/share/templates/plotnine'
ICON_PATH = PYSPREAD_PATH / 'pyspread/share/icons'
ACTION_PATH = ICON_PATH / 'actions'
STATUS_PATH = ICON_PATH / 'status'
CHARTS_PATH = ICON_PATH / 'charts'
WEB_URL = "https://pyspread.gitlab.io"  # Official Web page


class Settings:
    """Contains all global application states."""

    # Note that `safe_mode` is not listed here but inside
    # :class:`model.model.DataArray`

    widget_names = ["main_window", "main_toolbar", "find_toolbar",
                    "format_toolbar", "macro_toolbar", "entry_line",
                    "entry_line_dock"]

    """Names of widgets with persistant states"""

    shape = 1000, 100, 3
    """Default shape of initial grid (rows, columns, tables)"""

    maxshape = 1000000, 100000, 100
    """Maximum shape of the grid"""

    changed_since_save = False
    """If `True` then File actions trigger a dialog"""

    last_file_input_path = Path.home()
    """Initial :class:`~pathlib.Path` for opening files"""

    last_file_output_path = Path.home()
    """Initial :class:`~pathlib.Path` for saving files"""

    last_file_import_path = Path.home()
    """Initial :class:`~pathlib.Path` for importing files"""

    last_file_export_path = Path.home()
    """Initial :class:`~pathlib.Path` for exporting files"""

    max_file_history = 5
    """Maximum number of files in file history"""

    file_history = []
    """Files in file history"""

    entry_line_font_family = "Iosevka Sezimal"
    """Font family for entry line widget"""

    macro_editor_font_family = "Iosevka Sezimal"
    """Font family for macro editor widget"""

    digest_types = None
    """List of default digest types for preprocessing values from CSV import"""

    highlighter_limit = 1000000
    """Maximum length of code, for which the netry line enables highlighting"""

    border_choice = "All borders"
    """The state of the border choice button"""

    timeout = 1000
    """Timeout for cell calculations in milliseconds"""

    refresh_timeout = 1000
    """Timeout for frozen cell updates in milliseconds"""

    signature_key = None
    """Key for signing save files"""

    font_sizes = (6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32)
    """Sizes"""

    default_row_height = 30
    default_column_width = 100

    zoom_levels = (0.4, 0.5, 0.6, 0.7, 0.8, 1.0,
                   1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0)

    print_zoom = None

    show_frozen = False
    """If `True` then frozen cell background is striped"""

    find_dialog_state = None
    """Find dialog state - needs to be stored when dialog is closed"""

    default_encoding = "utf-8"
    """Default encoding for exporting files (e.g. CSV)"""

    currency_iso_code = QLocale.system().currencySymbol(
        QLocale.CurrencySymbolFormat.CurrencyIsoCode)
    """Default currency for Money shortcut"""

    encodings = (
        "ascii", "big5", "big5hkscs", "cp037", "cp424", "cp437",
        "cp500", "cp720", "cp737", "cp775", "cp850", "cp852", "cp855", "cp856",
        "cp857", "cp858", "cp860", "cp861", "cp862", "cp863", "cp864", "cp865",
        "cp866", "cp869", "cp874", "cp875", "cp932", "cp949", "cp950",
        "cp1006", "cp1026", "cp1140", "cp1250", "cp1251", "cp1252", "cp1253",
        "cp1254", "cp1255", "cp1256", "cp1257", "cp1258", "euc-jp",
        "euc-jis-2004", "euc-jisx0213", "euc-kr", "gb2312", "gbk", "gb18030",
        "hz", "iso2022-jp", "iso2022-jp-1", "iso2022-jp-2", "iso2022-jp-2004",
        "iso2022-jp-3", "iso2022-jp-ext", "iso2022-kr", "latin-1", "iso8859-2",
        "iso8859-3", "iso8859-4", "iso8859-5", "iso8859-6", "iso8859-7",
        "iso8859-8", "iso8859-9", "iso8859-10", "iso8859-13", "iso8859-14",
        "iso8859-15", "iso8859-16", "johab", "koi8-r", "koi8-u",
        "mac-cyrillic", "mac-greek", "mac-iceland", "mac-latin2", "mac-roman",
        "mac-turkish", "ptcp154", "shift-jis", "shift-jis-2004",
        "shift-jisx0213", "utf-32", "utf-32-be", "utf-32-le", "utf-16",
        "utf-16-be", "utf-16-le", "utf-7", "utf-8", "utf-8-sig",
    )
    """Encodings for importing and exporting files (e.g. CSV or SVG)"""

    sniff_size = 65536
    """Number of bytes for csv sniffer
       sniff_size should be larger than 1st+2nd line
    """

    # Status bar cell result summation
    show_statusbar_sum = True

    def __init__(self, parent: QWidget, reset_settings: bool = False):
        """
        :param parent: Parent widget, normally main window
        :param reset_settings: Do not restore saved settings

        """

        super().__setattr__("parent", parent)
        super().__setattr__("reset_settings", reset_settings)

    def __setattr__(self, key: str, value: Any):
        """
        Overloads __setattr__ to ensure that only existing attributes are set

        :param key: Setting attribute key
        :param value: New setting value

        """

        if not hasattr(self, key):
            raise AttributeError(f"{self} has no attribute {key}.")
        super().__setattr__(key, value)

    def add_to_file_history(self, filename: Path):
        """Adds new file to history

        :param value: File name to be added to history

        """

        self.file_history = [f for f in self.file_history if f != filename]
        self.file_history.insert(0, filename)
        self.file_history = self.file_history[:self.max_file_history]

    def reset(self):
        """Reset to defaults"""

        cls_attrs = (attr for attr in dir(self)
                     if (not attr.startswith("__")
                         and attr not in ("reset", "parent", "save",
                                          "restore", "default_settings")))
        for cls_attr in cls_attrs:
            setattr(self, cls_attr, getattr(Settings, cls_attr))

    def save(self):
        """Saves application state to QSettings"""

        if system() == "Darwin":
            settings = QSettings(APP_NAME+".gitlab.io", APP_NAME)
        else:
            settings = QSettings(APP_NAME, APP_NAME)

        # Application state

        # Do not store the actual filename. Otherwise, after saving and closing
        # File -> Save would overwrite the last saved file.

        if self.last_file_input_path is not None:
            settings.setValue("last_file_input_path",
                              self.last_file_input_path)
        if self.last_file_import_path is not None:
            settings.setValue("last_file_import_path",
                              self.last_file_import_path)
        if self.last_file_export_path is not None:
            settings.setValue("last_file_export_path",
                              self.last_file_export_path)
        settings.setValue("max_file_history", self.max_file_history)
        settings.value("file_history", [], 'QStringList')
        if self.file_history:
            settings.setValue("file_history", self.file_history)
        settings.setValue("timeout", self.timeout)
        settings.setValue("refresh_timeout", self.refresh_timeout)
        settings.setValue("signature_key", self.signature_key)
        settings.setValue("show_statusbar_sum", self.show_statusbar_sum)

        # GUI state
        for widget_name in self.widget_names:

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)

            # geometry
            geometry_name = widget_name + '/geometry'
            try:
                settings.setValue(geometry_name, widget.saveGeometry())
            except AttributeError:
                pass

            # state
            widget_state_name = widget_name + '/windowState'
            try:
                settings.setValue(widget_state_name, widget.saveState())
            except AttributeError:
                pass

            if isinstance(widget, QToolBar):
                toolbar_visibility_name = widget_name + '/visibility'
                settings.value(toolbar_visibility_name, [], bool)
                settings.setValue(toolbar_visibility_name,
                                  [a.isVisible() for a in widget.actions()])

            if widget_name == "entry_line_dock":
                settings.setValue("entry_line_isvisible", widget.isVisible())

        settings.sync()

    def restore(self):
        """Restores application state from QSettings"""

        def qt_bool(value):
            """Converts Qt setting string for bool into Python bool"""
            if value == "true":
                return True
            else:
                return False

        if self.reset_settings:
            return

        if system() == "Darwin":
            settings = QSettings(APP_NAME+".gitlab.io", APP_NAME)
        else:
            settings = QSettings(APP_NAME, APP_NAME)

        def setting2attr(setting_name, attr=None, mapper=None):
            """Sets attr to mapper(<Setting from setting_name>)"""

            value = settings.value(setting_name)
            if value is None:
                return
            if attr is None:
                attr = setting_name
            if mapper is None:
                def mapper(x):
                    return x
            setattr(self, attr, mapper(value))

        # Application state

        setting2attr("last_file_input_path")
        setting2attr("last_file_import_path")
        setting2attr("last_file_export_path")
        setting2attr("max_file_history", mapper=int)
        setting2attr("file_history")
        setting2attr("timeout", mapper=int)
        setting2attr("refresh_timeout", mapper=int)
        setting2attr("signature_key")
        setting2attr("show_statusbar_sum", mapper=qt_bool)

        # GUI state

        for widget_name in self.widget_names:
            geometry_name = widget_name + '/geometry'
            widget_state_name = widget_name + '/windowState'

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)

            geometry = settings.value(geometry_name)
            if geometry:
                widget.restoreGeometry(geometry)
            widget_state = settings.value(widget_state_name)
            if widget_state:
                widget.restoreState(widget_state)

            if isinstance(widget, QToolBar):
                toolbar_visibility_name = widget_name + '/visibility'
                visibility = settings.value(toolbar_visibility_name)
                if visibility is not None:
                    for is_visible, action in zip(visibility,
                                                  widget.actions()):
                        action.setVisible(is_visible in ['true', True])
                manager_button = widget.widgetForAction(widget.actions()[-1])
                manager_button.menu().update_checked_states()

            if widget_name == "entry_line_dock" \
               and settings.value("entry_line_isvisible") is not None:
                visible = settings.value("entry_line_isvisible") in ['true',
                                                                     True]
                widget.setVisible(visible)
