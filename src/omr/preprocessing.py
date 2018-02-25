import subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import sys
import os


def get_converter_path():
    gm_check = subprocess.call('gm convert -help', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if gm_check == 0:
        converter_path = 'gm'
    else:
        try:
            exam_system_path = Path(
                '/'.join([part for part in Path.cwd().parts[:Path.cwd().parts.index('exam-system') + 1]]))
            converter_path = exam_system_path / 'src/GraphicsMagick/gm.exe'
        except:
            print('couldn\'t find GraphicsMagick installation')
    return converter_path


def images_from_pdf(input_file_path, output_folder_path, density=300):
    image_name = str(Path(input_file_path).stem)
    output_file_pattern = '{}.png'.format(Path(output_folder_path) / (image_name.replace(' ', '_') + '_%03d'))
    converter_path = get_converter_path()
    cmd_string = '{} convert -density {} "{}" +adjoin "{}"'.format(converter_path, density, input_file_path,
                                                                   output_file_pattern)
    try:
        subprocess.check_call(cmd_string, shell=True)
    except subprocess.CalledProcessError:
        print('failed to convert pdf \'{}\', check GraphicsMagick and GhostScript installation'.format(
            Path(input_file_path).name))
        raise


def optimise_quality(input_file_path, output_file_path=None, overwrite=False):
    assert Path(input_file_path).suffix.lower() in ['.png', '.jpg', '.jpeg'], 'input file must be a valid image'
    if output_file_path:
        assert Path(output_file_path).suffix.lower() in ['.png', '.jpg',
                                                         '.jpeg'], 'output path must be an image file name'
    im = Image.open(input_file_path)
    im = im.rotate(-90, expand=1)
    im = ImageOps.autocontrast(im)
    im = ImageEnhance.Brightness(im).enhance(1.05)
    im = ImageOps.equalize(im)
    a, b, c = 1, 0.1, 0.05
    k = [0, 0, 0, 0, 0,
         0, c, b, c, 0,
         0, b, a, b, 0,
         0, c, b, c, 0,
         0, 0, 0, 0, 0]
    im = im.filter(ImageFilter.Kernel((5, 5), k))
    im = im.filter(ImageFilter.Kernel((5, 5), k))
    im = im.filter(ImageFilter.Kernel((5, 5), k))
    im = im.filter(ImageFilter.MaxFilter(3))
    im = im.filter(ImageFilter.MaxFilter(3))
    im = im.filter(ImageFilter.MaxFilter(3))
    im = im.convert('1')
    im = im.filter(ImageFilter.MinFilter(3))
    im = im.filter(ImageFilter.MinFilter(3))
    if output_file_path:
        if Path(output_file_path).exists() and not overwrite:
            raise Exception('can\'t save {}. Overwrite not set as True'.format(Path(output_file_path).stem))
        else:
            im.save(output_file_path)
    elif not output_file_path and not overwrite:
        raise Exception('can\'t save {}. Overwrite not set as True'.format(Path(output_file_path).stem))
    else:
        im.save(input_file_path)


def preprocess_folder(input_folder, output_folder):
    if not Path(output_folder).exists():
        Path(output_folder).mkdir()
    else:
        assert len(os.listdir(output_folder)) == 0, 'output folder must be empty'
    # extract images from pdf
    for file_path in Path(input_folder).iterdir():
        if file_path.suffix.lower() == '.pdf':
            print('INFO: extracting images from {}'.format(file_path.name))
            images_from_pdf(str(file_path), output_folder)
    # optimise quality of all images (e.g. brightness)
    # for file_path in Path(output_folder).iterdir():
    #     optimise_quality(str(file_path), overwrite=True)
    # crop and rotate all images to only OMR form
    print('INFO: folder preprocessed')


if __name__ == '__main__' and sys.argv[1] == 'dev':
    pass
