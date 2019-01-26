# Python Optical Mark Recognition eXtraction tool

Tool for extracting data from specific forms using optical mark recognition. Made for the education team at Save the Children.

To use the software, click on releases above and download the latest version as a zip file, extract it, and use run.exe to start the tool. Everything is currently in alpha stage: please do report bugs and issues.

## System Requirements
Windows 7+, [Visual C++ 2015 Update 3 RC](https://www.microsoft.com/en-us/download/details.aspx?id=52685)

## Development
The code hasn't been developed as a public repo to date, so no garuantees are made about api stability or otherwise, but to get started clone the repo and use requirements.txt to download dependencies. All development so far has been done on Windows 7: either python 3.5 or python 3.6 should work. There are some demos, of which attendance_register_v2 is the latest and should work. You will need to obtain further data in order to run the demos, which hasn't been included here for data protection.

## Notes
- The tool is currently hard coded to specific form designs for attendance registers and exam marksheets, please contact shaun for more details.
- The output of the attendance register tool is as follows:
```
box_no,class_code,file_name,marker_error,omr_error,school_code,sheet_number,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,student_number
1,3,sample_form,p2,,,1,2,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,46
1,3,sample_form,p2,,,1,2,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,47
```
