Pyspread deployment test
========================

<date>
<version>

The tests are conducted with commit
<hash>

Test system:
 + Manjaro
 + Python <version>
 + PyQt5 <version>
 + numpy <version>
 + matplotlib <version>
 + pyenchant <version>

1. Startup
----------

```
$ cd <pyspread main directory>
$ ./bin/pyspread
```
Result: Pyspread main window is shown.
Rating: [ ]

Repetition after deleting config file
```
$ rm ~/.config/pyspread/pyspread.conf
$ ./pyspread.sh
```
Result: Pyspread main window is shown.
Rating: [ ]

2. File -> New
--------------
Select File -> New via menubar
Enter 1,1,1 in dialog
Result: Grid with 1 cell shown
Rating: [ ]

Select File -> New via toolbar
Enter 1,1,1 in dialog
Result: Grid with 1 cell shown
Rating: [ ]

Select File -> New via toolbar
Enter 0,0,0 in dialog
Result: No change in grid, error message
Rating: [ ]

Select File -> New via toolbar
Enter 9999999999,0,0 in dialog
Result: No change in grid, error message
Rating: [ ]

Select File -> New via toolbar
Enter 1000000,10000,10 in dialog
Result: Grid with correct shape shown
Rating: OK (unit test)

Select cell 999999, 9999, 9
Select File -> New via toolbar
Enter 2,2,2 in dialog
Result: Grid with correct shape shown
Rating: [ ]

Select File -> New via toolbar
Enter 1000,100,3 in dialog
Result: Grid with correct shape shown
Rating: [ ]

Select File -> New via toolbar
Cancel dialog
Result: No changes
Rating: [ ]


2. File -> Open
---------------

Select File -> Open via menubar
Choose valid and signed file test.pysu
Result: File loaded and displayed correctly
Rating: [ ]

Select File -> Open via toolbar
Choose valid and unsigned file test.pysu
Result: File loaded and put into safe mode
Rating: [ ]

Select File -> Open via toolbar
Cancel dialog
Result: No changes
Rating: [ ]

Select File -> Open via toolbar
Enter invalid filename
Result: Button is disabled
Rating: [ ]

Select File -> Open via toolbar
Choose valid and unsigned file test.pys
Result: File loaded and put into safe mode
Rating: [ ]

Select File -> Open via toolbar
Choose valid and signed file test.pys
Result: File loaded and displayed correctly
Rating: [ ]

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with shape 0,100,3
Result: Invalid grid is displayed in safe mode
Rating: [ ]

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with version 12.0 and shape 0,100,3
Result: Crash with ValueError indicating invalid version
Rating: [ ]

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with cell out of shape
Result: Grid is displayed in safe mode, crash on approve
Rating: [ ]

Select File -> Open via toolbar
Choose valid and unsigned file without read permissions test_inaccessible.pysu
Result: Crash with PermissionError [Errno 13] Permission denied
Rating: [ ]


3. File -> Open recent
----------------------

Select recent file test.pysu from menubar
Result: File is loaded correctly
Rating: [ ]

Select recent file test.pys from menubar
Result: File is loaded correctly
Rating: [ ]


4. File -> Save
---------------

Select recent file test.pys from menubar
Enter 'Test' in cell 0,0,0
Select File -> Save from menubar
Select recent file test.pys from menubar
Result: Change is still present, file is signed correctly and save moe is disabled
Rating: [ ]


5. File -> Save as
------------------

Select recent file test.pysu from menubar
Select File -> Save as from menubar
Enter file test_empty.pysu and press OK
Result: File is created
Rating: [ ]

Delete content and remove merges
Select File -> Save as from menubar
Enter file test_empty.pysu and press OK
Result: File overwriting is protected by dialog
Rating: [ ]

Select recent file test.pysu from menubar
Select File -> Save as from menubar
Enter file test_empty.pysu in folder '/' without write permissions and press OK
Result: Crash with PermissionError
Rating: [ ]


6. File -> Approve
------------------
Select File -> Open via toolbar
Choose valid and unsigned file test.pysu
Select File -> Approve via menubar
Result: File loaded correctly but safe mode message is still shown in macro panel.
Rating: [ ]


7. File -> Clear globals
------------------------
Select File -> Clear globals from menubar
Result: Message on_nothing >  &Clear globals <src.actions.Action object at 0x7f25a1614a50>
Rating: [ ]


