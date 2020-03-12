![pyomrx overview](res/overview_image.jpg)
------
![travis master build status](https://travis-ci.com/ShaunHowell/py-omrx.svg?token=qa3pqsZkoC8q17Ekgz3K&branch=master)

Python Optical Mark Recognition eXtraction tool is a library and GUI for generating OMR forms and extracting data from them. 
Form design is done in excel, then the tool converts this into an image and a .omr file. 
The image is printed, completed and scanned, then the tool extracts data from a batch of scans and outputs a csv file. 
Made originally for the education team at Save the Children UK for capturing school attendance and exam score data in 
contexts where digital data collection isn't possible.

# Install
To just use the graphical user interface on windows, click on releases above and download the latest version as a zip file, extract it, and use run.exe to start the tool.
To use as a python package:

`pip install pyomrx`

To build the windows executable, from the repo route run `python build_exe_zip.py`, which uses cx_Freeze to bundle requirements.

# Quickstart
EXAMPLES FOLDER

# Parts of an OMR form
Visual breakdown of parts of a form

# Creating a form in excel
Instructions on named ranges and comments etc

# Usage
## GUI
## CLI
## API
factory, forms, sub forms, circle groups, etc

# Output
- The output of the tool is as follows:
```
box_no,class_code,file_name,marker_error,omr_error,school_code,sheet_number,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,student_number
1,3,sample_form,p2,,,1,2,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,46
1,3,sample_form,p2,,,1,2,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,47
```

# Tests
`pytest`

# Contributing

# Credits
Big thank you to the education team at Save the Children UK, with whom this tool was originally concieved and created,
 especially Kathryn Cooper and Patrick Mroz-Dawes.
 
# License 

Please report bugs and issues to shaun: shaunkhowell -at- gmail.com