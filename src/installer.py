# -*- coding: utf-8 -*-

from dataclasses import dataclass
import importlib
import os
from pkg_resources import get_distribution, DistributionNotFound

from PyQt5 import QtWidgets, QtGui, QtCore


@dataclass
class Module:
    name: str
    description: str
    required_version: str  # The minimum version number that is required

    @property
    def version(self) -> str:
        """Currently installed version number, False if not installed"""

        try:
            return get_distribution(self.name).version
        except DistributionNotFound:
            return False

    @property
    def is_installed(self) -> bool:
        """True if the module is installed"""

        return bool(self.version)

# The required dependencies numpy and pyqt5 are not mentioned because
#  pyspread does not launch without them.

# Optional dependencies
# ---------------------


OPTIONAL_DEPENDENCIES = [
    Module(name="matplotlib",
           description="Create charts",
           required_version="1.1.1"),
    Module(name="xlrd",
           description="Load Excel files",
           required_version="0.9.2"),
    Module(name="xlwt",
           description="Save Excel files",
           required_version="0.9.2"),
    Module(name="pyenchant",
           description="Spell checker",
           required_version="1.1"),
]




PY_PACKAGES = (
    ("xlrd", ">=0.9.2", "loading excel files"),
    ("xlwt", ">=0.9.2", "saving excel files"),
    ("jedi", "(>=0.8.0", "for tab completion and context help in the entry line"),
    ("pyrsvg", ">=2.32", "displaying SVG files in cells"),
    ("pyenchant", ">=1.1",  "spell checking"),
    ("basemap", ">=1.0.7", "for the weather example pys file"),
)




def is_lib_installed(name):
    """Attempts to import lib
    :param name: Lib to load eg xwrd"""
    try:
        importlib.import_module(name)
        return True
    except Exception as e:
        print(e)
        pass
    return False

class InstallerDialog(QtWidgets.QDialog):
    """Installer dialog for python dependencies"""

    class C:
        """Column nos"""
        button = 0
        status = 1
        package = 2
        version = 3
        description = 4

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Installer")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        ## Button group for install buttons
        self.buttGroup = QtWidgets.QButtonGroup()
        self.buttGroup.buttonClicked.connect(self.on_butt_install)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10,10,10,10)
        self.setLayout(self.mainLayout)

        self.tree = QtWidgets.QTreeWidget()
        self.mainLayout.addWidget(self.tree, 4)

        self.tree.setHeaderLabels(["","Status", "Package", "Version", "Description"])
        self.tree.setRootIsDecorated(False)
        #self.tree.setSelectionMode(NoSelection ?)

        self.update_load()

    def update_load(self):

        C = self.C
        self.tree.clear()

        for idx, package in enumerate(PY_PACKAGES):
            pkg, ver, desc = package

            item = QtWidgets.QTreeWidgetItem()
            item.setText(C.package, pkg)
            item.setText(C.version, ver)
            item.setText(C.description, desc)
            self.tree.addTopLevelItem(item)

            if not is_lib_installed(pkg):
                status = "Not installed"
                color = "#F3FFBB"
                butt = QtWidgets.QToolButton()
                butt.setText("Install")
                self.tree.setItemWidget(item, C.button, butt)
                self.buttGroup.addButton(butt, idx)
            else:
                color = "#DBFEAC"
                status = "Installed"

            item.setText(C.status, status)
            item.setBackground(C.status, QtGui.QColor(color))


    def on_butt_install(self, butt):
        """One of install buttons pressed"""

        butt.setDisabled(True)
        idx = self.buttGroup.id(butt)

        dial = InstallPackageDialog(self, package=PY_PACKAGES[idx])
        dial.exec_()
        self.update_load()




class InstallPackageDialog(QtWidgets.QDialog):
    """Shows a dialog to execute command"""

    def __init__(self, parent=None, package=None):
        super().__init__(parent)

        self.package = package

        self.setWindowTitle("Install Package")
        self.setMinimumWidth(600)



        self.process = QtCore.QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_read_standard)
        self.process.readyReadStandardError.connect(self.on_read_error)
        self.process.finished.connect(self.on_finished)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10,10,10,10)
        self.setLayout(self.mainLayout)

        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setTitle("Shell Command")
        self.groupBoxLayout = QtWidgets.QHBoxLayout()
        self.groupBox.setLayout(self.groupBoxLayout)
        self.mainLayout.addWidget(self.groupBox)

        self.buttSudo = QtWidgets.QCheckBox()
        self.buttSudo.setText("sudo")
        self.groupBoxLayout.addWidget(self.buttSudo, 0)
        self.buttSudo.toggled.connect(self.update_cmd_line)
        self.buttSudo.setVisible(os.name != "nt")

        self.txtCommand = QtWidgets.QLineEdit()
        self.groupBoxLayout.addWidget(self.txtCommand, 10)

        self.buttExecute = QtWidgets.QPushButton()
        self.buttExecute.setText("Execute")
        self.groupBoxLayout.addWidget(self.buttExecute, 0)
        self.buttExecute.clicked.connect(self.on_butt_execute)

        self.txtStdOut = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdOut)

        self.txtStdErr = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdErr)

        self.update_cmd_line()

    def update_cmd_line(self, *unused):


        pkg = self.package[0]

        ## Umm ?? sudo, virtual env ??
        # its gonna be > pip3 install foo ?
        cmd = ""
        if self.buttSudo.isChecked():
            cmd += "pkexec  "

        cmd += "pip3 install %s" % pkg

        self.txtCommand.setText(cmd)

    def on_butt_execute(self):
        self.buttSudo.setDisabled(True)
        self.buttExecute.setDisabled(True)

        self.txtStdOut.setPlainText("")
        self.txtStdErr.setPlainText("")
        self.process.start(self.txtCommand.text())

    def on_read_standard(self):
        c = str(self.txtStdOut.toPlainText())
        s = str(self.process.readAllStandardOutput())

        ss = c + "\n-------------------------------------------------------\n" + s
        self.txtStdOut.setPlainText(ss)
        self.txtStdOut.moveCursor(QtGui.QTextCursor.End)

    def on_read_error(self):
        c = str(self.txtStdErr.toPlainText())
        s = str(self.process.readAllStandardError())

        ss = c + "\n-------------------------------------------------------\n" + s
        self.txtStdErr.setPlainText(ss)
        self.txtStdErr.moveCursor(QtGui.QTextCursor.End)

    def on_finished(self):
        self.buttSudo.setDisabled(False)
        self.buttExecute.setDisabled(False)

