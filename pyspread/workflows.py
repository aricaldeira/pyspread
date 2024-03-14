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

Workflows for pyspread

"""

from ast import literal_eval
from base64 import b85encode
import bz2
from contextlib import contextmanager
from copy import copy
import csv
import io
import numpy
import os.path
from pathlib import Path
from shutil import move
from tempfile import NamedTemporaryFile
from typing import Iterable, Tuple

from PyQt6.QtCore import (Qt, QMimeData, QModelIndex, QBuffer, QRect, QRectF,
                          QItemSelectionModel, QSize)
from PyQt6.QtGui import QTextDocument, QImage, QPainter, QUndoCommand
from PyQt6.QtWidgets import (QApplication, QMessageBox, QInputDialog,
                             QStyleOptionViewItem, QTableView)
try:
    from PyQt6.QtSvg import QSvgGenerator
except ImportError:
    QSvgGenerator = None

try:
    import matplotlib
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib = None
    matplotlib_figure = None

try:
    from pyspread import commands
    from pyspread.dialogs \
        import (DiscardChangesDialog, FileOpenDialog, GridShapeDialog,
                FileSaveDialog, ImageFileOpenDialog, ChartDialog,
                CellKeyDialog, FindDialog, ReplaceDialog, CsvFileImportDialog,
                CsvImportDialog, CsvExportDialog, CsvExportAreaDialog,
                FileExportDialog, SvgExportAreaDialog, SinglePageArea)
    from pyspread.interfaces.pys import PysReader, PysWriter
    from pyspread.lib.attrdict import AttrDict
    from pyspread.lib.hashing import sign, verify
    from pyspread.lib.selection import Selection
    from pyspread.lib.typechecks import is_svg, check_shape_validity
    from pyspread.lib.csv import csv_reader, convert
    from pyspread.lib.file_helpers import \
        (linecount, file_progress_gen, ProgressDialogCanceled)
    from pyspread.model.model import CellAttribute
    from pyspread.formatting import class_format_functions
except ImportError:
    import commands
    from dialogs \
        import (DiscardChangesDialog, FileOpenDialog, GridShapeDialog,
                FileSaveDialog, ImageFileOpenDialog, ChartDialog,
                CellKeyDialog, FindDialog, ReplaceDialog, CsvFileImportDialog,
                CsvImportDialog, CsvExportDialog, CsvExportAreaDialog,
                FileExportDialog, SvgExportAreaDialog, SinglePageArea)
    from interfaces.pys import PysReader, PysWriter
    from lib.attrdict import AttrDict
    from lib.hashing import sign, verify
    from lib.selection import Selection
    from lib.typechecks import is_svg, check_shape_validity
    from lib.csv import csv_reader, convert
    from lib.file_helpers import \
        (linecount, file_progress_gen, ProgressDialogCanceled)
    from model.model import CellAttribute
    from formatting import class_format_functions


class Workflows:
    """Workflow container class"""

    cell2dialog = {}  # Stores acrive chart dialogs

    def __init__(self, main_window):
        self.main_window = main_window

    @contextmanager
    def busy_cursor(self):
        """:class:`~contextlib.contextmanager` that displays a busy cursor"""

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        yield
        QApplication.restoreOverrideCursor()

    @contextmanager
    def prevent_updates(self):
        """:class:`~contextlib.contextmanager` sets the prevent_updates state

        The prevent_updates state prevents updates in main_window.grid.setData

        """

        self.main_window.prevent_updates = True
        yield
        self.main_window.prevent_updates = False

    def handle_changed_since_save(func, *args, **kwargs):
        """Decorator to handle changes since last saving the document

        If changes are present then a dialog is displayed that asks if the
        changes shall be discarded.

        - If the user selects `Cancel` then `func` is not executed.
        - If the user selects `Save` then the file is saved and `func` is
          executed.
        - If the user selects `Discard` then the file is not saved and `func`
          is executed.

        If no changes are present then `func` is directly executed.
        After executing `func`, :func:`reset_changed_since_save` and
        `update_main_window_title` are called.

        """

        def function_wrapper(self, *args, **kwargs):
            """Check changes and display and handle the dialog"""

            if self.main_window.settings.changed_since_save:
                choice = DiscardChangesDialog(self.main_window).choice
                if choice is None:
                    return
                if not choice:
                    # We try to save to a file
                    if self.file_save() is False:
                        # File could not be saved --> Abort
                        return
            try:
                func(self, *args, **kwargs)
            except TypeError:
                func(self)  # No args accepted
            self.reset_changed_since_save()
            self.update_main_window_title()

        return function_wrapper

    def reset_changed_since_save(self):
        """Sets changed_since_save to False and updates the window title"""

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

    def update_main_window_title(self):
        """Change the main window title to reflect the current file name"""

        # Get the current filepath
        filepath = self.main_window.settings.last_file_input_path
        if filepath == Path.home():
            title = "pyspread"
        else:
            title = f"{filepath.name} - pyspread"
        self.main_window.setWindowTitle(title)

    @handle_changed_since_save
    def file_new(self):
        """File new workflow"""

        # Get grid shape from user
        old_shape = self.main_window.grid.model.code_array.shape
        shape = GridShapeDialog(self.main_window, old_shape).shape

        # Check if shape is valid

        if shape is None:
            return

        try:
            check_shape_validity(shape, self.main_window.settings.maxshape)
        except ValueError as err:
            self.main_window.statusBar().showMessage('Error: ' + str(err))
            return

        # Set current cell to upper left corner
        for grid in self.main_window.grids:
            grid.current = 0, 0, 0
            # Select upper left cell because initial selection behaves strange
            grid.reset_selection()

        # Reset grid
        self.main_window.grid.model.reset()

        # Empty undo stack
        self.main_window.undo_stack.clear()

        # Delete old filepath
        self.main_window.settings.last_file_input_path = Path.home()

        # Set new shape
        self.main_window.grid.model.shape = shape

        # Update cell spans and zoom because this is unsupported by the model
        for grid in self.main_window.grids:
            with grid.undo_resizing_row():
                with grid.undo_resizing_column():
                    grid.update_cell_spans()
                    grid.update_zoom()

            # Update index widgets
            grid.update_index_widgets()

        # Set current cell to upper left corner
        for grid in self.main_window.grids:
            grid.current = 0, 0, 0

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Update macro editor
        self.main_window.macro_panel.update()

        # Exit safe mode
        self.main_window.safe_mode = False

    def count_file_lines(self, filepath: Path):
        """Returns line count of file in filepath

        :param filepath: Path of file to be analyzed

        """

        try:
            with open(filepath, 'rb') as infile:
                return linecount(infile)
        except OSError as error:
            self.main_window.statusBar().showMessage(str(error))
            return

    def filepath_open(self, filepath: Path):
        """Workflow for opening a file if a filepath is known

        :param filepath: Path of file to be opened

        """

        grid = self.main_window.grid
        code_array = grid.model.code_array

        # Get number of lines for progress dialog
        filelines = self.count_file_lines(filepath)
        if not filelines:  # May not be None or 0
            return

        # Reset grid
        grid.model.reset()

        # Empty undo stack
        self.main_window.undo_stack.clear()

        # Reset macro editor
        self.main_window.macro_panel.macro_editor.clear()

        # Is the file signed properly ?
        self.main_window.safe_mode = True
        signature_key = self.main_window.settings.signature_key
        try:
            with open(filepath, "rb") as infile:
                signature_path = filepath.with_suffix(filepath.suffix + '.sig')
                with open(signature_path, "rb") as sigfile:
                    self.main_window.safe_mode = not verify(infile.read(),
                                                            sigfile.read(),
                                                            signature_key)
        except OSError:
            self.main_window.safe_mode = True

        # File format handling
        if filepath.suffix == ".pysu":
            fopen = open
        else:
            fopen = bz2.open

        # Process events before showing the modal progress dialog
        QApplication.instance().processEvents()

        # Change into file directory
        os.chdir(filepath.parent)

        # Load file into grid
        title = "File open progress"
        label = f"Opening {filepath.name}..."

        try:
            with fopen(filepath, "rb") as infile:
                reader = PysReader(infile, code_array)
                try:
                    for i, _ in file_progress_gen(self.main_window, reader,
                                                  title, label, filelines):
                        pass
                except Exception as error:
                    grid.model.reset()
                    self.main_window.statusBar().showMessage(str(error))
                    self.main_window.safe_mode = False
                    return
                except ProgressDialogCanceled:
                    msg = f"File open stopped by user at line {i}."
                    self.main_window.statusBar().showMessage(msg)
                    grid.model.reset()
                    self.main_window.safe_mode = False
                    return

        except Exception as err:
            # A lot may got wrong with a malformed pys file, includes OSError
            msg_tpl = "Error opening file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)
            self.main_window.statusBar().showMessage(msg)
            # Reset grid
            grid.model.reset()
            self.main_window.safe_mode = False
            return
        # Explicitly set the grid shape
        shape = code_array.shape
        grid.model.shape = shape

        # Update cell spans and zoom because this is unsupported by the model
        for grid in self.main_window.grids:
            with grid.undo_resizing_row():
                with grid.undo_resizing_column():
                    grid.update_cell_spans()
                    grid.update_zoom()

            # Update index widgets
            grid.update_index_widgets()

            grid.model.dataChanged.emit(QModelIndex(), QModelIndex())

            # Select upper left cell because initial selection oddities
            grid.reset_selection()

        # Change the main window last input directory state
        self.main_window.settings.last_file_input_path = filepath
        self.main_window.settings.last_file_output_path = filepath

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Update macro editor
        self.main_window.macro_panel.update()

        # Add to file history
        self.main_window.settings.add_to_file_history(filepath.as_posix())

        # Update recent files in the file menu
        self.main_window.menuBar().file_menu.history_submenu.update()

        return filepath

    @handle_changed_since_save
    def file_open(self):
        """File open workflow"""

        # Get filepath from user
        dial = FileOpenDialog(self.main_window)
        if not dial.file_path:
            return  # Cancel pressed
        filepath = Path(dial.file_path).with_suffix(dial.suffix)

        self.filepath_open(filepath)

    @handle_changed_since_save
    def file_open_recent(self, filepath: Path):
        """File open recent workflow

        :param filepath: Path of file to be opened

        """

        self.filepath_open(Path(filepath))

    def sign_file(self, filepath: Path):
        """Signs filepath if not in :attr:`model.model.DataArray.safe_mode`

        :param filepath: Path of file to be signed

        """

        if self.main_window.safe_mode:
            msg = "File saved but not signed because it is unapproved."
            self.main_window.statusBar().showMessage(msg)
            return

        signature_key = self.main_window.settings.signature_key
        try:
            with open(filepath, "rb") as infile:
                signature = sign(infile.read(), signature_key)
        except OSError as err:
            msg = f"Error signing file: {err}"
            self.main_window.statusBar().showMessage(msg)
            return

        if signature is None or not signature:
            msg = 'Error signing file.'
            self.main_window.statusBar().showMessage(msg)
            return

        signature_path = filepath.with_suffix(filepath.suffix + '.sig')
        try:
            with open(signature_path, 'wb') as signfile:
                signfile.write(signature)
                msg = "File saved and signed."
        except OSError as err:
            msg_tpl = "Error signing file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)

        self.main_window.statusBar().showMessage(msg)

    def _save(self, filepath: Path):
        """Save filepath using chosen_filter

        Compresses save file if filepath.suffix is `.pys`

        :param filepath: Path of file to be saved

        """

        code_array = self.main_window.grid.model.code_array

        # Process events before showing the modal progress dialog
        QApplication.instance().processEvents()

        # Save grid to temporary file

        title = "File save progress"
        label = f"Saving {filepath.name}..."

        with NamedTemporaryFile(delete=False) as tempfile:
            filename = tempfile.name
            try:
                pys_writer = PysWriter(code_array)
                try:
                    for _, line in file_progress_gen(
                            self.main_window, pys_writer, title, label,
                            len(pys_writer)):
                        line = bytes(line, "utf-8")
                        if filepath.suffix == ".pys":
                            line = bz2.compress(line)
                        tempfile.write(line)

                except ProgressDialogCanceled:
                    msg = "File save stopped by user."
                    self.main_window.statusBar().showMessage(msg)
                    tempfile.delete = True  # Delete incomplete tmpfile
                    return False

            except (OSError, ValueError) as err:
                tempfile.delete = True
                QMessageBox.critical(self.main_window, "Error saving file",
                                     str(err))
                return False
        try:
            if filepath.exists() and not os.access(filepath, os.W_OK):
                raise PermissionError(f"No write access to {filepath}")
            move(filename, filepath)

        except OSError as err:
            # No tmp file present
            QMessageBox.critical(self.main_window, "Error saving file",
                                 str(err))
            return False

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Set the current filepath
        self.main_window.settings.last_file_output_path = filepath

        # Change the main window title
        self.main_window.setWindowTitle(f"{filepath.name} - pyspread")

        # Add to file history
        self.main_window.settings.add_to_file_history(filepath.as_posix())

        # Update recent files in the file menu
        self.main_window.menuBar().file_menu.history_submenu.update()

        self.sign_file(filepath)

    def file_save(self):
        """File save workflow"""

        filepath = self.main_window.settings.last_file_output_path
        if filepath.suffix and self._save(filepath) is not False:
            return

        # New, changed file that has never been saved before
        # Now the user has aborted the file save as dialog or
        # there was a write error
        return self.file_save_as()

    def file_save_as(self):
        """File save as workflow"""

        # Get filepath from user
        dial = FileSaveDialog(self.main_window)
        if not dial.file_path:
            return False  # Cancel pressed

        filepath = Path(dial.file_path)

        # Extend filepath suffix if needed
        if filepath.suffix != dial.suffix:
            filepath = filepath.with_suffix(dial.suffix)

        return self._save(filepath)

    def file_import(self):
        """Import csv files"""

        # Get filepath from user
        dial = CsvFileImportDialog(self.main_window)
        if not dial.file_path:
            return  # Cancel pressed
        filepath = Path(dial.file_path)

        self._csv_import(filepath)

    def _csv_import(self, filepath: Path):
        """Import csv from filepath

        :param filepath: Path of file to be imported

        """

        filelines = self.count_file_lines(filepath)
        if not filelines:  # May not be None or 0
            title = "CSV Import Error"
            text = f"File {filepath} seems to be empty."
            QMessageBox.warning(self.main_window, title, text)
            return

        # Store file import path for next time importing a file
        self.main_window.settings.last_file_import_path = filepath

        digest_types = self.main_window.settings.digest_types

        csv_dlg = CsvImportDialog(self.main_window, filepath,
                                  digest_types=digest_types)

        if not csv_dlg.exec():
            return

        self.main_window.settings.digest_types = csv_dlg.digest_types
        dialect = csv_dlg.dialect
        digest_types = csv_dlg.digest_types
        try:
            keep_header = dialect.hasheader and dialect.keepheader
        except AttributeError:
            keep_header = False
        grid = self.main_window.focused_grid
        row, column, _ = current = grid.current
        model = grid.model
        rows, columns, tables = model.shape

        # Dialog accepted, now check if grid is large enough
        csv_rows = filelines
        if dialect.hasheader and not dialect.keepheader:
            csv_rows -= 1
        csv_columns = csv_dlg.csv_table.model.columnCount()
        max_rows, max_columns = self.main_window.settings.maxshape[:2]

        if csv_rows > rows - row or csv_columns > columns - column:
            if csv_rows + row > max_rows or csv_columns + column > max_columns:
                # Required grid size is too large
                text_tpl = "The csv file {} does not fit into the grid.\n " +\
                           "\nIt has {} rows and {} columns. Counting from " +\
                           "the current cell, {} rows and {} columns would " +\
                           "be needed, which exeeds the maximum shape of " +\
                           "{} rows and {} columns. Data that does not fit " +\
                           "inside the grid is discarded.\n \nDo you want " +\
                           "to increase the grid size so that as much data " +\
                           "from the csv file as possible fits in?"
                text = text_tpl.format(filepath, csv_rows, csv_columns,
                                       rows-row, columns-column, max_rows,
                                       max_columns)
            else:
                # Shall we resize the grid?
                text_tpl = \
                    "The csv file {} does not fit into the grid.\n \n" +\
                    "It has {} rows and {} columns. Counting from the " +\
                    "current cell, only {} rows and {} columns remain for " +\
                    "CSV data.\n \nData that does not fit inside the grid " +\
                    "is discarded.\n \nDo you want to increase the grid " +\
                    "size so that all csv file data fits in?"
                text = text_tpl.format(filepath, csv_rows, csv_columns,
                                       rows-row, columns-column)

            title = "CSV Content Exceeds Grid Shape"
            choices = QMessageBox.StandardButton.No \
                | QMessageBox.StandardButton.Yes \
                | QMessageBox.StandardButton.Cancel
            default_choice = QMessageBox.StandardButton.No
            choice = QMessageBox.question(self.main_window, title, text,
                                          choices, default_choice)
            if choice == QMessageBox.StandardButton.Yes:
                # Resize grid
                target_rows = min(max_rows, max(csv_rows + row, rows))
                target_columns = min(max_columns,
                                     max(csv_columns + column, columns))
                self._resize_grid((target_rows, target_columns, tables))
                rows = target_rows
                columns = target_columns

            elif choice == QMessageBox.StandardButton.Cancel:
                return

        # Now fill the grid

        description_tpl = "Import from csv file {} at cell {}"
        description = description_tpl.format(filepath, current)

        command = None

        title = "csv import progress"
        label = f"Importing {filepath.name}..."

        try:
            if hasattr(dialect, "encoding"):
                __encoding = dialect.encoding
            else:
                __encoding = csv_dlg.csv_encoding
            with open(filepath, newline='', encoding=__encoding) as csvfile:
                try:
                    reader = csv_reader(csvfile, dialect)
                    for i, line in file_progress_gen(self.main_window, reader,
                                                     title, label, filelines):
                        if row + i >= rows:
                            break

                        for j, ele in enumerate(line):
                            if column + j >= columns:
                                break

                            if digest_types is None:
                                code = str(ele)
                            elif i == 0 and keep_header:
                                code = repr(ele)
                            else:
                                code = convert(ele, digest_types[j])
                            index = model.index(row + i, column + j)
                            _command = commands.SetCellCode(code, model, index,
                                                            description)
                            try:
                                command.mergeWith(_command)
                            except AttributeError:
                                command = _command

                except (TypeError, ValueError) as error:
                    title = "CSV Import Error"
                    text_tpl = "Error importing csv file {path}.\n \n" + \
                               "{errtype}: {error}"
                    text = text_tpl.format(path=filepath,
                                           errtype=type(error).__name__,
                                           error=error)
                    QMessageBox.warning(self.main_window, title, text)
                    return

                except ProgressDialogCanceled:
                    title = "CSV Import Stopped"
                    text = f"Import stopped by user at line {i}."
                    QMessageBox.warning(self.main_window, title, text)
                    return

        except Exception as error:
            # A lot may go wrong with malformed csv files, includes OSError
            title = "CSV Import Error"
            text_tpl = "Error importing csv file {path}.\n \n" +\
                       "{errtype}: {error}"
            text = text_tpl.format(path=filepath, errtype=type(error).__name__,
                                   error=error)
            QMessageBox.warning(self.main_window, title, text)
            return

        with self.main_window.entry_line.disable_updates():
            with self.busy_cursor():
                with self.prevent_updates():
                    if command is not None:
                        self.main_window.undo_stack.push(command)

    def file_export(self):
        """Export csv and svg files"""

        # Determine what filters ae available
        filters_list = ["CSV (*.csv)", "SVG (*.svg)"]

        grid = self.main_window.focused_grid

        current = grid.current
        code_array = grid.model.code_array

        res = code_array[current]

        if isinstance(res, QImage):
            filters_list.append("JPG of current cell (*.jpg)")

        if isinstance(res, (QImage, matplotlib.figure.Figure)):
            filters_list.append("PNG of current cell (*.png)")

        if isinstance(res, matplotlib.figure.Figure):
            filters_list.append("SVG of current cell (*.svg)")

        # Get filepath from user
        dial = FileExportDialog(self.main_window, filters_list)
        if not dial.file_path:
            return  # Cancel pressed
        filepath = Path(dial.file_path)

        # Store file export path for next time exporting a file
        self.main_window.settings.last_file_export_path = filepath

        if "CSV" in dial.selected_filter:
            self._csv_export(filepath)
            return

        if "SVG" in dial.selected_filter:
            # Extend filepath suffix if needed
            if filepath.suffix != dial.suffix:
                filepath = filepath.with_suffix(dial.suffix)
            self.svg_export(filepath)
            return

        # Extend filepath suffix if needed
        if filepath.suffix != dial.suffix:
            filepath = filepath.with_suffix(dial.suffix)

        if "JPG" in dial.selected_filter:
            if isinstance(res, QImage):
                self._qimage_export(str(filepath), file_format="jpg")

        if "PNG" in dial.selected_filter:
            if isinstance(res, QImage):
                self._qimage_export(str(filepath), file_format="png")
            elif isinstance(res, matplotlib.figure.Figure):
                self._matplotlib_export(filepath, file_format="png")

        elif "SVG" in dial.selected_filter:
            if isinstance(res, matplotlib.figure.Figure):
                self._matplotlib_export(filepath, file_format="svg")

    def _csv_export(self, filepath: Path):
        """Export to csv file filepath

        :param filepath: Path of file to be exported

        """

        grid = self.main_window.focused_grid

        # Get area for csv export
        area = CsvExportAreaDialog(self.main_window, grid,
                                   title="Csv export area").area
        if area is None:
            return

        code_array = grid.model.code_array
        table = grid.table
        csv_data = code_array[area.top: area.bottom + 1,
                              area.left: area.right + 1, table]

        csv_dlg = CsvExportDialog(self.main_window, area)

        if not csv_dlg.exec():
            return

        try:
            with open(filepath, "w", newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, dialect=csv_dlg.dialect)
                writer.writerows(csv_data)
        except OSError as error:
            self.main_window.statusBar().showMessage(str(error))

    def svg_export(self, filepath: Path, svg_area: SinglePageArea = None):
        """Export to svg file filepath

        :param filepath: Path of file to be exported
        :param svg_area: Area of the grid to be exported

        """

        with self.print_zoom():
            grid = self.main_window.grid

            generator = QSvgGenerator()
            generator.setFileName(str(filepath))

            if svg_area is None:
                # Get area for svg export
                svg_area = SvgExportAreaDialog(self.main_window, grid,
                                               title="Svg export area").area
            if svg_area is None:
                return

            self.main_window.print_area = svg_area

            rows = self.get_paint_rows(svg_area.top, svg_area.bottom)
            columns = self.get_paint_columns(svg_area.left, svg_area.right)
            total_height = self.get_total_height(svg_area.top, svg_area.bottom)
            total_width = self.get_total_width(svg_area.left, svg_area.right)

            x_offset = grid.columnViewportPosition(0)
            y_offset = grid.rowViewportPosition(0)

            top_left_idx = grid.model.index(svg_area.top, svg_area.left)
            top_left_visual_rect = grid.visualRect(top_left_idx)

            generator.setSize(QSize(total_width, total_height))
            paint_rect = QRectF(top_left_visual_rect.x() - x_offset,
                                top_left_visual_rect.y() - y_offset,
                                total_width,
                                total_height)
            generator.setViewBox(paint_rect)
            option = QStyleOptionViewItem()

            painter = QPainter(generator)
            self.paint(painter, option, paint_rect, rows, columns)

            painter.end()
            self.main_window.print_area = None

    def _qimage_export(self, filepath: Path, file_format: str):
        """Export to png file filepath

        :param filepath: Path of file to be exported
        :param file_format: File format to be exported, e.g. png

        """

        grid = self.main_window.focused_grid
        code_array = grid.model.code_array
        qimage = code_array[grid.current]

        try:
            if not qimage.save(filepath, file_format):
                msg = f"Could not save {filepath}"
                self.main_window.statusBar().showMessage(msg)
        except Exception as error:
            self.main_window.statusBar().showMessage(str(error))

    def _matplotlib_export(self, filepath: Path, file_format: str):
        """Export to svg file filepath

        :param filepath: Path of file to be exported
        :param file_format: File format to be exported, e.g. png or svg

        """

        if matplotlib is None:
            # matplotlib is not installed
            return

        grid = self.main_window.focused_grid
        code_array = grid.model.code_array
        figure = code_array[grid.current]

        try:
            figure.savefig(filepath, format=file_format)
        except Exception as error:
            self.main_window.statusBar().showMessage(str(error))

    @contextmanager
    def print_zoom(self, zoom: float = 1.0):
        """Decorator for tasks that have to take place in standard zoom

        :param zoom: Print zoom factor

        """

        grid = self.main_window.focused_grid
        __zoom = grid.zoom
        grid.zoom = zoom
        yield
        grid.zoom = __zoom

    def get_paint_rows(self, top: int, bottom: int) -> Iterable[int]:
        """Iterator of rows to paint

        :param top: First row to paint
        :param bottom: Last row to paint

        """

        grid = self.main_window.focused_grid
        rows = grid.model.shape[0]
        top = max(0, min(rows - 1, top))
        bottom = max(0, min(rows - 1, bottom))
        if top == -1:
            top = 0
        if bottom == -1:
            bottom = grid.model.shape[0]

        return range(top, bottom + 1)

    def get_paint_columns(self, left: int, right: int) -> Iterable[int]:
        """Iterator of columns to paint

        :param left: First column to paint
        :param right: Last column to paint

        """

        grid = self.main_window.focused_grid
        columns = grid.model.shape[1]
        left = max(0, min(columns - 1, left))
        right = max(0, min(columns - 1, right))
        if left == -1:
            left = 0
        if right == -1:
            right = grid.model.shape[1]

        return range(left, right + 1)

    def get_paint_tables(self, first: int, last: int) -> Iterable[int]:
        """Iterator of tables to paint

        :param first: First table to paint
        :param last: Last table to paint

        """

        grid = self.main_window.focused_grid
        tables = grid.model.shape[2]
        first = max(0, min(tables - 1, first))
        last = max(0, min(tables - 1, last))
        if first == -1:
            first = 0
        if last == -1:
            last = grid.model.shape[2]

        return range(first, last + 1)

    def get_total_height(self, top: int, bottom: int) -> float:
        """Total height of paint_rows

        :param top: First row to evaluate
        :param bottom: Last row to evaluate

        """

        grid = self.main_window.focused_grid
        rows = self.get_paint_rows(top, bottom)
        return sum(grid.rowHeight(row) for row in rows)

    def get_total_width(self, left: int, right: int) -> float:
        """Total height of paint_columns

        :param left: First column to evaluate
        :param right: Last column to evaluate

        """

        grid = self.main_window.focused_grid
        columns = self.get_paint_columns(left, right)
        return sum(grid.columnWidth(column) for column in columns)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              paint_rect: QRectF, rows: Iterable[int], columns: Iterable[int]):
        """Grid paint workflow for printing and svg export

        :param painter: Painter with which the grid is drawn
        :param option: Style option for rendering
        :param paint_rect: Rectangle, which is drawn at the grid borders
        :param rows: Rows to be painted
        :param columns: Columns to be painted

        """

        grid = self.main_window.focused_grid
        code_array = grid.model.code_array
        cell_attributes = code_array.cell_attributes

        x_offset = grid.columnViewportPosition(0)
        y_offset = grid.rowViewportPosition(0)

        max_width = 0
        max_height = 0

        for row in rows:
            for column in columns:
                key = row, column, grid.table
                merging_cell = cell_attributes.get_merging_cell(key)
                if merging_cell is None \
                   or merging_cell[0] == row and merging_cell[1] == column:

                    idx = grid.model.index(row, column)
                    visual_rect = grid.visualRect(idx)
                    x = max(0, visual_rect.x() - x_offset)
                    y = max(0, visual_rect.y() - y_offset)
                    width = visual_rect.width()
                    if visual_rect.x() - x_offset < 0:
                        width += visual_rect.x() - x_offset
                    height = visual_rect.height()
                    if visual_rect.y() - y_offset < 0:
                        height += visual_rect.y() - y_offset

                    option.rect = QRect(int(x), int(y),
                                        int(width), int(height))
                    option.rectf = QRectF(x, y, width, height)

                    max_width = max(max_width, x + width)
                    max_height = max(max_height, y + height)
                    # painter.setClipRect(option.rectf)

                    option.text = code_array(key)
                    option.widget = grid

                    grid.itemDelegate().paint(painter, option, idx)

    @handle_changed_since_save
    def file_quit(self):
        """Program exit workflow"""

        self.main_window.settings.save()
        QApplication.instance().quit()

    # Edit menu

    def delete(self, description_tpl: str = "Delete selection {}"):
        """Delete cells in selection

        :param description_tpl: Description template for `QUndoCommand`

        """

        grid = self.main_window.focused_grid
        model = grid.model
        selection = grid.selection

        description = description_tpl.format(selection)
        command = commands.DeleteSelectedCellData(grid, model, selection,
                                                  description)
        self.main_window.undo_stack.push(command)

    def edit_cut(self):
        """Edit -> Cut workflow"""

        self.edit_copy()
        self.delete(description_tpl="Cut selection {}")

    def edit_copy(self):
        """Edit -> Copy workflow

        Copies selected grid code to clipboard

        """

        grid = self.main_window.focused_grid
        table = grid.table
        selection = grid.selection
        bbox = selection.get_grid_bbox(grid.model.shape)
        (top, left), (bottom, right) = bbox

        data = []

        for row in range(top, bottom + 1):
            data.append([])
            for column in range(left, right + 1):
                if (row, column) in selection:
                    try:
                        code = grid.model.code_array((row, column, table))
                    except IndexError:
                        code = None
                    if code is None:
                        code = ""
                    code = code.replace("\n", "\u000C")  # Replace LF by FF
                else:
                    code = ""
                data[-1].append(code)

        data_string = "\n".join("\t".join(line) for line in data)

        clipboard = QApplication.clipboard()
        clipboard.setText(data_string)

    def _copy_results_current(self, grid: QTableView):
        """Copy cell results for the current cell

        :param grid: Main grid

        """

        current = grid.current
        data = grid.model.code_array[current]
        if data is None:
            return

        clipboard = QApplication.clipboard()

        # Get renderer for current cell
        renderer = grid.model.code_array.cell_attributes[current].renderer

        if renderer == "text":
            clipboard.setText(grid.model.data(grid.currentIndex()))
            # clipboard.setText(str(data))

        elif renderer == "image":
            if isinstance(data, QImage):
                clipboard.setImage(data)
            else:
                # We may have an svg image here
                try:
                    svg_bytes = bytes(data)
                except TypeError:
                    svg_bytes = bytes(data, encoding='utf-8')
                if is_svg(svg_bytes):
                    mime_data = QMimeData()
                    mime_data.setData("image/svg+xml", svg_bytes)
                    clipboard.setMimeData(mime_data)

        elif renderer == "markup":
            mime_data = QMimeData()
            mime_data.setHtml(str(data))

            # Also copy data as plain text
            doc = QTextDocument()
            doc.setHtml(str(data))
            mime_data.setText(doc.toPlainText())

            clipboard.setMimeData(mime_data)

        elif renderer == "matplotlib" and isinstance(data,
                                                     matplotlib_figure.Figure):
            # We copy and svg to the clipboard
            svg_filelike = io.BytesIO()
            png_filelike = io.BytesIO()
            data.savefig(svg_filelike, format="svg")
            data.savefig(png_filelike, format="png")
            svg_bytes = (svg_filelike.getvalue())
            png_image = QImage().fromData(png_filelike.getvalue())
            mime_data = QMimeData()
            mime_data.setData("image/svg+xml", svg_bytes)
            mime_data.setImageData(png_image)
            clipboard.setMimeData(mime_data)

    def _copy_results_selection(self, grid: QTableView):
        """Copy selected cells result objects to the clipboard

        :param grid: Main grid

        """

        def str_nn(ele):
            """str which returns '' if ele is None"""
            if ele is None:
                return ''

            try:
                if ele.__class__ in class_format_functions:
                    format_function = class_format_functions[ele.__class__]
                    return format_function(ele)

                return str(ele)
            except Exception as err:
                return str(err)

        table = grid.table
        selection = grid.selection
        bbox = selection.get_grid_bbox(grid.model.shape)
        (top, left), (bottom, right) = bbox

        data = grid.model.code_array[top:bottom+1, left:right+1, table]
        data_string = "\n".join("\t".join(map(str_nn, line)) for line in data)

        clipboard = QApplication.clipboard()
        clipboard.setText(data_string)

    def edit_copy_results(self):
        """Edit -> Copy results workflow

        If a selection is present then repr of selected grid cells result
        objects are copied to the clipboard.

        If no selection is present, the current cell results are copied to the
        clipboard. This can be plain text, html, a png image or an svg image.

        """

        grid = self.main_window.focused_grid

        if grid.has_selection():
            self._copy_results_selection(grid)
        else:
            self._copy_results_current(grid)

    def _paste_to_selection(self, selection: Selection, data: str):
        """Pastes data into grid filling the selection

        :param selection: Grid cell selection for pasting
        :param data: Clipboard text

        """

        grid = self.main_window.focused_grid
        model = grid.model
        undo_stack = self.main_window.undo_stack

        description_tpl = "Paste clipboard to {}"
        description = description_tpl.format(selection)

        cmd = commands.PasteSelectedCellData(grid, model, selection, data,
                                             description)
        undo_stack.push(cmd)

    def _paste_to_current(self, data: str):
        """Pastes data into grid starting from the current cell

        :param data: Clipboard text

        """

        grid = self.main_window.focused_grid
        model = grid.model
        top, left, table = current = grid.current
        code_array = grid.model.code_array
        undo_stack = self.main_window.undo_stack

        description_tpl = "Paste clipboard starting from cell {}"
        description = description_tpl.format(current)

        command = None

        paste_gen = (line.split("\t") for line in data.split("\n"))
        for row, line in enumerate(paste_gen):
            paste_row = row + top
            if (paste_row, 0, table) not in code_array:
                break
            for column, value in enumerate(line):
                paste_column = column + left
                if (paste_row, paste_column, table) in code_array:
                    index = model.index(paste_row, paste_column, QModelIndex())
                    # Preserve line breaks
                    value = value.replace("\u000C", "\n")
                    cmd = commands.SetCellCode(value, model, index,
                                               description)
                    if command is None:
                        command = cmd
                    else:
                        command.mergeWith(cmd)
                else:
                    break
        if command is not None:
            undo_stack.push(command)

    def edit_paste(self):
        """Edit -> Paste workflow

        Pastes text clipboard data

        If no selection is present, data is pasted starting with the current
        cell. If a selection is present, data is pasted fully if the selection
        is smaller. If the selection is larger then data is duplicated.

        """

        grid = self.main_window.focused_grid

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        if data:
            # Change the main window filepath state
            self.main_window.settings.changed_since_save = True

            with self.busy_cursor():
                if grid.has_selection():
                    self._paste_to_selection(grid.selection, data)
                else:
                    self._paste_to_current(data)

    def _paste_svg(self, svg: str, index: QModelIndex):
        """Pastes svg image into cell

        :param svg: SVG data
        :param index: Target cell index

        """

        grid = self.main_window.focused_grid

        codelines = svg.splitlines()
        codelines[0] = '"""' + codelines[0]
        codelines[-1] = codelines[-1] + '"""'
        code = "\n".join(codelines)

        model = grid.model
        description = f"Insert svg image into cell {index}"

        grid.on_image_renderer_pressed()
        with self.main_window.entry_line.disable_updates():
            command = commands.SetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)

    def _paste_image(self, image_data: bytes, index: QModelIndex):
        """Pastes svg image into cell

        :param image_data: Raw image data. May be anything that QImage handles.
        :param index: Target cell index

        """

        def gen_chunk(string: str, length: int) -> Iterable[str]:
            """Generator for chunks of string

            :param string: String to be chunked
            :param length: Chunk length

            """

            for i in range(0, len(string), length):
                yield string[i:i+length]

        grid = self.main_window.focused_grid

        repr_image_data = repr(b85encode(bz2.compress(image_data)))
        newline = "'\n+b'"

        image_data_str = newline.join(gen_chunk(repr_image_data, 8000))

        code_lines = [
            "data = bz2.decompress(base64.b85decode(",
            image_data_str,
            "))",
            "qimg = QImage()",
            "QImage.loadFromData(qimg, data)",
            "qimg",
        ]

        code = "\n".join(code_lines)

        model = grid.model
        description = f"Insert image into cell {index}"

        grid.on_image_renderer_pressed()
        with self.main_window.entry_line.disable_updates():
            command = commands.SetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)

    def edit_paste_as(self):
        """Pastes clipboard into one cell using a user specified mime type"""

        grid = self.main_window.focused_grid
        model = grid.model

        # The mimetypes that are supported by pyspread
        mimetypes = ("image", "text/html", "text/plain")
        clipboard = QApplication.clipboard()
        formats = clipboard.mimeData().formats()

        items = [fmt for fmt in formats if any(m in fmt for m in mimetypes)]
        if not items:
            return
        if len(items) == 1:
            item = items[0]
        else:
            item, ok = QInputDialog.getItem(self.main_window, "Paste as",
                                            "Choose mime type", items,
                                            current=0, editable=False)
            if not ok:
                return

        row, column, _ = current = grid.current  # Target cell key

        description_tpl = "Paste {} from clipboard into cell {}"
        description = description_tpl.format(item, current)

        index = model.index(row, column, QModelIndex())

        mime_data = clipboard.mimeData()

        if item == "image/svg+xml":
            # SVG Image
            if mime_data:
                svg = mime_data.data("image/svg+xml")
                self._paste_svg(str(svg, encoding='utf-8'), index)

        elif "image" in item and mime_data.hasImage():
            # Bitmap Image
            image = clipboard.image()
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            image.save(buffer, "PNG")
            buffer.seek(0)
            image_data = buffer.readAll()
            buffer.close()
            self._paste_image(image_data, index)

        elif item == "text/html" and mime_data.hasHtml():
            # HTML content
            html = mime_data.html()
            command = commands.SetCellCode(html, model, index, description)
            self.main_window.undo_stack.push(command)
            grid.on_markup_renderer_pressed()

        elif item == "text/plain":
            # Normal code
            code = clipboard.text()
            if code:
                command = commands.SetCellCode(code, model, index, description)
                self.main_window.undo_stack.push(command)

        else:
            # Unknown mime type
            return NotImplemented

    def edit_find(self):
        """Edit -> Find workflow, opens FindDialog"""

        find_dialog = FindDialog(self.main_window)
        find_dialog.show()
        find_dialog.raise_()
        find_dialog.activateWindow()

    def _get_next_match(self, find_dialog: FindDialog,
                        start_key: Tuple[int, int, int] = None):
        """Returns tuple of find string and next matching cell key

        :param find_dialog: Find dialog from which the search origins
        :param start_key: Start search at given key

        """

        grid = self.main_window.focused_grid
        findnextmatch = grid.model.code_array.findnextmatch

        find_editor = find_dialog.search_text_editor
        find_string = find_editor.text()

        if start_key is not None:
            pass
        elif find_dialog.from_start_checkbox.isChecked():
            start_key = 0, 0, grid.table
        elif find_dialog.backward_checkbox.isChecked():
            start_key = grid.row - 1, grid.column, grid.table
        else:
            start_key = grid.row + 1, grid.column, grid.table

        match = findnextmatch(start_key, find_string,
                              up=find_dialog.backward_checkbox.isChecked(),
                              word=find_dialog.word_checkbox.isChecked(),
                              case=find_dialog.case_checkbox.isChecked(),
                              regexp=find_dialog.regex_checkbox.isChecked(),
                              results=find_dialog.results_checkbox.isChecked())

        return find_string, match

    def _display_match_msg(self, find_string: str, next_match: str,
                           regexp: str):
        """Displays find match message in statusbar

        :param find_string: Message component
        :param next_match: Message component
        :param regexp: Message component

        """

        str_name = "Regular expression" if regexp else "String"
        msg_tpl = "{str_name} {find_string} found in cell {next_match}."
        msg = msg_tpl.format(str_name=str_name,
                             find_string=find_string,
                             next_match=next_match)
        self.main_window.statusBar().showMessage(msg)

    def find_dialog_on_find(self, find_dialog: FindDialog):
        """Edit -> Find workflow, after pressing find button in FindDialog

        :param find_dialog: Find dialog of origin

        """

        grid = self.main_window.focused_grid

        find_string, next_match = self._get_next_match(find_dialog)

        if next_match:
            grid.current = next_match

            regexp = find_dialog.regex_checkbox.isChecked()
            self._display_match_msg(find_string, next_match, regexp)

            if find_dialog.from_start_checkbox.isChecked():
                find_dialog.from_start_checkbox.setChecked(False)

    def edit_find_next(self):
        """Edit -> Find next workflow"""

        grid = self.main_window.focused_grid

        findnextmatch = grid.model.code_array.findnextmatch

        find_editor = self.main_window.find_toolbar.find_editor
        find_string = find_editor.text()

        if find_editor.up:
            start_key = grid.row - 1, grid.column, grid.table
        else:
            start_key = grid.row + 1, grid.column, grid.table

        next_match = findnextmatch(start_key, find_string,
                                   up=find_editor.up,
                                   word=find_editor.word,
                                   case=find_editor.case,
                                   regexp=find_editor.regexp,
                                   results=find_editor.results)
        if next_match:
            grid.current = next_match

            self._display_match_msg(find_string, next_match,
                                    find_editor.regexp)

    def edit_replace(self):
        """Edit -> Replace workflow, opens ReplaceDialog"""

        find_dialog = ReplaceDialog(self.main_window)
        find_dialog.show()
        find_dialog.raise_()
        find_dialog.activateWindow()

    def _get_replace_command(self, next_match: Tuple[int, int, int],
                             find_string: str,
                             replace_string: str,
                             max_: int = 1,
                             description: str = None) -> QUndoCommand:
        """Returns SetCellCode command for replace operations

        :param next_match: Key of next matching cell
        :param find_string: String to find
        :param replace_string: Replacement string
        :param max_: Maximum number of replace actions, -1 is unlimited
        :param description: Forced command description string

        """

        model = self.main_window.focused_grid.model

        old_code = model.code_array(next_match)
        new_code = old_code.replace(find_string, replace_string, max_)

        if description is None:
            description_tpl = "Replaced {old} with {new} in cell {key}."
            description = description_tpl.format(old=old_code, new=new_code,
                                                 key=next_match)
        index = model.index(*next_match[:2])
        return commands.SetCellCode(new_code, model, index, description)

    def replace_dialog_on_replace(self, replace_dialog: ReplaceDialog,
                                  toggled: bool = False,
                                  max_: int = 1) -> bool:
        """Edit -> Replace workflow when pushing Replace in ReplaceDialog

        Returns True if there is a match otherwise False

        :param replace_dialog: Replace dialog of origin
        :param toggled: Replace dialog toggle state
        :param max_: Maximum number of replace actions, -1 is unlimited

        """

        grid = self.main_window.focused_grid

        find_string, next_match = self._get_next_match(replace_dialog)
        replace_string = replace_dialog.replace_text_editor.text()

        if next_match:
            command = self._get_replace_command(next_match, find_string,
                                                replace_string, max_=max_)
            self.main_window.undo_stack.push(command)

            grid.current = next_match

            self.main_window.statusBar().showMessage(command.description)

            if replace_dialog.from_start_checkbox.isChecked():
                replace_dialog.from_start_checkbox.setChecked(False)

            return True

        return False

    def replace_dialog_on_replace_all(self, replace_dialog: ReplaceDialog):
        """Edit -> Replace workflow when pushing ReplaceAll in ReplaceDialog

        :param replace_dialog: Replace dialog of origin

        """

        find_string = replace_dialog.search_text_editor.text()
        replace_string = replace_dialog.replace_text_editor.text()

        word = replace_dialog.word_checkbox.isChecked()
        case = replace_dialog.case_checkbox.isChecked()
        regexp = replace_dialog.regex_checkbox.isChecked()

        command = None

        grid = self.main_window.focused_grid
        code_array = grid.model.code_array
        keys = code_array.keys()

        matches = []

        with self.busy_cursor():
            with self.main_window.entry_line.disable_updates():
                with self.prevent_updates():
                    for key in keys:
                        code = code_array(key)

                        if code_array.string_match(code, find_string, word,
                                                   case, regexp) is not None:
                            matches.append(key)

                    for match in matches:
                        msg = f"Replace all {find_string} by {replace_string}"
                        _command = self._get_replace_command(match,
                                                             find_string,
                                                             replace_string,
                                                             max_=-1,
                                                             description=msg)
                        if command is None:
                            command = _command
                        else:
                            command.mergeWith(_command)

                    if command is not None:
                        self.main_window.undo_stack.push(command)

        msg = f"{find_string} replaced by {replace_string} in {len(matches)} "\
              f"cell{'s' if len(matches) != 1 else ''}."
        self.main_window.statusBar().showMessage(msg)

    def _sort(self, ascending: bool = True):
        """Edit -> Sort ascending

        :param ascending: True for ascending sort, False for descending sort

        """

        grid = self.main_window.focused_grid
        model = grid.model
        table = grid.current[2]
        selection = grid.selection

        (top, left), (bottom, right) = selection.get_bbox()
        if top == bottom:
            return

        data = grid.model.code_array[top:bottom+1, left:right+1, table].copy()
        if ascending:
            data[data == None] = numpy.inf  # `is` does not work here
        else:
            data[data == None] = -numpy.inf  # `is` does not work here

        try:
            if ascending:
                sorted_idx = data[:, grid.current[1]-left].argsort()
            else:
                sorted_idx = data[:, grid.current[1]-left].argsort()[::-1]
        except TypeError as err:
            msg = f"Could not sort selection: {err}"
            self.main_window.statusBar().showMessage(msg)
            return

        old_code = {}
        for key in selection.cell_generator(model.shape, table):
            old_code[key] = grid.model.code_array(key)

        command = None
        if ascending:
            description = f"Sort {grid.selection} ascending"
        else:
            description = f"Sort {grid.selection} descending"

        for row, column in selection.cell_generator(model.shape):
            code = old_code[(sorted_idx[row-top]+top, column, table)]
            index = model.index(row, column)
            _command = commands.SetCellCode(code, model, index, description)
            if command is None:
                command = _command
            else:
                command.mergeWith(_command)

        if command is not None:
            self.main_window.undo_stack.push(command)

        msg = "Selection sorted."
        self.main_window.statusBar().showMessage(msg)

    def edit_sort_ascending(self):
        """Edit -> Sort ascending"""

        self._sort()

    def edit_sort_descending(self):
        """Edit -> Sort descending"""

        self._sort(ascending=False)

    def edit_resize(self):
        """Edit -> Resize workflow"""

        grid = self.main_window.focused_grid

        # Get grid shape from user
        old_shape = grid.model.code_array.shape
        title = "Resize grid"
        shape = GridShapeDialog(self.main_window, old_shape, title=title).shape
        self._resize_grid(shape)

    def _resize_grid(self, shape: Tuple[int, int, int]):
        """Resize grid

        :param shape: New grid shape

        """

        grid = self.main_window.focused_grid

        old_shape = grid.model.code_array.shape

        # Check if shape is valid
        try:
            check_shape_validity(shape, self.main_window.settings.maxshape)
        except ValueError as err:
            self.main_window.statusBar().showMessage('Error: ' + str(err))
            return

        grid.current = 0, 0, 0

        description = f"Resize grid to {shape}"

        with self.main_window.entry_line.disable_updates():
            command = commands.SetGridSize(grid, old_shape, shape, description)
            self.main_window.undo_stack.push(command)

        # Select upper left cell because initial selection behaves strangely
        grid.reset_selection()

    # View menu

    def view_goto_cell(self):
        """View -> Go to cell workflow"""

        grid = self.main_window.focused_grid

        # Get cell key from user
        shape = grid.model.shape
        key = CellKeyDialog(self.main_window, shape).key

        if key is not None:
            grid.current = key

    # Format menu

    def format_copy_format(self):
        """Copies the format of the selected cells to the Clipboard

        Cells are shifted so that the top left bbox corner is at 0,0

        """

        def remove_tabu_keys(attrs: AttrDict):
            """Remove keys that are not copied from attr

            :param attr: Attribute dict that holds cell attributes

            """

            tabu_attrs = "merge_area", "frozen"
            for tabu_attr in tabu_attrs:
                try:
                    attrs.pop(tabu_attr)
                except KeyError:
                    pass

        grid = self.main_window.focused_grid
        code_array = grid.model.code_array
        cell_attributes = code_array.cell_attributes

        # Cell attributes

        new_cell_attributes = []
        selection = grid.selection

        # Format content is shifted so that the top left corner is 0,0
        (top, left), (_, _) = selection.get_grid_bbox(grid.model.shape)

        table_cell_attributes = cell_attributes.for_table(grid.table)
        for __selection, _, attrs in table_cell_attributes:
            new_selection = selection & __selection
            if new_selection:
                # We do not copy merged cells and cell renderers
                __attrs = copy(attrs)
                remove_tabu_keys(__attrs)
                new_shifted_selection = new_selection.shifted(-top, -left)
                if __attrs:
                    cell_attribute = new_shifted_selection.parameters, __attrs
                    new_cell_attributes.append(cell_attribute)

        ca_repr = bytes(repr(new_cell_attributes), encoding='utf-8')

        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        mime_data.setData("application/x-pyspread-cell-attributes", ca_repr)
        clipboard.setMimeData(mime_data)

    def format_paste_format(self):
        """Pastes cell formats

        Pasting starts at cursor or at top left bbox corner

        """

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        grid = self.main_window.focused_grid
        model = grid.model

        row, column, table = grid.current

        if "application/x-pyspread-cell-attributes" not in mime_data.formats():
            return

        cas_data = mime_data.data("application/x-pyspread-cell-attributes")
        cas_data_str = str(cas_data, encoding='utf-8')
        cas = literal_eval(cas_data_str)
        if not isinstance(cas, list):
            msg_tpl = "{} has type {} that is not instance of list"
            msg = msg_tpl.format(cas, type(cas))
            raise Warning(msg)

        tabu_attrs = "merge_area", "frozen"

        description_tpl = "Paste format for selections {}"
        description = description_tpl.format([ca[0] for ca in cas])

        for selection_params, attrs in cas:
            if not any(tabu_attr in attrs for tabu_attr in tabu_attrs):
                selection = Selection(*selection_params)
                shifted_selection = selection.shifted(row, column)
                attr_dict = AttrDict()
                attr_dict.update(attrs)
                new_cell_attribute = CellAttribute(shifted_selection, table,
                                                   attr_dict)
                selected_idx = []
                for key in shifted_selection.cell_generator(model.shape):
                    selected_idx.append(model.index(*key))
                command = commands.SetCellFormat(new_cell_attribute, model,
                                                 grid.currentIndex(),
                                                 selected_idx, description)
                self.main_window.undo_stack.push(command)

    # Macro menufilepath

    def _read_svg_str(self, filepath, encoding):
        """Returns svg string from filepath

        :param filepath: Path of SVG file to read

        """

        try:
            with open(filepath, "r", encoding=encoding) as svgfile:
                return svgfile.read()
        except UnicodeError:
            encoding, ok = QInputDialog().getItem(
                self, f"{filepath} not encoded in utf-8",
                f"Encoding of {filepath}",
                self.main_window.settings.encodings)
            if ok:
                return self._read_svg_str(filepath, encoding)
        except OSError as err:
            msg_tpl = "Error opening file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)
            self.main_window.statusBar().showMessage(msg)

    def macro_insert_image(self):
        """Insert image workflow"""

        grid = self.main_window.focused_grid

        dial = ImageFileOpenDialog(self.main_window)
        if not dial.file_path:
            return  # Cancel pressed

        filepath = Path(dial.file_path)

        index = grid.currentIndex()
        grid.clearSelection()
        grid.selectionModel().select(index,
                                     QItemSelectionModel.SelectionFlag.Select)

        if filepath.suffix == ".svg":
            svg = self._read_svg_str(filepath, encoding='utf-8')
            if not svg:
                return

            self._paste_svg(svg, index)
        else:
            try:
                with open(filepath, "rb") as imgfile:
                    image_data = imgfile.read()
            except OSError as err:
                msg_tpl = "Error opening file {filepath}: {err}."
                msg = msg_tpl.format(filepath=filepath, err=err)
                self.main_window.statusBar().showMessage(msg)
                return
            self._paste_image(image_data, index)

    def macro_insert_chart(self):
        """Insert chart workflow"""

        grid = self.main_window.focused_grid

        model = grid.model
        code_array = model.code_array
        current = grid.current
        code = code_array(current)

        if current in self.cell2dialog:
            self.cell2dialog[current].activateWindow()
            self.cell2dialog[current].setFocus()
            return

        chart_dialog = ChartDialog(self.main_window, current)
        self.cell2dialog[current] = chart_dialog

        chart_dialog.show()

        if code is not None:
            chart_dialog.editor.setPlainText(code)

        if chart_dialog.exec() == ChartDialog.DialogCode.Accepted:
            code = chart_dialog.editor.toPlainText()
            grid.current = current
            index = grid.currentIndex()
            grid.clearSelection()
            grid.selectionModel().select(
                index, QItemSelectionModel.SelectionFlag.Select)
            grid.on_matplotlib_renderer_pressed()

            description = f"Insert chart into cell {index}"
            command = commands.SetCellCode(code, model, index, description)

            self.main_window.undo_stack.push(command)

        self.cell2dialog.pop(current)

    def macro_insert_sum(self):
        """Sum up selection area

        The sum is inserted into the cell below the bottom right cell of the
        selection.

        """

        grid = self.main_window.focused_grid
        selection = grid.selection
        shape = grid.model.shape

        (top, left), (bottom, right) = selection.get_grid_bbox(shape)

        if bottom >= shape[0] - 1:
            self.main_window.statusBar().showMessage(
                "ValueError: Target cell is beyond grid limits")
            return

        key = bottom + 1, right, grid.table

        code = f"numpy.sum(eval({repr(selection)}" + \
               f".get_absolute_access_string({shape}, Z)))"

        grid.current = key
        index = grid.currentIndex()
        description = f"Insert sum of {selection} into cell {key}"
        command = commands.SetCellCode(code, grid.model, index, description)

        self.main_window.undo_stack.push(command)
