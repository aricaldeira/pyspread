---
layout: default
section: manual
parent: ../
title: Advanced topics
---

# Advanced topics

## Accessing the current cell from a macro

The variables X, Y, Z, R, C and T are set to None inside the macro panel. In order to access the row, column or table of the cell that is calling a function inside the macro panel or inside an external library, the respective variables have to be provided as parameters.

## Conditional formatting

For conditionally formatting the background color of a cell, enter
```python
def color(value, condition_func, X, Y, Z):
    if condition_func(value):
        color = 255, 0, 0
    else:
        color = None

    S.cell_attributes[X,Y,Z]["bgcolor"] = color

    return value
```
into the macro panel and
```
color(5, lambda x: x>4, X, Y, Z)
```
into a cell.
If you change the first parameter in the cell's function from 5 into 1 then the background color changes back to white.


## Adjusting the float accuracy that is displayed in a cell

While one can use the `round` function to adjust accuracy, this may be tedious for larger spreadsheets.
Therefore, starting with pyspread v 2.3, `class_format_functions` is available. It is a dict that maps a type to a function.
It should be used in the Macro editor. The following code adjusts `float` output:

```python
class_format_functions[float] = lambda x: f"{x:.4f}"
```

Note that depending on your use case, `float` may not be the best choice. Consider using Python's builtin [decimal module](https://docs.python.org/3/library/decimal.html). When creating decimals from given numbers, do not forget to provide them as strings.

```
Decimal(3.2)    # 3.20000000000000017763568394002504646778106689453125
Decimal('3.2')  # 3.2
```

For arbitrary precision, you may want to try out the [mpmath module](https://pypi.org/project/mpmath/), which
provides the pretty attribute for human friendly representation.

If you are working with currencies, you may be interested in the **`Macro → Money`** action that requires the optional dependency [`py-moneyed`](https://pypi.org/project/py-moneyed/).

## Deep calls

Python's stack limits depth of calls. Therefore counting cells up by adding 1 to the cell result above is not recommended. Use the magic variable `X` instead.

## Cyclic references

Cyclic references are possible in pyspread. However, recursion depth is limited. Pyspread shows an error when the maximum recursion depth is exceeded. It is strongly advisable to only use cyclic references when either a frozen or a button cell interrupts the cycle. Otherwise, cyclic calculations may lock up pyspread.

## Result stability in old Python versions (<=3.5)

In old Python versions (<=3.5), result stability is not guaranteed because execution order may be changed. This results from the order of dict elements not being guaranteed.
This happens for when in large spreadsheets the result cache is full and cell results that are purged from the cache are re-evaluated.
This may be an issue when redefining global variables, which is therefore discouraged.
Note that for Python 3.7+, dict order stability is a language feature and therefore result stability is guaranteed.

## Security annoyance when approving files in read only folders

If a pys file is situated in a folder without write and file creation access, the signature file cannot be created. Therefore, the file has to approved each time it is opened.

## Handling large amounts of data

While the pyspread main grid may be large, filling many cells may consume considerable amounts of memory. When handling large amounts of data, data should be loaded into one cell. This approach saves memory, Therefore, load all your data in a numpy array that is situated within a cell and work from there.

## Substituting pivot tables

In the examples directory, a Pivot table replacement is shown using list comprehensions.

## Memory consumption for sheets with many matplotlib charts

If there are hundreds of charts in a spreadsheet then pyspread can consume considerable amounts of memory. This is most obvious when printing or when creating PDF files.
