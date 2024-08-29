#!/usr/bin/env python3
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


**Modal dialogs**

 * :class:`DiscardChangesDialog`
 * :class:`DiscardDataDialog`
 * :class:`ApproveWarningDialog`
 * :class:`DataEntryDialog`
 * :class:`GridShapeDialog`
 * :class:`SinglePageArea`
 * :class:`MultiPageArea`
 * :class:`CsvExportAreaDialog`
 * :class:`SvgExportAreaDialog`
 * :class:`PrintAreaDialog`
 * (:class:`FileDialogBase`)
 * :class:`FileOpenDialog`
 * :class:`FileSaveDialog`
 * :class:`ImageFileOpenDialog`
 * :class:`CsvFileImportDialog`
 * :class:`FileExportDialog`
 * :class:`FindDialog`
 * :class:`ChartDialog`
 * :class:`CsvImportDialog`
 * :class:`CsvExportDialog`
 * :class:`TutorialDialog`
 * :class:`ManualDialog`
 * :class:`PrintPreviewDialog`
"""

from contextlib import redirect_stdout
import csv
try:
    from dataclasses import dataclass
except ImportError:
    from pyspread.lib.dataclasses import dataclass  # Python 3.6 compatibility
from functools import partial
import io
from pathlib import Path
from typing import List, Sequence, Tuple, Union

from PyQt6.QtCore import Qt, QPoint, QSize, QEvent
from PyQt6.QtWidgets \
    import (QApplication, QMessageBox, QFileDialog, QDialog, QLineEdit, QLabel,
            QFormLayout, QVBoxLayout, QGroupBox, QDialogButtonBox, QSplitter,
            QTextBrowser, QCheckBox, QGridLayout, QLayout, QHBoxLayout,
            QPushButton, QWidget, QComboBox, QTableView, QAbstractItemView,
            QPlainTextEdit, QToolBar, QMainWindow, QTabWidget, QInputDialog,
            QComboBox)
from PyQt6.QtGui \
    import (QIntValidator, QImageWriter, QStandardItemModel, QStandardItem,
            QValidator, QWheelEvent)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtPrintSupport import (QPrintPreviewDialog, QPrintPreviewWidget,
                                  QPrinter)

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
except ImportError:
    Figure = None

try:
    import openpyxl
    import pycel
except ImportError:
    openpyxl = None

try:
    import moneyed
except ImportError:
    moneyed = None

try:
    from pyspread.actions import ChartDialogActions
    from pyspread.toolbar import ChartTemplatesToolBar, RChartTemplatesToolBar
    from pyspread.widgets import HelpBrowser, TypeMenuComboBox
    from pyspread.lib.csv import sniff, csv_reader, get_header, convert
    from pyspread.lib.spelltextedit import SpellTextEdit
    from pyspread.settings import (TUTORIAL_PATH, MANUAL_PATH,
                                   MPL_TEMPLATE_PATH, RPY2_TEMPLATE_PATH,
                                   PLOT9_TEMPLATE_PATH)
except ImportError:
    from actions import ChartDialogActions
    from toolbar import ChartTemplatesToolBar, RChartTemplatesToolBar
    from widgets import HelpBrowser, TypeMenuComboBox
    from lib.csv import sniff, csv_reader, get_header, convert
    from lib.spelltextedit import SpellTextEdit
    from settings import (TUTORIAL_PATH, MANUAL_PATH, MPL_TEMPLATE_PATH,
                          RPY2_TEMPLATE_PATH, PLOT9_TEMPLATE_PATH)


class DiscardChangesDialog:
    """Modal dialog that asks if the user wants to discard or save unsaved data

    The modal dialog is shown on accessing the property choice.

    """

    title = "Unsaved changes"
    text = "There are unsaved changes.\nDo you want to save?"
    buttons = QMessageBox.StandardButton
    choices = buttons.Discard | buttons.Cancel | buttons.Save
    default_choice = buttons.Save

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """
        self.main_window = main_window

    @property
    def choice(self) -> bool:
        """User choice

        Returns True if the user confirms in a user dialog that unsaved
        changes will be discarded if conformed.
        Returns False if the user chooses to save the unsaved data
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.main_window, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == QMessageBox.StandardButton.Discard:
            return True
        if button_approval == QMessageBox.StandardButton.Save:
            return False


class DiscardDataDialog(DiscardChangesDialog):
    """Modal dialog that asks if the user wants to discard data"""

    title = "Data to be discarded"
    buttons = QMessageBox.StandardButton
    choices = buttons.Discard | buttons.Cancel
    default_choice = buttons.Cancel

    def __init__(self, main_window: QMainWindow, text: str):
        """
        :param main_window: Application main window
        :param text: Message text

        """

        super().__init__(main_window)
        self.text = text


class ApproveWarningDialog:
    """Modal warning dialog for approving files to be evaled

    The modal dialog is shown on accessing the property choice.

    """

    title = "Security warning"
    text = ("You are going to approve and trust a file that you have not "
            "created yourself. After proceeding, the file is executed.\n \n"
            "It may harm your system as any program can. Please check all "
            "cells thoroughly before proceeding.\n \n"
            "Proceed and sign this file as trusted?")
    buttons = QMessageBox.StandardButton
    choices = buttons.No | buttons.Yes
    default_choice = buttons.No

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent widget, e.g. main window

        """

        self.parent = parent

    @property
    def choice(self) -> bool:
        """User choice

        Returns True iif the user approves leaving safe_mode.
        Returns False iif the user chooses to stay in safe_mode
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.parent, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == self.buttons.Yes:
            return True
        if button_approval == self.buttons.No:
            return False


class DataEntryDialog(QDialog):
    """Modal dialog for entering multiple values"""

    def __init__(self, parent: QWidget, title: str, labels: Sequence[str],
                 initial_data: Sequence[str] = None,
                 groupbox_title: str = None,
                 validators: Sequence[Union[QValidator, bool, None]] = None):
        """
        :param parent: Parent widget, e.g. main window
        :param title: Dialog title
        :param labels: Labels for the values in the dialog
        :param initial_data: Initial values to be displayed in the dialog
        :param validators: Validators for the editors of the dialog

        len(initial_data), len(validators) and len(labels) must be equal

        """

        super().__init__(parent)

        self.labels = labels
        self.groupbox_title = groupbox_title

        if initial_data is None:
            self.initial_data = [""] * len(labels)
        elif len(initial_data) != len(labels):
            raise ValueError("Length of labels and initial_data not equal")
        else:
            self.initial_data = initial_data

        if validators is None:
            self.validators = [None] * len(labels)
        elif len(validators) != len(labels):
            raise ValueError("Length of labels and validators not equal")
        else:
            self.validators = validators

        self.editors = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_form())
        layout.addStretch(1)
        layout.addWidget(self.create_buttonbox())
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)

    @property
    def data(self) -> Tuple[str]:
        """Executes the dialog and returns input as a tuple of strings

        Returns None if the dialog is canceled.

        """

        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            data = []
            for editor in self.editors:
                if isinstance(editor, QLineEdit):
                    data.append(editor.text())
                elif isinstance(editor, QComboBox):
                    data.append(editor.currentText())
                else:
                    data.append(editor.isChecked())
            return tuple(data)

    def create_form(self) -> QGroupBox:
        """Returns form inside a QGroupBox"""

        form_group_box = QGroupBox()
        if self.groupbox_title:
            form_group_box.setTitle(self.groupbox_title)
        form_layout = QFormLayout()

        for label, initial_value, validator in zip(self.labels,
                                                   self.initial_data,
                                                   self.validators):
            if validator is bool:
                editor = QCheckBox("")
                editor.setChecked(initial_value)
            elif hasattr(validator, "acceptable_values"):
                editor = QComboBox()
                editor.addItems(validator.acceptable_values)
                editor.setCurrentText(initial_value)
            else:
                editor = QLineEdit(str(initial_value))
                editor.setAlignment(Qt.AlignmentFlag.AlignRight)
            if validator and validator is not bool:
                editor.setValidator(validator)
            form_layout.addRow(QLabel(label + " :"), editor)
            self.editors.append(editor)

        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_group_box.setLayout(form_layout)

        return form_group_box

    def create_buttonbox(self) -> QDialogButtonBox:
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                      | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box


class GridShapeDialog(DataEntryDialog):
    """Modal dialog for entering the number of rows, columns and tables"""

    def __init__(self, parent: QWidget, shape: Tuple[int, int, int],
                 title: str = "Create a new Grid"):
        """
        :param parent: Parent widget, e.g. main window
        :param shape: Initial shape to be displayed in the dialog

        """

        groupbox_title = "Grid Shape"
        labels = ["Number of Rows", "Number of Columns", "Number of Tables"]
        validator = QIntValidator()
        validator.setBottom(1)  # Do not allow negative values
        validators = [validator] * len(labels)
        super().__init__(parent, title, labels, shape, groupbox_title,
                         validators)

    @property
    def shape(self) -> Tuple[int, int, int]:
        """Executes the dialog and returns an rows, columns, tables

        Returns None if the dialog is canceled.

        """

        try:
            return tuple(map(int, self.data))
        except (TypeError, ValueError):
            pass


@dataclass
class SinglePageArea:
    """Holds single page area boundaries e.g. for export"""

    top: int
    left: int
    bottom: int
    right: int


@dataclass
class MultiPageArea(SinglePageArea):
    """Holds multi page area boundaries e.g. for printing"""

    first: int
    last: int


class CsvExportAreaDialog(DataEntryDialog):
    """Modal dialog for entering csv export area

    Initially, this dialog is filled with the selection bounding box
    if present or with the visible area of <= 1 cell is selected.

    """

    groupbox_title = "Page area"
    labels = ["Top", "Left", "Bottom", "Right"]
    area_cls = SinglePageArea

    def __init__(self, parent: QWidget, grid: QTableView, title: str):
        """
        :param parent: Parent widget, e.g. main window
        :param grid: The main grid widget
        :param title: Dialog title

        """

        self.grid = grid
        self.shape = grid.model.shape

        super().__init__(parent, title, self.labels, self._initial_values,
                         self.groupbox_title, self.validator_list)

    @property
    def _validator(self):
        """Returns int validator for positive numbers"""

        validator = QIntValidator()
        validator.setBottom(0)
        return validator

    @property
    def _row_validator(self) -> QIntValidator:
        """Returns row validator"""

        row_validator = self._validator
        row_validator.setTop(self.shape[0] - 1)
        return row_validator

    @property
    def _column_validator(self) -> QIntValidator:
        """Returns column validator"""

        column_validator = self._validator
        column_validator.setTop(self.shape[1] - 1)
        return column_validator

    @property
    def validator_list(self) -> List[QIntValidator]:
        """Returns list of validators for dialog"""

        return [self._row_validator, self._column_validator] * 2

    @property
    def _initial_values(self) -> Tuple[int, int, int, int]:
        """Returns tuple of initial values"""

        grid = self.grid
        shape = grid.model.shape

        if grid.selection and len(grid.selected_idx) > 1:
            (bb_top, bb_left), (bb_bottom, bb_right) = \
                grid.selection.get_grid_bbox(shape)
        else:
            bb_top, bb_bottom = grid.rowAt(0), grid.rowAt(grid.height())
            bb_left, bb_right = grid.columnAt(0), grid.columnAt(grid.width())

        return bb_top, bb_left, bb_bottom, bb_right

    @property
    def area(self) -> Union[SinglePageArea, MultiPageArea]:
        """Executes the dialog and returns top, left, bottom, right

        Returns None if the dialog is canceled.

        """

        try:
            int_data = map(int, self.data)
            data = (min(self.shape[i % 2], d) for i, d in enumerate(int_data))
        except (TypeError, ValueError):
            return

        if data is not None:
            try:
                return self.area_cls(*data)
            except ValueError:
                return


class SvgExportAreaDialog(CsvExportAreaDialog):
    """Modal dialog for entering svg export area

    Initially, this dialog is filled with the selection bounding box
    if present or with the visible area of <= 1 cell is selected.

    """

    groupbox_title = "SVG export area"


class PrintAreaDialog(CsvExportAreaDialog):
    """Modal dialog for entering print area

    Initially, this dialog is filled with the selection bounding box
    if present or with the visible area of <= 1 cell is selected.
    Initially, the current table is selected.

    """

    labels = ["Top", "Left", "Bottom", "Right", "First table", "Last table"]
    area_cls = MultiPageArea

    @property
    def _table_validator(self) -> QIntValidator:
        """Returns column validator"""

        table_validator = self._validator
        table_validator.setTop(self.shape[1] - 1)
        return table_validator

    @property
    def validator_list(self) -> List[QIntValidator]:
        """Returns list of validators for dialog"""

        validators = super().validator_list
        validators += [self._table_validator] * 2
        return validators

    @property
    def _initial_values(self) -> Tuple[int, int, int, int, int, int]:
        """Returns tuple of initial values"""

        bb_top, bb_left, bb_bottom, bb_right = super()._initial_values
        table = self.grid.table

        return bb_top, bb_left, bb_bottom, bb_right, table, table


class TupleValidator(QValidator):
    """Validator for a tuple of values, normally strings"""

    def __init__(self, *acceptable_values):
        super().__init__()
        self.acceptable_values = acceptable_values

    def validate(self, text, pos):
        """Validator core function. Must be overloaded."""

        if text in self.acceptable_values:
            return self.State.Acceptable
        return self.State.Invalid


class PreferencesDialog(DataEntryDialog):
    """Modal dialog for entering pyspread preferences"""

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent widget, e.g. main window

        """

        title = "Preferences"
        groupbox_title = "Global settings"
        labels = ["Signature key for files", "Cell calculation timeout [ms]",
                  "Frozen cell refresh period [ms]", "Number of recent files",
                  "Show sum in statusbar"]
        self.keys = ["signature_key", "timeout", "refresh_timeout",
                     "max_file_history", "show_statusbar_sum"]
        self.mappers = [str, int, int, int, bool]

        int_validator = QIntValidator()
        int_validator.setBottom(0)  # Do not allow negative values

        validators = [None, int_validator, int_validator, int_validator, bool]
        if moneyed is not None:
            currencies = map(str, moneyed.list_all_currencies())
            tuple_validator = TupleValidator(*currencies)
            labels.append("Money default currency")
            self.keys.append("currency_iso_code")
            self.mappers.append(str)
            validators.append(tuple_validator)

        data = [getattr(parent.settings, key) for key in self.keys]
        super().__init__(parent, title, labels, data, groupbox_title,
                         validators)

    @property
    def data(self) -> dict:
        """Executes the dialog and returns a dict containing preferences data

        Returns None if the dialog is canceled.

        """

        data = super().data
        if data is not None:
            data_dict = {}
            for key, mapper, data in zip(self.keys, self.mappers, data):
                data_dict[key] = mapper(data)
            return data_dict


