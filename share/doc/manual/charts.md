---
layout: default
section: manual
parent: ../
title: Charts
---


- [Overview](#overview)
- [Colors](#colors)
- [Plot Chart](#plot-chart)
- [Bar Chart](#bar-chart)
- [Box Plot](#box-plot)
- [Chart Annotation](#chart-annotation)
- [Contour Chart](#contour-chart)
- [Sankey Diagram](#sankey-diagram)


## Overview

Since version 0.2.3, *pyspread* can generate matplotlib charts. Each cell which
yields a *matplotlib figure* displays the figure as a bitmap and
is stretched to the cell’s extents.

The **`Macros -> Insert chart...`** option provides an easy way of generating
matplotlib figures. They generate code of a special class `charts.ChartFigure` that is provided.
This class subclasses the matplotlib Figure class. The subclass takes
matplotlib arguments and creates a figure in one step. The dialog
creates the code for doing that. It also parses any code
starting with charts.ChartFigure and figures out, which choice had
been made last time. This may very well fail if you changed the cell code manually. For
further reference, the [matplotlib web site](https://matplotlib.org/users/index.html) is recommended.

**Note:** Cells display all types of matplotlib figures. The chart
dialog just provides a convenient user to create and edit common chart types.

Since version 0.4, six chart types are supported by the
chart dialog: Plots, i.e. line charts, bar charts, histograms, box plots, pie charts and
annotations. Note that pie charts cannot be combined with other chart type yet. Please suggest
other chart types that you find usable by posting at the issue tracker.

<img class="img-fluid" src="../images/screenshot_chartdialog.png">

The chart dialog is designed as a fast to use graphical front-end for common matplotlib properties. Attributes
correspond to matplotlib function properties. Each property is described in tooltips. The chart dialog consists
of three parts (from left to right):
- the Axes panel
- the Series panel
- Chart preview panel.

### Axes Panel

The Axes panel allows changing X and Y axes attributes. Other axes types such as Z axis in 3D charts are
not supported by the chart dialog. The axes panel is structured into three sections: Axes, X-Axis and Y-Axis.

In the first box, overall figure attributes can be set, which is title text, the title text font and color and
id a legend is drawn. The text entry field for the title text accepts Python expressions, i.e. if you want
a specific string to be displayed as the title, you have to quote the text. However, if you want a certain global
variable of cell content to be displayed then you can enter the object name. Functions and operators are also
allowed as long as they return a string or unicode like object. Note that this applies for all
fields of the chart dialog unless otherwise specified.

In the second box, X-axis attributes are specified. The X-axis label is provided again as a Python expression. Font
and color can be specified. Next, X-axis scaling can be set to linear (no check) or logarithmic (check), and
the X-axis grid can be turned on and off. If the X-axis shall display a date instead of values and if
a datetime.date object is provided as input for the x-axis values then the date format field should be filled
with a strftime format string. Details about the format string are given in the tooltip. The ticks field accepts a
list or a tuple of numbers or floats. At these locations, axis ticks are set when specified. If left empty, axis
ticks are set automatically. The label field lets the user specify arbitrary text as label at a tick. Font and
color of the labels can be specified here. The secondary ticks option allows ticks to be displayed on the
opposide side of the chart, i.e. on the top as at the bottom. The outside, inside, both choice specifies, where the
ticks are situated at the axis. Padding allows setting the distance between label text and axis. Size lets the user
specify text size if no explicit labels are given in the labels field.

In the third box, Y-axis attributes are specified. Attributes match those of the X-axis both
in content and format with the exception of the date format field, which is not available for the Y-axis.

### Series Panel

The Series panel allows adding one or more series to the axes. In order to add a new series, click on the + tab at
the bottom of the panel. A series is deleted with the x right of the tabs. You can switch between series by
clicking on the respective tabs.

Each data series can be of a specific type that is chosen from the list that is on the left side of the Series
panel. In version 1.0.3 there are eight series types: plot, bar, hist, boxplot, pie, annotate, contour and Sankey. Note
that the series type names correspond to the respective matplotlib names. Other types of matplotlib series
are not supported in the chart dialog. If such a need arises please post an e-mail to the issue tracker.

## Colors

Colors below are expressed with the following:

- `b` - black
- `g` - green
- `r` - red
- `c` - cyan
- `m` - magenta
- `y` - yellow
- `k` - black
- `w` - white
- a floating point number between 0.0 and 1.0 for gray values or an htm hex string such as `#a36271`.


## Plot chart

<img class="img-fluid" src="../images/screenshot-chartdialog-plot.png">


When the plot chart type is selected then on the right panel, Data, Line and Marker boxes are displayed.

In the Data box, a data label can be specified that appears in the legend if it is activated. The X field
is optional. It has to be an iterable of the same length of Y and allows specifying the X values of each
data point. In the Y field, Y values of each point are specified in an iterable.

In the Line box, the line style chosen from solid, dashed, dash-dotted and frozen. Its width can be specified
in points (integer values only) as well as its color.

In the Marker box, the marker style for the actual data points may be chosen from a range of 22 styles. The marker
size can be specified (integer values only) as well as its face and egde colors. The marker alpha value is set
with a floating point value, where 1.0 is solid and 0.0 is fully transparent.


## Bar chart

<img class="img-fluid" src="../images/screenshot-chartdialog-bar.png">

When the bar chart type is selected then on the right panel, Data and Bar boxes are displayed.

In the Data box, a data label can be specified that appears in the legend if it is activated. The left positions
field is mandatory. It expects an iterable of left bar values that is as long as the bar heights iterable that
defines the upper limits of the bars (not the bar lengths). The bar widths field expects either a number that applies
to all bars or an iterable so that specific bars may have different widths. The bar bottoms field is optional and
defines the lower limit of the bars. Similarly to the widths field, it allows entering a number or an iterable.

In the Bar box, the bar fill and edge color can be chosen. Furthermore, an alpha value can be specified with a floating
point value, where 1.0 is solid and 0.0 is fully transparent.

Note that while bar charts may be morte difficult to use than plot charts, they can be used in order to plot arbitrary
rectangles, which makes them also applicable for example to plot simple top down views on room layouts.

## Histogram

<img class="img-fluid" src="../images/screenshot-chartdialog-hist.png">

When the histogram chart type is selected then on the right panel, Data and Histogram boxes are displayed.

In the Data box, a data label can be specified that appears in the legend if it is activated. The data series that
has to be provided is an iterable of numerical values. Categorical values are not supported here
because this is not supported by matplotlib. Value tuples are also not supported.

In the Histogram box, the number of bin can be specified as an integer value. If Normed is checked then the integral
of the histogram will sum to:

If stacked is also True, the sum of the histograms is normalized to 1. If culumative is checked then then a histogram
is computed where each bin gives the counts in that bin plus all bins for smaller values. The last bin gives the total
number of datapoints. Furthermore, the histogram bar color can be set. The alpha value can be specified with a floating
point value, where 1.0 is solid and 0.0 is fully transparent.


## Box Plot

<img class="img-fluid" src="../images/screenshot-chartdialog-boxplot.png">

When the boxplot chart type is selected then on the right panel, Data and Box plot boxes are displayed.

In the Data box, a sequence of numerical values or a sequence of sequences can be provided. In the latter case, multiple
boxplots are combined in one diagram.

In the Box plot box, the box width can be specified as a floatig point value. If vertical is checked then the
boxplots are frawn vertical else horizontal. Flier symbols may be chosen from 22 choices. If notch is checked
then the main box shows a notch at the median value.



## Pie Chart

<img class="img-fluid" src="../images/screenshot-chartdialog-piechart.png">

When the pie chart type is selected then on the right panel, Data and Pie boxes are displayed.

In the Data box, a sequence of numerical values can be provided.

In the Pie box, labels for the wedges can be specified as a sequence of objects (e.g. strings). Wedge colors
are provided in the Colors text box as sequence of strings, where colors can be the strings
- `b` - black
- `g` - green
- `r` - red
- `c` - cyan
- `m` - magenta
- `y` - yellow
- `k` - black
- `w` - white
- a floating point number between 0.0 and 1.0 for gray values or an htm hex string such as `#a36271`.

The pie chart can be rotated with the angle value, which may be a positive or negative integer. The checkbox shadow
enables or disables a shadow behind the pie chart.




## Chart Annotation

<img class="img-fluid" src="../images/screenshot-chartdialog-annotation.png">

When the annotation chart type is selected then on the right panel, an Annotation box is displayed. There, a text
can be entered as a string along with a 2-tuple of coordinates. In a choice box, information, what these coordinates
refer to, is given. Annotations mostly make sense as an additional figure layer.



## Contour Chart

<img class="img-fluid" src="../images/screenshot-chartdialog-contour.png">

When the contour chart type is selected then on the right panel, Data and Lines, Areas and Labels boxes are displayed.

In the Data box, x and y values form a mesh for which z values are specified. Note that z must be a one-time
nested list. For optimizing performance, the numpy helper functions meshgrid may be used as z may also
be a 2D numpy array.

In the Lines box, the style, width, color and alpha value of the contour separating line may be specified. The
line wdth must be an Integer value. The colors are provided in the Colors text box as sequence of
strings, see [colors](#colors).

Note that the colors are also used for the filling of the contour. Therefore, two overlaying contour plots may be
combined in order to get e.g. black contour lines for a coloured contour.

In the Areas box, filling of the contour can be turned on and off and hatch types can be specified that is
overlaid with the filling. The hatch types can be given in a sequence of hatch strings. A hatch string can be one of:

- `/` - diagonal hatching
- `\` - back diagonal
- `|` - vertical


- horizontal
- crossed
  - `x` - crossed diagonal
  - `o` - small circle
  - `O` - large circle
  - `.` - dots
- stars

Letters can be combined, in which case all the specified hatchings are done. If same letter repeats, it increases
the density of hatching of that pattern. Note that when the color is white then the mesh type is displayed
as black on white.

In the Labels box, contour labels can be turned on and off, and the font size can be spezified as an Integer.



## Sankey Diagram

<img class="img-fluid" src="../images/screenshot-chartdialog-sankey.png">

When the Sankey chart type is selected then on the right panel, Data and Diagram and Area boxes are displayed.

In the Data box, flows and orientations can be specified as sequences of numbers. Flows have positive numbers for
inputs and negative numbers for outputs. The absolute value of the number specifies the arrow width.
Orientations may have the values are
- `1` - from/to the top
- `0` - from/to the left or right
- `-1` - from/to the bottom

If orientations == 0, inputs will break in from the left and outputs will break away to the right. Labels may be
specified as a sequence of strings - either one string for all arrows or one per arrow. Each label is followed
by the value and the unit. Values are formatted using a Python formatting string

In the Diagram box, rotatation, gap, radius, shoulder, offset and angle can be specified, which control the
layout of the Sankey diagram.

In the Area box, the color of the diagram edge and the diagram filling can be set.

The figure panel is automatically updated whenever content of the chart dialog is changed. Should it show no
chart then something is wrong with the input so that later in the grid, no chart is shown as well.