# -*- coding: utf-8 -*-


import importlib

from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5 import QtWidgets

from icons import Icon


PY_EXTRAS = (
    ["xlrd", ">=0.9.2", "loading excel files"],
    ["xlwt", ">=0.9.2", "saving excel files"],
    ["jedi", "(>=0.8.0", "for tab completion and context help in the entry line"],
    ["pyrsvg", ">=2.32", "displaying SVG files in cells"],
    ["pyenchant", ">=1.1",  "spell checking"],
    ["basemap", ">=1.0.7", "for the weather example pys file"],
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
    """Installer dialog"""

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

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.tree = QtWidgets.QTreeWidget()
        self.mainLayout.addWidget(self.tree, 4)

        self.tree.setHeaderLabels(["","Status", "Package", "Version", "Description"])
        self.tree.setRootIsDecorated(False)
        #self.tree.setSelectionMode()

        self.buttGroup = QtWidgets.QButtonGroup()
        self.buttGroup.buttonClicked.connect(self.on_button)

        self.load()

    def load(self):

        C = self.C
        self.tree.clear()

        for idx, package in enumerate(PY_EXTRAS):
            pkg, ver, desc = package

            item = QtWidgets.QTreeWidgetItem()
            item.setText(C.package, pkg)
            item.setText(C.version, ver)
            item.setText(C.description, desc)
            self.tree.addTopLevelItem(item)

            if not is_lib_installed(pkg):
                item.setText(C.status, "Not installed")
                butt = QtWidgets.QToolButton()
                butt.setText("Install")
                self.tree.setItemWidget(item, C.button, butt)
                self.buttGroup.addButton(butt, idx)
            else:
                item.setText(C.status, "Installed")


    def on_button(self, butt):

        idx = self.buttGroup.id(butt)

        pkg, ver, desc  = PY_EXTRAS[idx]

        print("Install: %s" % pkg)
        ## Umm ?? sudo, virtual env ??
        # its gonna be > pip3 install foo ?
        cmd = "pip3 install %s" % pkg




