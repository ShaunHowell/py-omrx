# exam-system
[![Build Status](https://travis-ci.com/ShaunHowell/exam-system.svg?token=qa3pqsZkoC8q17Ekgz3K&branch=master)](https://travis-ci.com/ShaunHowell/exam-system)

Data and analytics pipeline for reporting on exam performance, based on optical mark recognition of marking forms.

Made for the education team at Save the Children, for the Accelerated Education Program common approach.

## Demos
To get started with the demos: 
- Clone the repo
- If using Windows:
    - Install [GhostScript](https://www.ghostscript.com/download/gsdnld.html)
    - Install [GraphicsMagick](ftp://ftp.graphicsmagick.org/pub/GraphicsMagick/windows/)
        - Choose the latest `.exe` version, either 32-bit or 64-bit according to your operating system
        - You can find whether you're on 32-bit or 64-bit by right-clicking on `my computer`, then `properties`       
- Install the python dependencies
    - make `exam-system` your working directory in a terminal
    - run `pip install -r requirements.txt` (or `pip3` if necessary)
- Then you can run the demos in `src/demo` by navigating to the root of a demo and running `python run_demo.py`

## Notes
- Requires Python and pip to be installed
- Only tested with Python 3.5 on Windows 7
