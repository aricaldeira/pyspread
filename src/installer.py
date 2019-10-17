

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


class InstallerDialog(QtWidgets.QDialog):
    """Installer dialog

    """

    class C:
        button = 0
        package = 1
        version = 2
        description = 3

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Installer")
        self.setMinimumWidth(600)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)



        self.tree = QtWidgets.QTreeWidget()
        self.mainLayout.addWidget(self.tree, 4)

        self.tree.setHeaderLabels(["", "Package", "Version", "Description"])
        self.tree.setRootIsDecorated(False)
        #self.tree.setSelectionMode()

        self.load()

    def load(self):

        C = self.C
        self.tree.clear()
        for pkg, ver, desc in PY_EXTRAS:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(C.package, pkg)
            item.setText(C.version, ver)
            item.setText(C.description, desc)
            self.tree.addTopLevelItem(item)

            # TODO check if installed and version installed
            butt = QtWidgets.QToolButton()
            butt.setAutoRaise(True)
            butt.setText("Install")
            self.tree.setItemWidget(item, C.button, butt)