class CellKeyDialog(DataEntryDialog):
    """Modal dialog for entering a cell key, i.e. row, column, table"""

    def __init__(self, parent: QWidget, shape: Tuple[int, int, int]):
        """
        :param parent: Parent widget, e.g. main window
        :param shape: Grid shape

        """

        title = "Go to cell"
        groupbox_title = "Cell index"
        labels = ["Row", "Column", "Table"]

        row_validator = QIntValidator()
        row_validator.setRange(0, shape[0] - 1)
        column_validator = QIntValidator()
        column_validator.setRange(0, shape[1] - 1)
        table_validator = QIntValidator()
        table_validator.setRange(0, shape[2] - 1)
        validators = [row_validator, column_validator, table_validator]

        super().__init__(parent, title, labels, None, groupbox_title,
                         validators)

    @property
    def key(self) -> Tuple[int, int, int]:
        """Executes the dialog and returns rows, columns, tables

        Returns None if the dialog is canceled.

        """

        data = self.data

        if data is None:
            return

        try:
            return tuple(map(int, data))
        except ValueError:
            pass


class FileDialogBase:
    """Base class for modal file dialogs

    The chosen filename is stored in the file_path attribute
    The chosen name filter is stored in the chosen_filter attribute
    If the dialog is aborted then both filepath and chosen_filter are None

    _get_filepath must be overloaded

    """

    file_path = None

    title = "Choose file"

    filters_list = [
        "Pyspread un-compressed (*.pysu)",
        "Pyspread compressed (*.pys)",
    ]
    if openpyxl is not None:
        filters_list.append("Office Open XML - Tabellendokument (*.xlsx)")

    selected_filter = None

    @property
    def filters(self) -> str:
        """Formatted filters for qt"""

        return ";;".join(self.filters_list)

    @property
    def suffix(self) -> str:
        """Suffix for filepath"""

        return self.selected_filter.split("(")[-1].strip()[1:-1]

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        self.main_window = main_window
        self.selected_filter = self.filters_list[0]

        self.show_dialog()

    def show_dialog(self):
        """Sublasses must overload this method"""

        raise NotImplementedError


