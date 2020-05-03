from pathlib import Path
from setuptools import find_packages, setup
from bin import omrx

with open(str(Path(__file__).parent/'VERSION.txt')) as version_file:
    VERSION = version_file.read()

requirements = Path('requirements.txt').read_text()
requirements = '\n'.join([req for req in requirements.split('\n')if 'cx_Freeze' not in req])

setup(
    name="pyomrx",
    version=VERSION,
    author='Shaun Howell',
    author_email='shaunkhowell@gmail.com',
    url='https://github.com/ShaunHowell/py-omrx',
    description=
    "Library and GUI for optical mark recognition form generation and data extraction",
    packages=find_packages(include=['pyomrx', 'pyomrx.*']),
    entry_points={
        'console_scripts': ['omrx = omrx:main'],
    },
    install_requires=requirements,
    tests_require=['pytest']
)

# workaround for cx_freeze naming multiprocessing.pool incorrectly and files which couldn't be excluded...
# Path('build/lib/multiprocessing/Pool.pyc').rename(
#     Path('build/lib/multiprocessing/pool.pyc'))
# shutil.rmtree(str(Path('build/lib/pyomrx/tests')), ignore_errors=True)
