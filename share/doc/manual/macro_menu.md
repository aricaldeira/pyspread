---
layout: default
section: manual
parent: ../
title: Macro actions
---


##### -> Insert image

The **`Insert bitmap`** option in the Macros menu lets the user choose an image file and creates cell code that represents an image and chooses the image cell renderer.

##### -> Insert chart

The **`Macros -> Insert chart...`** option provides an easy way of generating
matplotlib figures. They generate multi-line code. The last line is an expression that yields a `matplotlib.figure.Figure` object.

<img class="img-fluid" src="../images/screenshot_chartdialog.png">

The dialog comprises a toolbar with several chart types, an editor on the left and a chart preview on the right side.

Clicking on a chart button inserts code for the respective chart at the current cursor position. The code is meant as template for users, who want to quickly create and edit common chart types. However, any matplotlib chart can be created in the editor.

The preview is updated when pressing the `Apply` button. If an exception occurs of if no Figure object could be retrieved then an error message is displayed.

Pressing the `Ok` button puts the code in the editor in the current cell and activates the matplotlib renderer.