8. File -> Print preview
------------------------
Select File -> Print preview from menubar
Cancel dialog
Result: Nothing
Rating: [ ]

Select File -> Print preview from menubar
Press OK
Result: Print Preview dialog
Rating: [ ]

Select File -> Print preview from menubar
Enter 1111, 0, 1199, 5 (outside shape 1000, 100, 3)
Press OK
Result: Crash, ZeroDivisionError
Rating: [ ]

Select File -> Print preview from menubar
Enter 1, 1, 12, 5
Press OK
Result: Print preview dialog shows non-centered grid
Rating: [ ]

Select File -> Print preview from menubar
Enter 3, 3, 33, 33
Press OK
Result: Print preview dialog shows non-centered grid
Rating: [ ]

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 1, 1
Press OK
Result: Print preview dialog shows grid
Rating: [ ]

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 0, 0
Press OK
Result: Print preview dialog shows grid cell that is larger than the page
Rating: [ ]

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 9999, 999
Press OK
Result: Long wait, Memory consumption > 3GB, test aborted by tester
Rating: [ ]


9. File -> Print
----------------

Select File -> Print from menubar
Press OK
Result: Printer dialog
Rating: [ ]


10. File -> Preferences
-----------------------

Select File -> Preferences from menubar
Press Cancel
Result: Nothing
Rating: [ ]

Select File -> Preferences from menubar
Change Signature key to "" and press OK
Select File -> Preferences from menubar
Result: Signature key is ""
Rating: [ ]

Select File -> Preferences from menubar
Change Signature key to empty string and press OK
Select File -> Preferences from menubar
Result: New signature key is visible
Rating: [ ]

Select File -> Preferences from menubar
Change Cell calculation timeout to 10000 and press OK
Select File -> Preferences from menubar
Result: New Cell calculation timeout is visible
Rating: [ ]

Select File -> Preferences from menubar
Change Frozen cell refresh period to 10000 and press OK
Select File -> Preferences from menubar
Result: New Frozen cell refresh period is visible
Rating: [ ]


Select File -> Preferences from menubar
Change number of recent files to 2 and press OK
Select File -> Preferences from menubar
Result: Value has not changed and is still 5
Rating: [ ]


11. File -> Quit
----------------

Open Pyspread
Select File -> Quit from menubar
Result: Application has closed
Rating: [ ]

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Result: Dialog unsaved changes is visible
Rating: [ ]

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Save in Dialog unsaved changes
Result: Save as dialog is shown
Rating: [ ]

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Cancel in Dialog unsaved changes
Result: Nothing
Rating: [ ]

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Save in Dialog unsaved changes
Cancel Save dialog
Result: Application has closed
Rating: [ ]


12. Edit -> Undo
----------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,1,0
Format cell 0,1,0 bold
Enter 3 in cell 0,2,0
Format cell 0,2,0 bold, italics, underlined and strikethrough
Enter 'Test' in cell 0,3,0
Align and justify cell 0,3,0 centered
Select cells 0,1,0 to 2,2,0
Change line color to blue and background color to yellow
Undo all steps
Result: Steps undone, border line coloring is undone in 2 steps
Rating: [ ]


13. Edit -> Redo
----------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,1,0
Format cell 0,1,0 bold
Enter 3 in cell 0,2,0
Format cell 0,2,0 bold, italics, underlined and strikethrough
Enter 'Test' in cell 0,3,0
Align and justify cell 0,3,0 centered
Select cells 0,1,0 to 2,2,0
Change line color to blue and background color to yellow
Undo all steps
Redo all steps
Result: Cells look like before the undo operation
Rating: [ ]


14. Edit -> Cut
---------------

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Cut from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
Rating: [ ]

Enter 1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl+x
Select cell 1,0,0
Press Ctrl+v
Result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
Rating: [ ]

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Cut from toolbar
Select cell 1,0,0
Select Paste from toolbar
Result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
Rating: [ ]

Enter 1 in all cells between 0,0,0 and 3,2,0
Select cells 0,0,0 to 3,2,0
Select Edit -> Cut from menubar
Select Cell 6,0,0
Select Edit -> Paste from menubar
Result: Cell 0,0,0 to 3,2,0 are empty, cells in the area at 6,0,0 show 1
Rating: [ ]


