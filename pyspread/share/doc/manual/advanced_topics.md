---
layout: default
section: manual
parent: ../
title: Advanced topics
---

# Advanced topics

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

The recommended option is to use Python's builtin [decimal module](https://docs.python.org/3/library/decimal.html).
When creating decimals from given numbers, do not forget to provide them as strings.

```
Decimal(3.2)    # 3.20000000000000017763568394002504646778106689453125
Decimal('3.2')  # 3.2
```

If you actually want floating point arithmetics using `numpy.float` provides less digits for many cases. 
For arbitrary precision, you may want to try out the [mpmath module](https://pypi.org/project/mpmath/), which
provides the pretty attribute for human friendly representation.

If you are working with currencies, you may be interested in the [Python Money Class](https://pypi.org/project/money/).
Putting their currency presets approach, which is stated on their project page, into the macro editor works well for me:

```
class EUR(Money):
    def __init__(self, amount='0'):
        super().__init__(amount=amount, currency='EUR')
```


## Cyclic references

Cyclic references are possible in pyspread. However, recursion depth is limited. Pyspread shows an error when the maximum recursion depth is exceeded. It is strongly advisable to only use cyclic references when either a frozen or a button cell interrupts the cycle. Otherwise, cyclic calculations may lock up pyspread.

## Result stability

Result stability is not guaranteed when redefining global variables because execution order may be changed. This happens for when in large spreadsheets the result cache is full and cell results that are purged from the cache are re-evaluated.

## Security annoyance when approving files in read only folders

If a pys file is situated in a folder without write and file creation access, the signature file cannot be created. Therefore, the file has to approved each time it is opened.

## Handling large amounts of data

While the pyspread main grid may be large, filling many cells may consume considerable amounts of memory. When handling large amounts of data, data should be loaded into one cell. This approach saves memory, Therefore, load all your data in a numpy array that is situated within a cell and work from there.

## Substituting pivot tables

In the examples directory, a Pivot table replacement is shown using list comprehensions.

## Memory consumption for sheets with many matplotlib charts

If there are hundreds of charts in a spreadsheet then pyspread can consume considerable amounts of memory. This is most obvious when printing or when creating PDF files.