class FileOpenDialog(FileDialogBase):
    """Modal dialog for opening a pyspread file"""

    title = "Open"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class FileSaveDialog(FileDialogBase):
    """Modal dialog for saving a pyspread file"""

    title = "Save"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_output_path
        self.file_path, self.selected_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class ImageFileOpenDialog(FileDialogBase):
    """Modal dialog for inserting an image"""

    title = "Insert image"

    img_formats = QImageWriter.supportedImageFormats()
    img_format_strings = (f"*.{fmt.data().decode()}" for fmt in img_formats)
    img_format_string = " ".join(img_format_strings)
    name_filter = f"Images ({img_format_string})" + ";;" \
                  "Scalable Vector Graphics (*.svg *.svgz)"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window,
                                        self.title,
                                        str(path),
                                        self.name_filter)


class CsvFileImportDialog(FileDialogBase):
    """Modal dialog for importing csv files"""

    title = "Import data"
    filters_list = [
        "CSV file (*.*)",
    ]

    @property
    def suffix(self):
        """Do not offer suffix for filepath"""

        return

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_import_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.filters_list[0])


class FileExportDialog(FileDialogBase):
    """Modal dialog for exporting csv files"""

    title = "Export data"

    def __init__(self, main_window: QMainWindow, filters_list: List[str]):
        """
        :param main_window: Application main window
        :param filters_list: List of filter strings

        """

        self.filters_list = filters_list
        super().__init__(main_window)

    @property
    def suffix(self) -> str:
        """Suffix for filepath"""

        return f".{self.selected_filter.split()[0].lower()}"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_export_path
        self.file_path, self.selected_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.filters_list[0])


