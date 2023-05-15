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

 * :class:`MultiStateBitmapButton`
 * :class:`RotationButton`
 * :class:`JustificationButton`
 * :class:`RendererButton`
 * :class:`AlignmentButton`
 * :class:`ColorButton`
 * :class:`TextColorButton`
 * :class:`LineColorButton`
 * :class:`BackgroundColorButton`
 * :class:`MenuComboBox`
 * :class:`TypeMenuComboBox`
 * :class:`FontChoiceCombo`
 * :class:`FontSizeCombo`
 * :class:`Widgets`
 * :class:`FindEditor`
 * :class:`CellButton`
 * :class:`HelpBrowser`

"""

from pathlib import Path
from typing import Tuple

try:
    from markdown2 import markdown
except ImportError:
    markdown = None

from PyQt6.QtCore import pyqtSignal, QSize, Qt, QModelIndex, QPoint
from PyQt6.QtWidgets \
    import (QToolButton, QColorDialog, QFontComboBox, QComboBox, QSizePolicy,
            QLineEdit, QPushButton, QTextBrowser, QWidget, QMainWindow,
            QMenu, QTableView)
from PyQt6.QtGui import (QPalette, QColor, QFont, QIntValidator, QCursor,
                         QIcon, QAction)

try:
    from pyspread.actions import Action
    from pyspread.icons import Icon
    from pyspread.lib.csv import typehandlers, currencies
except ImportError:
    from actions import Action
    from icons import Icon
    from lib.csv import typehandlers, currencies


class MultiStateBitmapButton(QToolButton):
    """QToolButton that cycles through arbitrary states

    The states are defined by an iterable of QIcons

    """

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__()
        self.main_window = main_window

        self._current_action_idx = 0

        self.clicked.connect(self.on_clicked)

    @property
    def current_action_idx(self) -> int:
        """Index of current action"""

        return self._current_action_idx

    @current_action_idx.setter
    def current_action_idx(self, index: int):
        """Sets current action index and updates button and menu

        :param index: Index of action to be set

        """

        self._current_action_idx = index
        action = self.get_action(index)
        self.setIcon(action.icon())

    def get_action(self, index: int) -> QAction:
        """Returns action from index in action_names

        :param index: Index of action to be returned

        """

        action_name = self.action_names[index]
        return self.main_window.main_window_actions[action_name]

    def set_current_action(self, action_name: str):
        """Sets current action

        :param action_name: Name of action as in MainWindowActions

        """

        self.current_action_idx = self.action_names.index(action_name)

    def next(self) -> QAction:
        """Advances current_action_idx and returns current action"""

        if self.current_action_idx >= len(self.action_names) - 1:
            self.current_action_idx = 0
        else:
            self.current_action_idx += 1

        return self.get_action(self.current_action_idx)

    def set_menu_checked(self, action_name: str):
        """Sets checked status of menu

        :param action_name: Name of action as in MainWindowActions

        """

        action = self.main_window.main_window_actions[action_name]
        action.setChecked(True)

    def on_clicked(self):
        """Button clicked event handler. Chechs corresponding menu item"""

        action = self.next()
        action.trigger()
        action.setChecked(True)


class RotationButton(MultiStateBitmapButton):
    """Rotation button for the format toolbar"""

    label = "Rotate"
    action_names = "rotate_0", "rotate_90", "rotate_180", "rotate_270"

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.setStatusTip("Text rotation")
        self.setToolTip("Text rotation")

    def icon(self) -> QIcon:
        """Returns icon for button identification"""

        return Icon.rotate_0


class JustificationButton(MultiStateBitmapButton):
    """Justification button for the format toolbar"""

    label = "Justification"
    action_names = ("justify_left", "justify_center", "justify_right",
                    "justify_fill")

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.setStatusTip("Text justification")
        self.setToolTip("Text justification")

    def icon(self) -> QIcon:
        """Returns icon for button identification"""

        return Icon.justify_left


class RendererButton(MultiStateBitmapButton):
    """Cell render button for the format toolbar"""

    label = "Renderer"
    action_names = "text", "markup", "image", "matplotlib"

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.setStatusTip("Cell render type")
        self.setToolTip("Cell render type")

    def icon(self) -> QIcon:
        """Returns icon for button identification"""

        return Icon.text


class AlignmentButton(MultiStateBitmapButton):
    """Alignment button for the format toolbar"""

    label = "Alignment"
    action_names = "align_top", "align_center", "align_bottom"

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.setStatusTip("Text alignment")
        self.setToolTip("Text alignment")

    def icon(self) -> QIcon:
        """Returns icon for button identification"""

        return Icon.align_top


class ColorButton(QToolButton):
    """Color button widget"""

    colorChanged = pyqtSignal()
    title = "Select Color"
    default_color = None
    _color = None

    def __init__(self, color: QColor, icon: QIcon = None,
                 max_size: QSize = QSize(28, 28)):
        """
        :param color: Color that is initially set
        :param icon: Button foreground image
        :param max_size: Maximum Size of the button

        """

        super().__init__()

        self.set_max_size(max_size)

        if icon is not None:
            self.setIcon(icon)

        self.color = color

        self.pressed.connect(self.on_pressed)

    @property
    def color(self) -> QColor:
        """Chosen color"""

        return self._color

    @color.setter
    def color(self, color: QColor):
        """Color setter that adjusts internal state and button background

        :param color: Color to be set

        """

        if self._color == color:
            return

        self._color = color

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Button, color)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

    def set_max_size(self, size: QSize):
        """Set the maximum size of the widget

        :param color: Maximum button size

        """

        self.setMaximumWidth(size.width())
        self.setMaximumHeight(size.height())

    def on_pressed(self):
        """Button pressed event handler

        Shows color dialog and sets the chosen color.

        """

        dlg = QColorDialog(self.parent())

        dlg.setCurrentColor(self.color)
        if self.default_color is not None:
            dlg.setCustomColor(15, self.default_color)
        dlg.setWindowTitle(self.title)

        dlg.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setOptions(QColorDialog.ColorDialogOption.DontUseNativeDialog)

        pos = self.mapFromGlobal(QCursor.pos())
        pos.setX(pos.x() + int(self.rect().width() / 2))
        pos.setY(pos.y() + int(self.rect().height() / 2))
        dlg.move(self.mapToGlobal(pos))

        if dlg.exec():
            self.color = dlg.currentColor()
            self.colorChanged.emit()


class TextColorButton(ColorButton):
    """Color button with text icon"""

    label = "Text Color"

    def __init__(self, color: QColor):
        """
        :param color: Color that is initially set

        """

        icon = Icon.text_color
        super().__init__(color, icon=icon)

        self.title = "Select text color"
        self.setStatusTip("Text color")
        self.setToolTip("Text color")

        self.default_color = self.palette().color(QPalette.ColorRole.Text)


class LineColorButton(ColorButton):
    """Color button with text icon"""

    label = "Line Color"

    def __init__(self, color: QColor):
        """
        :param color: Color that is initially set

        """

        icon = Icon.line_color
        super().__init__(color, icon=icon)

        self.title = "Select cell border line color"
        self.setStatusTip("Cell border line color")
        self.setToolTip("Cell border line color")

        self.default_color = self.palette().color(QPalette.ColorRole.Mid)


class BackgroundColorButton(ColorButton):
    """Color button with text icon"""

    label = "Background Color"

    def __init__(self, color: QColor):
        """
        :param color: Color that is initially set

        """

        icon = Icon.background_color
        super().__init__(color, icon=icon)

        self.title = "Select cell background color"
        self.setStatusTip("Cell background color")
        self.setToolTip("Cell background color")

        self.default_color = self.palette().color(QPalette.ColorRole.Base)


class MenuComboBox(QComboBox):
    """ComboBox that uses a menu instead of a list"""

    text_tpl = "{} ({})"  # Template for ComboBox item text

    def __init__(self, items: dict):
        """

        :param items: Menu items

        The dict items needs to be given in the following format:
        {
            "<label_1>": None,  # For leaf item
            "<label_2>": {"<label_2.1>": None},  # For submenu
         }

        """

        super().__init__()

        self.action2index = {}  # Maps menu action to ComboBox item index

        self.menu = QMenu(self)
        self.menu.triggered.connect(self.on_menu_selected)

        self._fill(items, self.menu)

    def _fill(self, items: dict, menu: QMenu, parent_item_text: str = ""):
        """Fills the menu and the combobox

        :param items: Menu items for respective (sub)menu
        :param items: Menu or submenu
        :param parent_item_text: Text of parent item in submenu

        """

        for item in items:
            if parent_item_text:
                text = self.text_tpl.format(parent_item_text, item)
            else:
                text = item

            if items[item] is None:
                # Leaf item
                action = menu.addAction(item)
                self.addItem(text)
                self.action2index[action] = self.count() - 1

            else:
                # Submenu
                submenu = self.menu.addMenu(item)
                self._fill(items[item], submenu, parent_item_text=text)

    def showPopup(self):
        """Show combo menu"""

        rect = self.rect()

        pos = QPoint(rect.x(), rect.y()+rect.height())
        self.menu.popup(self.mapToGlobal(pos))

    def hidePopup(self):
        """Hide combo menu"""

        self.menu.hideTearOffMenu()
        super().hidePopup()

    def on_menu_selected(self, action):
        """Event handler for menu"""

        self.setCurrentIndex(self.action2index[action])


class TypeMenuComboBox(MenuComboBox):
    """MenuComboBox that comprises types and currencies for CSV import"""

    def __init__(self):
        items = {}
        for typehandler in typehandlers:
            if typehandler == "Money":
                items[typehandler] = dict((currency.code, None)
                                          for currency in currencies)
            else:
                items[typehandler] = None

        super().__init__(items)


class FontChoiceCombo(QFontComboBox):
    """Font choice combo box"""

    label = "Font Family"

    fontChanged = pyqtSignal()

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.setMaximumWidth(150)

        # Set default font
        self.setFont(QFont())

        self.currentFontChanged.connect(self.on_font)

    @property
    def font(self) -> str:
        """Font family name"""

        return self.currentFont().family()

    @font.setter
    def font(self, font: str):
        """Sets font from family name without emitting currentTextChanged"""

        self.currentFontChanged.disconnect(self.on_font)
        self.setCurrentFont(QFont(font))
        self.currentFontChanged.connect(self.on_font)

    def icon(self) -> QIcon:
        """Returns QIcon for button identification"""

        return Icon.font_dialog

    def on_font(self):
        """Font choice event handler"""

        self.fontChanged.emit()


class FontSizeCombo(QComboBox):
    """Font choice combo box"""

    label = "Font Size"
    fontSizeChanged = pyqtSignal()

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__()

        self.setEditable(True)

        for size in main_window.settings.font_sizes:
            self.addItem(str(size))

        idx = self.findText(str(main_window.settings.font_sizes))
        if idx >= 0:
            self.setCurrentIndex(idx)

        validator = QIntValidator(1, 128, self)
        self.setValidator(validator)

        self.currentTextChanged.connect(self.on_text)

    @property
    def size(self) -> int:
        """Size of current text"""

        return int(self.currentText())

    @size.setter
    def size(self, size: int):
        """Sets size without emitting currentTextChanged

        :param size: Size to be set

        """

        self.currentTextChanged.disconnect(self.on_text)
        self.setCurrentText(str(size))
        self.currentTextChanged.connect(self.on_text)

    def icon(self) -> QIcon:
        """Returns icon for button identification"""

        return Icon.font_dialog

    def on_text(self):
        """Font size choice event handler"""

        try:
            value = int(self.currentText())
        except ValueError:
            value = 1
            self.setCurrentText("1")

        if value < 1:
            self.setCurrentText("1")
        if value > 128:
            self.setCurrentText("128")

        self.fontSizeChanged.emit()


class Widgets:
    """Container class for widgets"""

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        # Format toolbar widgets

        self.font_combo = FontChoiceCombo(main_window)

        self.font_size_combo = FontSizeCombo(main_window)

        text_color = QColor("black")
        self.text_color_button = TextColorButton(text_color)

        background_color = QColor("white")
        self.background_color_button = BackgroundColorButton(background_color)

        line_color = QColor("black")
        self.line_color_button = LineColorButton(line_color)

        self.renderer_button = RendererButton(main_window)
        self.rotate_button = RotationButton(main_window)
        self.justify_button = JustificationButton(main_window)
        self.align_button = AlignmentButton(main_window)


class FindEditor(QLineEdit):
    """The Find editor widget for the find toolbar"""

    up = False
    word = False
    case = False
    regexp = False
    results = False

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent widget

        """

        super().__init__(parent)

        self.actions = parent.main_window.main_window_actions

        self.label = "Find editor"
        self.icon = lambda: Icon.find_next
        self.sizePolicy().setHorizontalPolicy(QSizePolicy.Policy.Preferred)
        self.setClearButtonEnabled(True)
        self.addAction(self.actions.find_next,
                       QLineEdit.ActionPosition.LeadingPosition)

        workflows = parent.main_window.workflows
        self.returnPressed.connect(workflows.edit_find_next)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def prepend_actions(self, menu: QMenu):
        """Prepends find specific actions to menu

        :param menu: Find editor context menu

        """

        toggle_case = Action(self, "Match &case",
                             self.on_toggle_case, checkable=True,
                             statustip='Match case in search')

        toggle_results = Action(self, "Code and results",
                                self.on_toggle_results, checkable=True,
                                statustip='Search also considers string '
                                          'representations of result objects.')

        toggle_up = Action(self, "Search &backward",
                           self.on_toggle_up, checkable=True,
                           statustip='Search fore-/backwards')

        toggle_word = Action(self, "&Whole words",
                             self.on_toggle_word, checkable=True,
                             statustip='Whole word search')

        toggle_regexp = Action(self, "Regular expression",
                               self.on_toggle_regexp, checkable=True,
                               statustip='Regular expression search')

        toggle_case.setChecked(self.case)
        toggle_results.setChecked(self.results)
        toggle_up.setChecked(self.up)
        toggle_word.setChecked(self.word)
        toggle_regexp.setChecked(self.regexp)

        actions = (toggle_case, toggle_results, toggle_up, toggle_word,
                   toggle_regexp)
        menu.insertActions(menu.actions()[0], actions)

    def on_context_menu(self, point: QPoint):
        """Context menu event handler

        :param point: Context menu coordinates on screen

        """

        menu = self.createStandardContextMenu()
        menu.insertSeparator(menu.actions()[0])
        self.prepend_actions(menu)
        menu.exec(self.mapToGlobal(point))

    def on_toggle_up(self, toggled: bool):
        """Find upwards toggle event handler

        :param toggled: up option toggle state

        """

        self.up = toggled

    def on_toggle_word(self, toggled: bool):
        """Find whole word toggle event handler

        :param toggled: whole word option toggle state

        """

        self.word = toggled

    def on_toggle_case(self, toggled: bool):
        """Find case sensitively toggle event handler

        :param toggled: case sensitivity option toggle state

        """

        self.case = toggled

    def on_toggle_regexp(self, toggled: bool):
        """Find with regular expression toggle event handler

        :param toggled: regular expression option toggle state

        """

        self.regexp = toggled

    def on_toggle_results(self, toggled: bool):
        """Find in results toggle event handler

        :param toggled: results option toggle state

        """

        self.results = toggled


