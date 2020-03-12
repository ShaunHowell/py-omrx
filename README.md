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
The examples folder contains an attendance form and and exam marksheet folder. 
This quickstart will guide you through the full process of making and extracting from a form via the GUI. There is also a CLI, described below.
To run the examples with the GUI follow these steps:
1. Start the GUI (either `python app.py` or if you downloaded a release, unzip the build folder and rouble click `run.exe`)
2. Click the `Generate template` tab
3. Choose the excel file in one of the example folders as the template file, and choose an output file path for the `.omr` file. 
4. Click `Process` and wait for completion
5. Open the output location you chose: there should be an image (or 2 in the attendance form case) and a .omr file
6. Fill in one of the images: either print, complete and scan (as an image not a pdf), or use the fill tool in paint. See the form filling guide below.
7. Put the image in a new folder
8. Start the GUI again, this time click the `Extract data` tab
9. Choose the previously generated `.omr` template file, select the new images folder, and choose an output path
10. Click `Process` and wait for completion. Your extracted data should now be ready as a csv file.

# Parts of an OMR form
Visual breakdown of parts of a form
A pyomrx form contains the following heirarchy of components:


# Creating a form in excel
Instructions on named ranges and comments etc

# Usage
## GUI
## CLI
## API
factory, forms, sub forms, circle groups, etc

## Filling in a pyomrx form for best results

# Output
- The output of the tool is as follows:
```
box_no,class_code,file_name,marker_error,omr_error,school_code,sheet_number,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,student_number
1,3,sample_form,p2,,,1,2,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,46
1,3,sample_form,p2,,,1,2,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,47
```

# FAQ / Troubleshooting
1. File path too long: this is a limitation on Windows

# Tests
`pytest`

# Contributing

# Credits
Big thank you to the education team at Save the Children UK, with whom this tool was originally concieved and created,
 especially Kathryn Cooper and Patrick Mroz-Dawes.
 
# License 

Please report bugs and issues to shaun: shaunkhowell -at- gmail.com