15. Edit -> Copy
----------------

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Result: Cell 0,0,0 and cell 1,0,0 show 1
Rating: [ ]

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Copy from toolbar
Select cell 1,0,0
Select Paste from toolbar
Result: Cell 0,0,0 and cell 1,0,0 show 1
Rating: [ ]

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Result: Cell 1,0,0 has the code 1+1 and shows 2
Rating: [ ]

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl+c
Select cell 1,0,0
Press Ctrl+v
Result: Cell 1,0,0 has the code 1+1 and shows 2
Rating: [ ]


16. Edit -> Copy results
------------------------

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy results from menubar
Select cell 1,0,0
Press Ctrl-v
Result: Cell 1,0,0 has the code 2 and shows 2
Rating: [ ]


17. Edit -> Paste
-----------------

Enter 1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Select Edit -> Copy from menubar
Select cell 999,0,0 (grid shape is 1000,100,3)
Select Edit -> Paste from menubar
Result: Cell 999,0,0 shows 1
Rating: [ ]

Enter 1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Select Edit -> Copy from menubar
Select Table 1
Select cell 0,0,1
Select Edit -> Paste from menubar
Result: Cells 0,0,1 and 1,0,1 show 1
Rating: [ ]


18. Edit -> Paste as
--------------------

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl-c
Select cell 1,0,0
Select Edit -> Paste as from menubar
Result: Cell 1,0,0 has the code 1+1 and shows 2
Rating: [ ]

Enter 1+1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Press Ctrl-c
Select cell 3,0,0
Select Edit -> Paste as from menubar
Result: Cell 3,0,0 has the code 1+1\n1+1
Rating: [ ]

Load png image in cell 1,2,0
Select cell 1,2,0
Select Copy results from menubar
Select cell 4,2,0
Select Edit -> Paste as from menubar
Result: Image appears in cell 4,2,0
Rating: [ ]

Load svg image in cell 7,1,0
Select cell 7,1,0
Select Copy results from menubar
Select cell 7,2,0
Select Edit -> Paste as from menubar
Result: Image appears in cell 7,2,0
Rating: [ ]

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Result: Dialog appears with choices image svg+xml and x-qt-image
Rating: [ ]

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Choose image svg+xml from dialog
Result: Crash IndexError: list index out of range (cannot reproduce)
Rating: [ ]

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Choose image x-qt-image from dialog
Result: Chart appears in cell 9,2,0
Rating: [ ]


19. Edit -> Find
----------------
Enter 1 in cell 0,0,0
Enter 2 in cell 1,0,0
Enter 3 in cell 2,0,0
Enter 4 in cell 3,0,0
Enter 'a' in cell 0,1,0
Enter 'b' in cell 1,1,0
Enter 'c' in cell 2,1,0
Enter 'Test' in cell 3,1,0
Enter 2000+1 in cell 0,2,0

Enter 1 in Search box and press <Enter>
Result: Cell 0,0,0 is selected
Rating: [ ]

Press <Enter> again
Result: Nothing
Rating: [ ]

Enter 1 in Search box and press <Enter>
Result: Cell 1,0,0 is selected
Rating: [ ]

Enter Te in Search box and press <Enter>
Result: Cell 3,1,0 is selected
Rating: [ ]

Enter test in Search box and press <Enter>
Result: Cell 3,1,0 is selected
Rating: [ ]

Select cell 1,0,0
Toggle Match case On
Enter test in Search box and press <Enter>
Result: Nothing
Rating: [ ]

Toggle Match case Off
Enter 2001 in Search box and press <Enter>
Result: Nothing
Rating: [ ]

Toggle Code and Results On
Enter 2001 in Search box and press <Enter>
Result: Cell 0,2,0 is selected
Rating: [ ]

Toggle Code and Results Off
Select cell 5,2,0
Enter 1 in Search box and press <Enter>
Result: Cell 0,0,0 is selected
Rating: [ ]

Select cell 5,2,0
Toggle Search Backwards On
Enter 1 in Search box and press <Enter>
Result: Cell 0,2,0 is selected
Rating: [ ]

Toggle Search Backwards Off
Enter Te in Search box and press <Enter>
Result: Cell 3,1,0 is selected
Rating: [ ]

Toggle Whole Words On
Select cell 0,0,0
Enter Te in Search box and press <Enter>
Result: Nothing
Rating: [ ]

Toggle Whole Words On
Select cell 0,0,0
Enter Test in Search box and press <Enter>
Result: Cell 3,1,0 is selected
Rating: [ ]

