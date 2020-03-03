import shutil
import os
import argparse
import sys
from pathlib import Path
import re


def split_folder(input_folder):
    maths_regex = 'math'
    language_arts_regex = 'lang|art'
    level_regex = 'l(?:evel){0,1}\s*([1-3])'
    error_files = []
    for file_path in Path(input_folder).iterdir():
        is_language_arts = False
        is_maths = False
        file_path = str(file_path).lower()
        if re.findall(maths_regex, file_path):
            is_maths = True
        if re.findall(language_arts_regex, file_path):
            is_language_arts = True
        if (is_maths and is_language_arts) or (not is_language_arts
                                               and not is_maths):
            error_files.append(file_path)
            continue
        levels = re.findall(level_regex, file_path)
        if levels:
            if len(levels) > 1:
                error_files.append(file_path)
                continue
            else:
                level = int(
                    levels[0][0] if len(levels[0][0]) else levels[0][1])
        else:
            error_files.append(file_path)
            continue
        folder_path = Path(
            input_folder) / f'{"maths" if is_maths else "language"}_L{level}'
        if not folder_path.exists():
            os.makedirs(str(folder_path))
        shutil.copy(str(file_path), str(folder_path / Path(file_path).name))
    print(f'error files: {[Path(file).stem for file in error_files]}')


def main():
    input_folder = 'temp/big_exam_batch/images/Second lot cleaned'  #sys.argv[1]
    print(f'splitting files in {input_folder}')
    split_folder(input_folder)


if __name__ == '__main__':
    main()
