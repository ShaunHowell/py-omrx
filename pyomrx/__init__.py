from pathlib import Path
with open(str(Path(__file__).parent.parent / 'VERSION.txt')) as version_file:
    __version__ = version_file.read()

IMAGE_SUFFIXES = ['.png', '.jpg', 'jpeg', '.PNG', '.JPG', '.JPEG']

from pyomrx.core.omr_factory import OmrFactory
from pyomrx.core.form_maker import FormMaker