class CellButton(QPushButton):
    """Button that is used for button cells in the grid"""

    def __init__(self, text: str, grid: QTableView, key: Tuple[int, int, int]):
        """
        :param text: button label text
        :param grid: Main grid
        :param key: key of button's cell (row, column, table)

        """

        super().__init__(text, grid)

        self.grid = grid
        self.key = key  # Key of button cell

        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        """Clicked event handler, executes cell code"""

        code = self.grid.model.code_array(self.key)
        result = self.grid.model.code_array._eval_cell(self.key, code)
        self.grid.model.code_array.frozen_cache[repr(self.key)] = result
        self.grid.model.code_array.result_cache.clear()
        self.grid.model.dataChanged.emit(QModelIndex(), QModelIndex())


class HelpBrowser(QTextBrowser):
    """Help browser widget"""

    def __init__(self, parent: QWidget, path: Path):
        """
        :param parent: Parent window
        :param path: Path to markdown file that is displayed

        """

        super().__init__(parent)

        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.update(path)

    def update(self, path: Path):
        """Updates content

        :param path: Path to markdown file that is displayed

        """

        self.setSearchPaths([str(path.parents[0])])
        self.setHtml(self.get_html(path))

    def get_html(self, path: Path) -> str:
        """Returns html content for content of browser

        :param path: Path to markdown file that is displayed

        """

        try:
            with open(path, encoding='utf-8') as helpfile:
                help_text = helpfile.read()
        except IOError as err:
            return "Error opening file {}: {}".format(path, err)

        if markdown is None:
            error_msg = "<b>Warning: markdown2 is not installed.<br>" + \
                        "Rendering as pain text.</b><p>"
            return error_msg + help_text.replace("\n", "<br>")

        return markdown(help_text, extras=['metadata', 'code-friendly',
                                           'fenced-code-blocks'])
