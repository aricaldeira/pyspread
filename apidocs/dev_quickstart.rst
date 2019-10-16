Dev Quick Start
====================

Below are quick tips+hints of how it runs the plumbing kinda works ;-)

Fundamental is python3 and PyQt5 'bindings', so widget documentation is https://doc.qt.io/qt-5/qt5-intro.html

The gui
-----------

The app starts with  :class:`pyspread.MainWindow`.

* It is also passed down to other widgets for callback.
* upon startup the main windows call a set of `_init_*` functions eg

    * :class:`~pyspread.MainWindow._init_toolbars`.
    * :class:`~pyspread.MainWindow._init_toolbars`.

The :mod:`actions` module defines a set of :class:`actions.Action` a subclass of `QAction`

the icons are in Icons





