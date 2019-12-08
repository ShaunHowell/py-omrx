'''
script for processing a folder of folders of images, ie each child folder contains scans from one AEP centre
usage: python3.6 process_exam_marksheets.py <path to folder of folders>
'''
import sys
from pyomrx.core.exam_marksheet import process_exam_marksheet_folder
from pathlib import Path
from pyomrx.core.exceptions import OmrException
from pyomrx.default_configs import exam_marksheet

assert len(sys.argv) == 2, 'usage: python3.6 process_exam_marksheets.py <path to folder of folders>'
input_input_folder = sys.argv[1]
print('processing exam marksheets in child folders of {}'.format(input_input_folder))
config = exam_marksheet.default_config()
for input_path in Path(input_input_folder).iterdir():
    if 'output' in input_path.parts[-1]:
        continue
    if not input_path.is_dir():
        print('{} is not a directory, skipping'.format(input_path))
        continue
    input_path = Path(input_path)
    output_folder = Path(input_input_folder) / 'output' / input_path.parts[-1]
    try:
        process_exam_marksheet_folder(
            str(input_path),
            config,
            str(output_folder))
    except OmrException as e:
        print(e, file=sys.stderr)