Toggle Whole Words Off
Toggle Regular expression On
Select cell 10,0,0
Enter .*[1-3] in Search box and press <Enter>
Result: Cell 2,1,0 is selected
Rating: [ ]

Enter .*[1-3] in Search box and press <Enter>
Result: Cell 0,0,0 is selected
Rating: [ ]

Enter .*[1-3] in Search box and press <Enter>
Result: Cell 1,0,0 is selected
Rating: [ ]

Enter .*[1-3] in Search box and press <Enter>
Result: Cell 1,0,0 is selected
Rating: [ ]


20. Edit -> Replace
-------------------

Enter 'Test' in cell 0,0,0
Enter 1 in cell 1,0,0
Enter 1 in cell 2,0,0
Open Replace Dialog
Search for Te and Replace with Tee
Result: 'Teest' in cell 0,0,0
Rating: [ ]

Search for Tee and Replace with Te
Result: 'Test' in cell 0,0,0
Rating: [ ]

Select cell 0,0,0
Search for 1 and Replace all with 222
Result: 222 in cell 1,0,0
Rating: [ ]


21. Edit -> Quote
-----------------
Enter Test in cell 0,0,0
Select cell 0,0,0
Press <Ctrl>+<Enter>
Result 'Test' in cell 0,0,0
Rating: [ ]

Type Test in 0,0,0 and press <Ctrl> + <Enter>
Result: Code in cell is deleted
Ratung: [ ]


22. Edit -> Insert rows
-----------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 2,0,0
Select row 2
Select Insert rows
Result: 2 is in cell 3,0,0
Rating: [ ]

Select rows 2 and 3
Select Insert rows
Result: 2 is in cell 5,0,0
Rating: [ ]

23. Edit -> Insert columns
--------------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 1,1,0
Select column 1
Select Insert columns
Result: 2 is in cell 1,2,0
Rating: [ ]

Select columns 1 and 2
Select Insert columns
Result: 2 is in cell 1,4,0
Rating: [ ]


24. Edit -> Insert table
------------------------

Enter 0 in cell 0,0,0
Enter 1 in cell 0,0,1
Select Table 1
Select Insert table
Result: 1 is in cell 0,0,2
Rating: [ ]

25. Edit -> Delete rows
-----------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 3,0,0
Select row 1
Select Delete rows
Result: Crash, IndexError: Grid index (1, 100, 0) outside grid shape (1000, 100, 3).
Rating: [ ]


26. Edit -> Delete columns
--------------------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,2,0
Select column 1
Select Delete columns
Result: Crash, IndexError: Grid index (1000, 1, 0) outside grid shape (1000, 100, 3)
Rating: [ ]


27. Edit -> Delete table
------------------------

Enter 0 in cell 0,0,0
Enter 1 in cell 0,0,2
Select Table 1
Select Delete table
Result: 1 is in cell 0,0,1
Rating: [ ]


28. Edit -> Resize grid
-----------------------

Select Edit -> Resize grid
Enter shape 5,5,1 and press ok
Result: Grid with shape 5,5,1
Rating: [ ]

Select Edit -> Resize grid
Enter shape 0,0,0 and press ok
Result: Nothing
Rating: [ ]


29. View -> Fullscreen
----------------------

Select View -> Fullscreen
Result: Application is in fullscreen mode
Rating: [ ]

Select View -> Fullscreen
Result: Application is in normal mode again
Rating: [ ]


30. View -> Toolbars
--------------------

Toggle each toolbar on and off via the View -> Toolbars menu
Result: Each toolbar disappears and reappears as requested
Rating: [ ]


31. View -> Entry line
----------------------

Toggle entry line on and off via View -> Entry line
Result: The entry line disappears and reappears as requested
Rating: [ ]


32. View -> Macro panel
-----------------------

Toggle macro panel on and off via View -> Macro panel
Result: The macro panel disappears and reappears as requested
Rating: [ ]


33. View -> Go to cell
----------------------

Select cell 0,0,0
Select View -> Go to cell
Enter 0,0,0 in dialog
Result: Nothing
Rating: [ ]

Select View -> Go to cell
Enter nothing in dialog
Result: Nothing
Rating: [ ]

Select View -> Go to cell
Enter 1,0,0 in dialog
Result: Cell 1,0,0 is selected
Rating: [ ]

