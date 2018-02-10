import subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import sys


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
    output_file_pattern = '{}.png'.format(Path(output_folder_path) / (image_name + '_%03d'))
    converter_path = get_converter_path()
    cmd_string = '{} convert -density {} {} +adjoin {}'.format(converter_path, density, input_file_path,
                                                               output_file_pattern)
    try:
        subprocess.check_call(cmd_string, shell=True)
    except subprocess.CalledProcessError:
        print('failed to convert pdf \'{}\', check GraphicsMagick and GhostScript installation'.format(
            Path(input_file_path).name))
        raise


def optimise_quality(input_file_path, output_file_path=None, overwrite=False):
    im = Image.open(input_file_path)
    im2 = im.rotate(-90, expand=1)
    im2 = ImageOps.autocontrast(im2)
    im2 = ImageEnhance.Brightness(im2).enhance(1.05)
    im2 = ImageOps.equalize(im2)
    a, b, c = 1, 0.1, 0.05
    k = [0, 0, 0, 0, 0,
         0, c, b, c, 0,
         0, b, a, b, 0,
         0, c, b, c, 0,
         0, 0, 0, 0, 0]
    im2 = im2.filter(ImageFilter.Kernel((5, 5), k))
    im2 = im2.filter(ImageFilter.Kernel((5, 5), k))
    im2 = im2.filter(ImageFilter.Kernel((5, 5), k))
    im2 = im2.filter(ImageFilter.MaxFilter(3))
    im2 = im2.filter(ImageFilter.MaxFilter(3))
    im2 = im2.filter(ImageFilter.MaxFilter(3))
    im2 = im2.convert('1')
    im2 = im2.filter(ImageFilter.MinFilter(3))
    im2 = im2.filter(ImageFilter.MinFilter(3))
    if output_file_path:
        if Path(output_file_path).exists() and not overwrite:
            raise Exception('can\'t save {}. Overwrite not set as True'.format(Path(output_file_path).stem))
    elif not output_file_path and not overwrite:
        raise Exception('can\'t save {}. Overwrite not set as True'.format(Path(output_file_path).stem))
    print('saving')
    im2.save(output_file_path)


def preprocess_folder(input_folder, output_folder):
    # extract images from pdf
    for file_path in Path(input_folder).iterdir():
        if file_path.suffix.lower() == '.pdf':
            images_from_pdf(str(file_path), output_folder)

            # optimise quality of all images (e.g. brightness)
            # crop and rotate all images to only OMR form


if __name__ == '__main__' and sys.argv[1] == 'dev':
    pass
