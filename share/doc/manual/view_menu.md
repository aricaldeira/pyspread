---
layout: default
section: manual
parent: ../
title: View actions
---


##### -> Fullscreen

Toggles fullscreen mode, in which only the grid is visible on the screen. In fullscreen mode, the mouse wheel changes tables as if the mouse were in the table selection widget right to the entry line. `<F11>` acts as shortcut to the fullscreen mode toggle.

##### -> Toolbars

Toolbars contains a sub menu, in which the different toolbars can be switched on or off.

##### -> Entry line

Swiches the entry line on and off.

##### -> Macro panel

Swiches the macro panel on and off.

##### -> Go to cell

**`Go to cell`** opens a dialog, in which a cell can be specified via row, column and table. After pressing o.k., the specified cell becomes the current cell, and it is put into view on the grid. This involves switching to another grid table if necessary.

##### -> Toggle spell checker

Activates the spell checker for pyspread >=1.1 if pyenchant is installed. Code in the entry lineis checked in the English language. Words that are unknown are marked with a red curly underline.

##### -> Zoom in

Zoom the grid in.

##### -> Zoom out

Zoom the grid out.

##### -> Original size

Reset the grid zoom level to 100%.

##### -> Refresh selected cells

Executes code of cells that are selected and frozen and updates their cell results in the grid. If no cell is selected then the current cell is refreshed. The shortcut for is `<F5>`.

This action has only effects on cells that are frozen.

##### -> Toggle periodic updates

Periodically executes code of cells that are frozen and updates their cell results in the grid. The period can be adjusted in the [Preferences dialog](file_menu.html#--preferences): Set the desired period as “Frozen cells refresh period” in milliseconds.

##### -> Show frozen

Toggles display of a diagonal blue stripe pattern on the background of each frozen cell.