Select View -> Go to cell
Enter 999,99,9 in dialog
Result: Cell 999,99,0 is selected
Rating: [ ]

Select View -> Go to cell
Enter 999,99,1 in dialog
Result: Cell 999,99,1 is selected
Rating: [ ]


34. View -> Toggle spell checker
--------------------------------

Select cell 0,0,0
Enter Tes
Select View -> Toggle spell checker
Result: Nothing
Rating: Bug, minor inconvenience, immediate enabling of the spell checker would be better

Select cell 0,0,0
Enter Tes
Select cell 1,0,0
Select View -> Toggle spell checker
Select cell 0,0,0
Result: Tes is marked as unknown word
Rating: [ ]


35. View -> Zoom in
-------------------

Select View -> Zoom in
Result: Grid is zoomed in
Rating: OK


36. View -> Zoom out
--------------------

Select View -> Zoom out
Result: Grid is zoomed out
Rating: [ ]


37. View -> Original size
-------------------------

Select View -> Original size
Result: Grid is zoomed to original size
Rating: [ ]


38. View -> Refresh selected cells
----------------------------------

Enter i=0 in Macro editor
Enter i=i+1 in cell 0,0,0
Freeze cell 0,0,0
Select View -> Refresh multiple times
Results: Before Freezing, cell result is 1 after refreshing, it counts up
Rating: [ ]


39. View -> Toggle periodic updates
-----------------------------------

Enter i=0 in Macro editor
Enter i=i+1 in cell 0,0,0
Freeze cell 0,0,0
Select View -> Toggle periodic updates
Results: Cell result counts up once a second (dependent on preference setting)
Rating: [ ]


40. View -> Show frozen
-----------------------

Freeze cell 0,0,0
Select View -> Show frozen
Select View -> Show frozen
Results: Cell 0,0,0 shows blue diagonal pattern between When show frozen in toggled on.
Rating: [ ]


41. Format -> Copy format
-------------------------

see (42)

42. Format -> Paste format
--------------------------

Enter 1 in cell 1,2,0
Enter 2 in cell 2,2,0
Enter 3 in cell 1,3,0
Enter 4 in cell 2,3,0
Select cells 1,2,0 and 2,2,0
Format Bold
Select cells 1,3,0 and 2,3,0
Format Italics
Copy cell code of the 4 cells
Select cell 5,2,0
Paste clipboard
Select cells 1,2,0, 2,2,0, 1,3,0 and 2,3,0
Copy format
Select cell 5,2,0
Paste format
Result: Bold format is shown for cells 5,2,0 6,2,0 italics for  5,3,0, 6,3,0
Rating: [ ]


43. Format -> Font
------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Font
Select Arial font, bold, 22 in dialog and press ok
Result: The text in cell 0,0,0 is rendered accordingly.
Rating: [ ]

44. Format -> Bold
------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Bold
Result: The text in cell 0,0,0 is rendered accordingly.
Rating: [ ]


45. Format -> Italics
---------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Italics
Result: The text in cell 0,0,0 is rendered accordingly.
Rating: [ ]


46. Format -> Underline
-----------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Underline
Result: The text in cell 0,0,0 is rendered accordingly.
Rating: [ ]


47. Format -> Strikethrough
---------------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Strikethrough
Result: The text in cell 0,0,0 is rendered accordingly.
Rating: [ ]


48. Format -> Cell renderer
---------------------------

Enter numpy.diag([255]*100) in cell 0,0,0
Select Format -> Cell renderer ->  Image cell renderer
Result: Black image with diagonal white line
Rating: [ ]


Enter '<b>Test</b>' in cell 0,0,0
Select Format -> Cell renderer -> Markup cell renderer
Result: Test is printed bold
Rating: [ ]

Select Format -> Cell renderer -> Chart cell renderer
Result nothing but message
Rating: [ ]


49. Format -> Freeze cell
-------------------------

Select Cell 0,0,0
Select Format -> Freeze cell
Enter 1 in cell 0,0,0
Results: Nothing
Rating: [ ]


50. Format -> Lock cell
-----------------------

Select Cell 0,0,0
Enter 1 in cell 0,0,0
Select Format -> Lock cell
Try editing cell 0,0,0
Result: Cell is not selected, editor does not appear.
Rating: [ ]

Select Cell 0,0,0
Enter 1 in cell 0,0,0
Select Format -> Lock cell
Select Cell 0,0,0
press <Del>
Result: Cell content is Deleted
Rating: [ ]


