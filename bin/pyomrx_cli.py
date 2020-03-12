import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.resolve()))
import argparse
from pyomrx.core.form_maker import FormMaker
from pyomrx.core.omr_factory import OmrFactory


def main():
    parser = argparse.ArgumentParser(
        description='Tool for generating and extracting sub_form_data '
        'from optical mark recognition forms')
    parser.add_argument(
        'mode',
        nargs=1,
        type=str,
        help='make|extract '
        '(whether to make an omr form or extract sub_form_data from a folder of scans)'
    )
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        nargs=1,
        help='path to input file (make) or folder (extract)')
    parser.add_argument(
        '-o', '--output', type=str, nargs=1, help='path to output file')
    parser.add_argument(
        '-t',
        '--template',
        type=str,
        nargs=1,
        required=False,
        help='path to omr template (required if mode == extract)')
    args = parser.parse_args()
    input_path = args.input[0]
    output_path = args.output[0]
    if args.mode[0] == 'make':
        excel_path = input_path
        output_folder = output_path
        form_maker = FormMaker(
            excel_file_path=excel_path, output_path=output_folder)
        form_maker.make_form()
    elif args.mode[0] == 'extract':
        if not args.template:
            raise parser.error('no omr template file specified')
        omr_file_path = args.template[0]
        images_folder = input_path
        output_file_path = output_path
        omr_factory = OmrFactory.from_omr_file(omr_file_path=omr_file_path)
        omr_factory.process_images_folder(
            images_folder, output_file_path=output_file_path)
    else:
        parser.error(
            'neither form gen mode or sub_form_data extract mode active')
    return 0


if __name__ == '__main__':
    main()