@dataclass
class FindDialogState:
    """Dataclass for FindDialog state storage"""

    pos: QPoint
    case: bool
    results: bool
    more: bool
    backward: bool
    word: bool
    regex: bool
    start: bool


class FindDialog(QDialog):
    """Find dialog that is launched from the main menu"""

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        self.main_window = main_window
        workflows = main_window.workflows

        self._create_widgets()
        self._layout()
        self._order()

        self.setWindowTitle("Find")

        self.extension.hide()

        self.more_button.toggled.connect(self.extension.setVisible)

        self.find_button.clicked.connect(partial(workflows.find_dialog_on_find,
                                                 self))

        # Restore state
        state = self.main_window.settings.find_dialog_state
        if state is not None:
            self.restore(state)

    def _create_widgets(self):
        """Create find dialog widgets

        :param results_checkbox: Show find results checkbox

        """

        self.search_text_label = QLabel("Search for:")
        self.search_text_editor = QLineEdit()
        self.search_text_label.setBuddy(self.search_text_editor)

        self.case_checkbox = QCheckBox("Match &case")
        self.results_checkbox = QCheckBox("Code and &results")

        self.find_button = QPushButton("&Find")
        self.find_button.setDefault(True)

        self.more_button = QPushButton("&More")
        self.more_button.setCheckable(True)
        self.more_button.setAutoDefault(False)

        self.extension = QWidget()

        self.backward_checkbox = QCheckBox("&Backward")
        self.word_checkbox = QCheckBox("&Whole words")
        self.regex_checkbox = QCheckBox("Regular e&xpression")
        self.from_start_checkbox = QCheckBox("From &start")

        self.button_box = QDialogButtonBox(Qt.Orientation.Vertical)
        self.button_box.addButton(self.find_button,
                                  QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(self.more_button,
                                  QDialogButtonBox.ButtonRole.ActionRole)

    def _layout(self):
        """Find dialog layout"""

        self.extension_layout = QVBoxLayout()
        self.extension_layout.setContentsMargins(0, 0, 0, 0)
        self.extension_layout.addWidget(self.backward_checkbox)
        self.extension_layout.addWidget(self.word_checkbox)
        self.extension_layout.addWidget(self.regex_checkbox)
        self.extension_layout.addWidget(self.from_start_checkbox)
        self.extension.setLayout(self.extension_layout)

        self.text_layout = QGridLayout()
        self.text_layout.addWidget(self.search_text_label, 0, 0)
        self.text_layout.addWidget(self.search_text_editor, 0, 1)
        self.text_layout.setColumnStretch(0, 1)

        self.search_layout = QVBoxLayout()
        self.search_layout.addLayout(self.text_layout)
        self.search_layout.addWidget(self.case_checkbox)
        self.search_layout.addWidget(self.results_checkbox)

        self.main_layout = QGridLayout()
        self.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.main_layout.addLayout(self.search_layout, 0, 0)
        self.main_layout.addWidget(self.button_box, 0, 1)
        self.main_layout.addWidget(self.extension, 1, 0, 1, 2)
        self.main_layout.setRowStretch(2, 1)

        self.setLayout(self.main_layout)

    def _order(self):
        """Find dialog tabOrder"""

        self.setTabOrder(self.results_checkbox, self.backward_checkbox)
        self.setTabOrder(self.backward_checkbox, self.word_checkbox)
        self.setTabOrder(self.word_checkbox, self.regex_checkbox)
        self.setTabOrder(self.regex_checkbox, self.from_start_checkbox)

    def restore(self, state):
        """Restores state from FindDialogState"""

        self.move(state.pos)
        self.case_checkbox.setChecked(state.case)
        self.results_checkbox.setChecked(state.results)
        self.more_button.setChecked(state.more)
        self.backward_checkbox.setChecked(state.backward)
        self.word_checkbox.setChecked(state.word)
        self.regex_checkbox.setChecked(state.regex)
        self.from_start_checkbox.setChecked(state.start)

    # Overrides

    def closeEvent(self, event: QEvent):
        """Store state for next invocation and close

        :param event: Close event

        """

        state = FindDialogState(pos=self.pos(),
                                case=self.case_checkbox.isChecked(),
                                results=self.results_checkbox.isChecked(),
                                more=self.more_button.isChecked(),
                                backward=self.backward_checkbox.isChecked(),
                                word=self.word_checkbox.isChecked(),
                                regex=self.regex_checkbox.isChecked(),
                                start=self.from_start_checkbox.isChecked())
        self.main_window.settings.find_dialog_state = state

        super().closeEvent(event)


class ReplaceDialog(FindDialog):
    """Replace dialog that is launched from the main menu"""

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__(main_window)

        workflows = main_window.workflows

        self.setWindowTitle("Replace")

        self.results_checkbox.setDisabled(True)

        self.replace_text_label = QLabel("Replace with:")
        self.replace_text_editor = QLineEdit()
        self.replace_text_label.setBuddy(self.replace_text_editor)

        self.text_layout.addWidget(self.replace_text_label, 1, 0)
        self.text_layout.addWidget(self.replace_text_editor, 1, 1)

        self.replace_button = QPushButton("&Replace")
        self.replace_all_button = QPushButton("Replace &all")

        self.button_box.addButton(self.replace_button,
                                  QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(self.replace_all_button,
                                  QDialogButtonBox.ButtonRole.ActionRole)

        self.setTabOrder(self.search_text_editor, self.replace_text_editor)
        self.setTabOrder(self.more_button, self.replace_button)

        p_onreplace = partial(workflows.replace_dialog_on_replace, self)
        self.replace_button.clicked.connect(p_onreplace)

        p_onreplaceall = partial(workflows.replace_dialog_on_replace_all, self)
        self.replace_all_button.clicked.connect(p_onreplaceall)


class ChartDialog(QDialog):
    """The chart dialog"""

    def __init__(self, parent: QWidget, key: Tuple[int, int, int],
                 size: Tuple[int, int] = (1000, 700)):
        """
        :param parent: Parent window
        :param key: Target cell for chart
        :param size: Initial dialog size

        """

        self.key = key

        if Figure is None:
            raise ImportError

        super().__init__(parent)

        self.actions = ChartDialogActions(self)

        self.chart_templates_toolbar = ChartTemplatesToolBar(self)
        self.rchart_templates_toolbar = RChartTemplatesToolBar(self)

        self.setWindowTitle(f"Chart dialog for cell {key}")

        self.resize(*size)
        self.parent = parent

        self.actions = ChartDialogActions(self)

        self.dialog_ui()

    def on_template(self):
        """Event handler for pressing a template toolbar button"""

        chart_template_name = self.sender().data()
        chart_template_code = None

        tpl_paths = MPL_TEMPLATE_PATH, RPY2_TEMPLATE_PATH, PLOT9_TEMPLATE_PATH
        for tpl_path in tpl_paths:
            full_tpl_path = tpl_path / chart_template_name
            try:
                with open(full_tpl_path, encoding='utf8') as template_file:
                    chart_template_code = template_file.read()
            except OSError:
                pass

        if chart_template_code is None:
            return

        self.editor.insertPlainText(chart_template_code)

    def dialog_ui(self):
        """Sets up dialog UI"""

        msg = "Enter Python code into the editor to the left. Globals " + \
              "such as X, Y, Z, S are available as they are in the grid. " + \
              "The last line must result in a matplotlib figure.\n \n" + \
              "Pressing Apply displays the figure or an error message in " + \
              "the right area."

        self.message = QTextBrowser(self)
        self.message.setText(msg)
        self.editor = SpellTextEdit(self)
        self.splitter = QSplitter(self)

        buttonbox = self.create_buttonbox()

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.message)
        self.splitter.setOpaqueResize(False)
        self.splitter.setSizes([9999, 9999])

        # Layout
        layout = QVBoxLayout(self)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.chart_templates_toolbar)
        toolbar_layout.addWidget(self.rchart_templates_toolbar)
        layout.addLayout(toolbar_layout)

        layout.addWidget(self.splitter)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

    def apply(self):
        """Executes the code in the dialog and updates the canvas"""

        # Get current cell
        key = self.parent.grid.current
        code = self.editor.toPlainText()

        filelike = io.StringIO()
        with redirect_stdout(filelike):
            figure = self.parent.grid.model.code_array._eval_cell(key, code)
        stdout_str = filelike.getvalue()
        if stdout_str:
            stdout_str += "\n \n"

        if isinstance(figure, Figure):
            canvas = FigureCanvasQTAgg(figure)
            self.splitter.replaceWidget(1, canvas)
            try:
                canvas.draw()
            except Exception:
                pass
        elif isinstance(figure, bytes) or isinstance(figure, str):
            with redirect_stdout(filelike):
                if isinstance(figure, str):
                    figure = bytearray(figure, encoding='utf-8')
                svg_widget = QSvgWidget()
                self.splitter.replaceWidget(1, svg_widget)
                svg_widget.renderer().load(figure)
            stdout_str = filelike.getvalue()
            if stdout_str:
                stdout_str += "\n \n"
                msg = stdout_str + f"Error:\n{figure}"
                self.message.setText(msg)
        else:
            if isinstance(figure, Exception):
                msg = stdout_str + f"Error:\n{figure}"
                self.message.setText(msg)
            else:
                msg = stdout_str
                msg_text = "Error:\n{} has type '{}', " + \
                           "which is no instance of {}."
                msg += msg_text.format(figure, type(figure).__name__,
                                       Figure)
                self.message.setText(msg)

            if self.splitter.widget(1) != self.message:
                self.splitter.replaceWidget(1, self.message)

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                      | QDialogButtonBox.StandardButton.Apply
                                      | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(
            QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        return button_box


class CsvParameterGroupBox(QGroupBox):
    """QGroupBox that holds parameter widgets for the csv import dialog"""

    title = "Parameters"

    quotings = "QUOTE_ALL", "QUOTE_MINIMAL", "QUOTE_NONNUMERIC", "QUOTE_NONE"

    # Tooltips
    encoding_widget_tooltip = "CSV file encoding"
    quoting_widget_tooltip = \
        "Controls when quotes should be generated by the writer and " \
        "recognised by the reader."
    quotechar_tooltip = \
        "A one-character string used to quote fields containing special " \
        "characters, such as the delimiter or quotechar, or which contain " \
        "new-line characters."
    delimiter_tooltip = "A one-character string used to separate fields."
    escapechar_tooltip = "A one-character string used by the writer to " \
        "escape the delimiter if quoting is set to QUOTE_NONE and the " \
        "quotechar if doublequote is False. On reading, the escapechar " \
        "removes any special meaning from the following character."
    hasheader_tooltip = \
        "Analyze the CSV file and treat the first row as strings if it " \
        "appears to be a series of column headers."
    keepheader_tooltip = "Import header labels as str in the first row"
    doublequote_tooltip = \
        "Controls how instances of quotechar appearing inside a field " \
        "should be themselves be quoted. When True, the character is " \
        "doubled. When False, the escapechar is used as a prefix to the " \
        "quotechar."
    skipinitialspace_tooltip = "When True, whitespace immediately following " \
        "the delimiter is ignored."

    # Default values that are displayed if the sniffer fails
    default_quoting = "QUOTE_MINIMAL"
    default_quotechar = '"'
    default_delimiter = ','

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent window

        """

        super().__init__(parent)
        self.parent = parent
        self.default_encoding = parent.parent.settings.default_encoding
        self.encodings = parent.parent.settings.encodings

        self.setTitle(self.title)
        self._create_widgets()
        self._layout()

        self.hasheader_widget.toggled.connect(self.on_hasheader_toggled)

    def _create_widgets(self):
        """Create widgets for all parameters"""

        # Encoding
        self.encoding_label = QLabel("Encoding")
        self.encoding_widget = QComboBox(self.parent)
        self.encoding_widget.addItems(self.encodings)
        if self.default_encoding in self.encodings:
            default_encoding_idx = self.encodings.index(self.default_encoding)
            self.encoding_widget.setCurrentIndex(default_encoding_idx)
        self.encoding_widget.setEditable(False)
        self.encoding_widget.setToolTip(self.encoding_widget_tooltip)

        # Quote character
        self.quotechar_label = QLabel("Quote character")
        self.quotechar_widget = QLineEdit(self.default_quotechar, self.parent)
        self.quotechar_widget.setMaxLength(1)
        self.quotechar_widget.setToolTip(self.quotechar_tooltip)

        # Delimiter
        self.delimiter_label = QLabel("Delimiter")
        self.delimiter_widget = QLineEdit(self.default_delimiter, self.parent)
        self.delimiter_widget.setMaxLength(1)
        self.delimiter_widget.setToolTip(self.delimiter_tooltip)

        # Escape character
        self.escapechar_label = QLabel("Escape character")
        self.escapechar_widget = QLineEdit(self.parent)
        self.escapechar_widget.setMaxLength(1)
        self.escapechar_widget.setToolTip(self.escapechar_tooltip)

        # Quote style
        self.quoting_label = QLabel("Quote style")
        self.quoting_widget = QComboBox(self.parent)
        self.quoting_widget.addItems(self.quotings)
        if self.default_quoting in self.quotings:
            default_quoting_idx = self.quotings.index(self.default_quoting)
            self.quoting_widget.setCurrentIndex(default_quoting_idx)
        self.quoting_widget.setEditable(False)
        self.quoting_widget.setToolTip(self.quoting_widget_tooltip)

        # Header present
        self.hasheader_label = QLabel("Header present")
        self.hasheader_widget = QCheckBox(self.parent)
        self.hasheader_widget.setToolTip(self.hasheader_tooltip)

        # Keep header
        self.keepheader_label = QLabel("Keep header")
        self.keepheader_widget = QCheckBox(self.parent)
        self.keepheader_widget.setToolTip(self.keepheader_tooltip)

        # Double quote
        self.doublequote_label = QLabel("Doublequote")
        self.doublequote_widget = QCheckBox(self.parent)
        self.doublequote_widget.setToolTip(self.doublequote_tooltip)

        # Skip initial space
        self.skipinitialspace_label = QLabel("Skip initial space")
        self.skipinitialspace_widget = QCheckBox(self.parent)
        self.skipinitialspace_widget.setToolTip(self.skipinitialspace_tooltip)

        # Mapping to csv dialect

        self.csv_parameter2widget = {
            "encoding": self.encoding_widget,  # Extra dialect attribute
            "quotechar": self.quotechar_widget,
            "delimiter": self.delimiter_widget,
            "escapechar": self.escapechar_widget,
            "quoting": self.quoting_widget,
            "hasheader": self.hasheader_widget,  # Extra dialect attribute
            "keepheader": self.keepheader_widget,  # Extra dialect attribute
            "doublequote": self.doublequote_widget,
            "skipinitialspace": self.skipinitialspace_widget,
        }

    def _layout(self):
        """Layout widgets"""

        hbox_layout = QHBoxLayout()
        left_form_layout = QFormLayout()
        right_form_layout = QFormLayout()

        hbox_layout.addLayout(left_form_layout)
        hbox_layout.addSpacing(20)
        hbox_layout.addLayout(right_form_layout)

        left_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        right_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        left_form_layout.addRow(self.encoding_label, self.encoding_widget)
        left_form_layout.addRow(self.quotechar_label, self.quotechar_widget)
        left_form_layout.addRow(self.delimiter_label, self.delimiter_widget)
        left_form_layout.addRow(self.escapechar_label, self.escapechar_widget)

        right_form_layout.addRow(self.quoting_label, self.quoting_widget)
        right_form_layout.addRow(self.hasheader_label, self.hasheader_widget)
        right_form_layout.addRow(self.keepheader_label, self.keepheader_widget)
        right_form_layout.addRow(self.doublequote_label,
                                 self.doublequote_widget)
        right_form_layout.addRow(self.skipinitialspace_label,
                                 self.skipinitialspace_widget)

        self.setLayout(hbox_layout)

    # Event handlers
    def on_hasheader_toggled(self, toggled: bool):
        """Disables keep_header if hasheader is not toggled"""

        self.keepheader_widget.setChecked(False)
        self.keepheader_widget.setEnabled(toggled)

    def adjust_csvdialect(self, dialect: csv.Dialect) -> csv.Dialect:
        """Adjusts csv dialect from widget settings

        Note that the dialect has two extra attributes encoding and hasheader

        :param dialect: Attributes class for csv reading and writing

        """

        for parameter, widget in self.csv_parameter2widget.items():
            if hasattr(widget, "currentText"):
                value = widget.currentText()
            elif hasattr(widget, "isChecked"):
                value = widget.isChecked()
            elif hasattr(widget, "text"):
                value = widget.text()
            else:
                raise AttributeError(f"{widget} unsupported")

            # Convert strings to csv constants
            if parameter == "quoting" and isinstance(value, str):
                value = getattr(csv, value)

            setattr(dialect, parameter, value)

        return dialect

    def set_csvdialect(self, dialect: csv.Dialect):
        """Update widgets from given csv dialect

        :param dialect: Attributes class for csv reading and writing

        """

        for parameter in self.csv_parameter2widget:
            try:
                value = getattr(dialect, parameter)
            except AttributeError:
                value = None

            if value is not None:
                widget = self.csv_parameter2widget[parameter]
                if hasattr(widget, "setCurrentText"):
                    try:
                        widget.setCurrentText(value)
                    except TypeError:
                        try:
                            widget.setCurrentIndex(value)
                        except TypeError:
                            pass
                elif hasattr(widget, "setChecked"):
                    widget.setChecked(bool(value))
                elif hasattr(widget, "setText"):
                    widget.setText(value)
                else:
                    raise AttributeError(f"{widget} unsupported")
        if not self.hasheader_widget.isChecked():
            self.keepheader_widget.setEnabled(False)


class CsvTable(QTableView):
    """Table for previewing csv file content"""

    no_rows = 9

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent window

        """

        super().__init__(parent)

        self.parent = parent

        self.comboboxes = []

        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().hide()

    def add_choice_row(self, length: int):
        """Adds row with comboboxes for digest choice

        :param length: Number of columns in row

        """

        item_row = map(QStandardItem, [''] * length)
        self.comboboxes = [TypeMenuComboBox() for _ in range(length)]
        self.model.appendRow(item_row)
        for i, combobox in enumerate(self.comboboxes):
            self.setIndexWidget(self.model.index(0, i), combobox)

    def fill(self, filepath: Path, dialect: csv.Dialect,
             digest_types: List[str] = None):
        """Fills the csv table with values from the csv file

        :param filepath: Path to csv file
        :param dialect: Attributes class for csv reading and writing
        :param digest_types: Names of preprocessing functions for csv values

        """

        self.model.clear()

        self.verticalHeader().hide()

        try:
            if hasattr(dialect, "encoding"):
                encoding = dialect.encoding
            else:
                encoding = self.parent.csv_encoding
            try:
                with open(filepath, newline='', encoding=encoding) as csvfile:
                    if hasattr(dialect, 'hasheader') and dialect.hasheader:
                        header = get_header(csvfile, dialect)
                        self.model.setHorizontalHeaderLabels(header)
                        self.horizontalHeader().show()
                    else:
                        self.horizontalHeader().hide()

                    for i, row in enumerate(csv_reader(csvfile, dialect)):
                        if i >= self.no_rows:
                            break
                        if i == 0:
                            self.add_choice_row(len(row))
                        if digest_types is None:
                            item_row = map(QStandardItem, map(str, row))
                        else:
                            codes = (convert(ele, t)
                                     for ele, t in zip(row, digest_types))
                            item_row = map(QStandardItem, codes)
                        self.model.appendRow(item_row)
            except UnicodeDecodeError:
                QMessageBox.warning(self.parent, "Encoding error",
                                    f"File is not encoded in {encoding}.")
                self.model.clear()

        except (OSError, csv.Error) as error:
            title = "CSV Import Error"
            text_tpl = "Error importing csv file {path}.\n \n" +\
                       "{errtype}: {error}"
            text = text_tpl.format(path=filepath, errtype=type(error).__name__,
                                   error=error)
            QMessageBox.warning(self.parent, title, text)

    def get_digest_types(self) -> List[str]:
        """Returns list of digest types from comboboxes"""

        try:
            return [cbox.currentText() for cbox in self.comboboxes]
        except RuntimeError:
            return []

    def update_comboboxes(self, digest_types: List[str]):
        """Updates the cono boxes to show digest_types

        :param digest_types: Names of preprocessing functions for csv values

        """

        for combobox, digest_type in zip(self.comboboxes, digest_types):
            combobox.setCurrentText(digest_type)


class CsvImportDialog(QDialog):
    """Modal dialog for importing csv files"""

    title = "CSV import"

    def __init__(self, parent: QWidget, filepath: Path,
                 digest_types: List[str] = None):
        """
        :param parent: Parent window
        :param filepath: Path to csv file
        :param digest_types: Names of preprocessing functions for csv values

        """

        super().__init__(parent)

        self.parent = parent
        self.filepath = filepath
        self.digest_types = digest_types

        self.sniff_size = parent.settings.sniff_size

        self.csv_encoding = 'utf-8'
        self.dialect = None

        self.setWindowTitle(self.title)

        self.parameter_groupbox = CsvParameterGroupBox(self)
        self.csv_table = CsvTable(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.parameter_groupbox)
        layout.addWidget(self.csv_table)
        layout.addWidget(self.create_buttonbox())

        self.setLayout(layout)

        self.reset()

    def create_buttonbox(self):
        """Returns a QDialogButtonBox"""

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Reset
                                      | QDialogButtonBox.StandardButton.Apply
                                      | QDialogButtonBox.StandardButton.Ok
                                      | QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(
            QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset)
        button_box.button(
            QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)

        return button_box

    def _sniff_dialect(self):
        """Sniff the dialect of self.filepath`"""

        try:
            return sniff(self.filepath, self.sniff_size, self.csv_encoding)
        except UnicodeError:
            self.csv_encoding, ok = QInputDialog().getItem(
                self, f"{self.filepath} not encoded in utf-8",
                f"Encoding of {self.filepath}",
                self.parent.settings.encodings)
            if ok:
                return self._sniff_dialect()
        except (OSError, csv.Error) as error:
            title = "CSV Import Error"
            text = f"Error sniffing csv file {self.filepath}.\n \n" + \
                   f"{type(error).__name__}: {error}"
            QMessageBox.warning(self.parent, title, text)

    # Button event handlers

    def reset(self):
        """Button event handler, resets parameter_groupbox and csv_table"""

        dialect = self._sniff_dialect()
        if dialect is None:
            return

        self.parameter_groupbox.set_csvdialect(dialect)
        self.csv_table.fill(self.filepath, dialect)
        if self.digest_types is not None:
            self.csv_table.update_comboboxes(self.digest_types)

    def apply(self):
        """Button event handler, applies parameters to csv_table"""

        sniff_dialect = self._sniff_dialect()
        if sniff_dialect is None:
            return

        try:
            dialect = self.parameter_groupbox.adjust_csvdialect(sniff_dialect)
        except AttributeError as error:
            title = "CSV Import Error"
            text_tpl = "Error setting dialect for csv file {path}.\n \n" +\
                       "{errtype}: {error}"
            text = text_tpl.format(path=self.filepath,
                                   errtype=type(error).__name__, error=error)
            QMessageBox.warning(self.parent, title, text)
            return

        digest_types = self.csv_table.get_digest_types()
        self.csv_table.fill(self.filepath, dialect, digest_types)
        self.csv_table.update_comboboxes(digest_types)

    def accept(self):
        """Button event handler, starts csv import"""

        sniff_dialect = self._sniff_dialect()
        if sniff_dialect is None:
            return

        try:
            dialect = self.parameter_groupbox.adjust_csvdialect(sniff_dialect)
        except AttributeError as error:
            title = "CSV Import Error"
            text_tpl = "Error setting dialect for csv file {path}.\n \n" +\
                       "{errtype}: {error}"
            text = text_tpl.format(path=self.filepath,
                                   errtype=type(error).__name__, error=error)
            QMessageBox.warning(self.parent, title, text)
            self.reject()
            return

        self.digest_types = self.csv_table.get_digest_types()
        self.dialect = dialect

        super().accept()


class CsvExportDialog(QDialog):
    """Modal dialog for exporting csv files"""

    title = "CSV export"
    maxrows = 10

    def __init__(self, parent: QWidget, csv_area: SinglePageArea):
        """
        :param parent: Parent window
        :param csv_area: Grid area to be exported

        """

        super().__init__(parent)

        self.parent = parent

        self.csv_area = csv_area

        self.dialect = self.default_dialect

        self.setWindowTitle(self.title)

        self.parameter_groupbox = CsvParameterGroupBox(self)
        self.csv_preview = QPlainTextEdit(self)
        self.csv_preview.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.parameter_groupbox)
        layout.addWidget(self.csv_preview)
        layout.addWidget(self.create_buttonbox())

        self.setLayout(layout)

        self.reset()

    @property
    def default_dialect(self) -> csv.Dialect:
        """Default dialect for export based on excel-tab"""

        dialect = csv.excel
        dialect.encoding = "utf-8"
        dialect.hasheader = False

        return dialect

    def reset(self):
        """Button event handler, resets parameter_groupbox and csv_preview"""

        self.parameter_groupbox.set_csvdialect(self.default_dialect)
        self.csv_preview.clear()

    def apply(self):
        """Button event handler, applies parameters to csv_preview"""

        top = self.csv_area.top
        left = self.csv_area.left
        bottom = self.csv_area.bottom
        right = self.csv_area.right
        table = self.parent.grid.table

        bottom = min(bottom-top, self.maxrows-1) + top

        code_array = self.parent.grid.model.code_array
        csv_data = code_array[top: bottom + 1, left: right + 1, table]

        adjust_csvdialect = self.parameter_groupbox.adjust_csvdialect
        dialect = adjust_csvdialect(self.default_dialect)

        str_io = io.StringIO()
        writer = csv.writer(str_io, dialect=dialect)
        writer.writerows(csv_data)

        self.csv_preview.setPlainText(str_io.getvalue())

    def accept(self):
        """Button event handler, starts csv import"""

        adjust_csvdialect = self.parameter_groupbox.adjust_csvdialect
        self.dialect = adjust_csvdialect(self.default_dialect)
        super().accept()

    def create_buttonbox(self) -> QDialogButtonBox:
        """Returns button box with Reset, Apply, Ok, Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Reset
                                      | QDialogButtonBox.StandardButton.Apply
                                      | QDialogButtonBox.StandardButton.Ok
                                      | QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(
            QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset)
        button_box.button(
            QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)

        return button_box


class TutorialDialog(QDialog):
    """Dialog for browsing the pyspread tutorial"""

    window_title = "pyspread tutorial"
    size_hint = 1000, 800
    path: Path = TUTORIAL_PATH / 'tutorial.md'

    def __init__(self, parent: QWidget):
        """
        :param parent: Parent window

        """

        super().__init__(parent)

        self._create_widgets()
        self._layout()

    def _create_widgets(self):
        """Creates dialog widgets, e.g. the browser"""

        self.browser = HelpBrowser(self, self.path)

    def _layout(self):
        """Dialog layout management"""

        self.setWindowTitle(self.window_title)

        layout = QHBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    # Overrides

    def sizeHint(self) -> QSize:
        """QDialog.sizeHint override"""

        return QSize(*self.size_hint)


class ManualDialog(TutorialDialog):
    """Dialog for browsing the pyspread manual"""

    window_title = "pyspread manual"
    size_hint = 1000, 800
    title2path = {
        "Overview": MANUAL_PATH / 'overview.md',
        "Concepts": MANUAL_PATH / 'basic_concepts.md',
        "Workspace": MANUAL_PATH / 'workspace.md',
        "File": MANUAL_PATH / 'file_menu.md',
        "Edit": MANUAL_PATH / 'edit_menu.md',
        "View": MANUAL_PATH / 'view_menu.md',
        "Format": MANUAL_PATH / 'format_menu.md',
        "Macro": MANUAL_PATH / 'macro_menu.md',
        "Advanced topics": MANUAL_PATH / 'advanced_topics.md',
    }

    def _create_widgets(self):
        """Creates tabbar and dialog browser"""

        self.tabbar = QTabWidget(self)
        for title, path in self.title2path.items():
            self.tabbar.addTab(HelpBrowser(self, path), title)

    def _layout(self):
        """Dialog layout management"""

        self.setWindowTitle(self.window_title)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addWidget(self.tabbar)


class PrintPreviewDialog(QPrintPreviewDialog):
    """Adds Mouse wheel functionality"""

    def __init__(self, printer: QPrinter):
        """
        :param printer: Target printer

        """

        super().__init__(printer)
        self.toolbar = self.findChildren(QToolBar)[0]
        self.actions = self.toolbar.actions()
        self.widget = self.findChildren(QPrintPreviewWidget)[0]
        self.combo_zoom = self.toolbar.widgetForAction(self.actions[3])

    def wheelEvent(self, event: QWheelEvent):
        """Overrides mouse wheel event handler

        :param event: Mouse wheel event

        """

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                zoom_factor = self.widget.zoomFactor() / 1.1
            else:
                zoom_factor = self.widget.zoomFactor() * 1.1
            self.widget.setZoomFactor(zoom_factor)
            self.combo_zoom.setCurrentText(str(round(zoom_factor*100, 1))+"%")
        else:
            super().wheelEvent(event)