51. Format -> Merge cells
-------------------------

Select cells 0,0,0 to 4,1,0
Select Format -> Merge cells
Result: Cells are merged
Rating: [ ]

Select cell 0,0,0
Select Format -> Merge cells
Result: Cells are unmerged
Rating: [ ]


52. Format -> Rotation
----------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 rotation types
Result: Cells are rotated as expected
Rating: [ ]


53. Format -> Justification
---------------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 justification types
Result: Cells are justified as expected
Rating: [ ]


54. Format -> Alignment
-----------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 alignment types
Result: Cells are aligned as expected
Rating: [ ]


55. Format -> Formatted borders
-------------------------------

Select cell 1,1,0
Select Format -> Formatted borders -> Top border
Select Format -> Border width -> 8
Result: Top border is fat
Rating: [ ]

Select cell 1,1,0
Select Format -> Formatted borders -> Bottom border
Select Format -> Border width -> 8
Result: Bottom border is fat
Rating: [ ]

Select cell 1,1,0
Select Format -> Formatted borders -> Left border
Select Format -> Border width -> 8
Result: Left border is fat
Rating: [ ]

Select cell 1,1,0
Select Format -> Formatted borders -> Right border
Select Format -> Border width -> 8
Result: Right border is fat
Rating: [ ]

Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Outer border
Select Format -> Border width -> 8
Result: Outer borders are fat
Rating: [ ]

Select Format -> Border width -> 1
Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Inner border
Select Format -> Border width -> 8
Result: Inner borders are fat
Rating: [ ]

Select Format -> Border width -> 1
Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Top and bottom borders
Select Format -> Border width -> 8
Result: Top and bottom borders are fat
Rating: [ ]


56. Format -> Border width
--------------------------

Select cell 0,0,0
Select Format -> Border width 0
Result: Border width is a pixel line
Rating: [ ]

Select cell 1,1,0
Select Format -> Border width 1
Result: Border width is light line
Rating: [ ]

Select cell 1,1,0
Select Format -> Border width 64
Result: Border width is a huge line
Rating: [ ]


57. Format -> Text color
------------------------

Enter 'Test' in cell 0,0,0
Select cell 0,0,0
Select Format -> Text color
Choose red color in dialog and press ok
Result: Text is red
Rating: [ ]


58. Format -> Line color
------------------------

Select cell 0,0,0
Select Format -> Line color
Choose blue color in dialog and press ok
Result: Cell border line is blue
Rating: [ ]


59. Format -> Background color
------------------------------

Select cell 0,0,0
Select Format -> Background color
Choose yellow color in dialog and press ok
Result: Cell background is yellow
Rating: [ ]


60. Macro -> Insert image
-------------------------

Select cell 1,1,0
Select Macro -> Insert image
Choose png image and press OK
Result: Cell renderer is set to image and image appears
Rating: [ ]

Select cell 1,1,0
Select Macro -> Insert image
Choose svg image and press OK
Result: Cell renderer is set to image and image appears
Rating: [ ]


61. Macro -> Link image
-----------------------

Select cell 1,1,0
Select Macro -> Link image
Result: Error message on_nothing >  Link image... <src.actions.Action object at 0x7f76a0e8f690>
Rating: [ ]


62. Macro -> Insert chart
-------------------------

Select cell 1,1,0
Select Macro -> Insert chart
Choose Pie chart in chart dialog and press ok
Result: Chart renderer is activated and pie chart is displayed.
Rating: [ ]


63. Help -> First steps
-----------------------
Select Help -> First steps from menubar
Result: Message on_nothing >  First steps... <src.actions.Action object at 0x7f78e1644550>
Rating: [ ]

64. Help -> Tutorial
--------------------
Select Help -> Tutorial from menubar
Result: Message on_nothing >  Tutorial... <src.actions.Action object at 0x7f78e16445f0>
Rating: [ ]


65. Help -> FAQ
---------------
Select Help -> FAQ from menubar
Result: Message on_nothing >  FAQ... <src.actions.Action object at 0x7f78e1644730>
Rating: [ ]

66. Help -> Dependencies
------------------------

Select Help -> Dependencies from menubar
Result: Dependencies is displayed correctly
Rating: [ ]

67. Help -> About pyspread
--------------------------

Select Help -> About from menubar
Result: About dialog is displayed correctly
Rating: [ ]