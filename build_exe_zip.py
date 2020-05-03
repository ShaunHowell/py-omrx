'''
Script which uses cx freeze to build an exe and zip files for running and distributing on windows
Usage: python build_exe_zip.py build_exe
'''

import shutil
from pathlib import Path
import os
import sys
from setuptools import find_packages
from cx_Freeze import setup, Executable
import matplotlib
import opcode


if Path('build/').exists():
    shutil.rmtree(str(Path('build/')))

version_file_path = str(Path(__file__).parent/'VERSION.txt')
VIRTUALENV_PYTHON_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(VIRTUALENV_PYTHON_DIR, 'tcl',
                                         'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(VIRTUALENV_PYTHON_DIR, 'tcl', 'tk8.6')

SYSTEM_PYTHON_DLLS_FOLDER = str(Path(opcode.__file__).parent.parent / 'DLLs')
SYSTEM_PYTHON_LIB_FOLDER = str(Path(opcode.__file__).parent.parent / 'Lib')
options = {
    'build_exe': {
        'includes': [
            'pyomrx'
        ],
        'path':
            sys.path + ['modules'],
        # explicitly include packages which cx_freeze doesn't find
        'packages': ["numpy", "scipy", "matplotlib.backends.backend_tkagg"],
        "excludes": [
            "scipy.spatial.cKDTree",  # bug: cKDTree causes ckdtree to not copy
            "distutils",  # because of virtualenv
            "tests",
        ],
        "include_files": [
            (matplotlib.get_data_path(), "mpl-sub_form_data"),
            os.path.join(SYSTEM_PYTHON_DLLS_FOLDER,
                         'tk86t.dll'),
            os.path.join(SYSTEM_PYTHON_DLLS_FOLDER,
                         'tcl86t.dll'),
            (os.path.join(SYSTEM_PYTHON_LIB_FOLDER, 'distutils'), 'distutils'),
            (version_file_path, 'lib/VERSION.txt')
        ],
        "build_exe":
            'build',
        "include_msvcr": True
    }
}
target = Executable(
    script="app.py",
    base="Win32GUI" if sys.platform == "win32" else None,
    icon='res/logo.ico',
    targetName='run.exe')

with open(version_file_path) as version_file:
    VERSION = version_file.read()


setup(
    name="pyomrx",
    version=VERSION,
    author='Shaun Howell',
    author_email='shaunkhowell@gmail.com',
    url='https://github.com/ShaunHowell/py-omrx',
    description=
    "Library and GUI for optical mark recognition form generation and data extraction",
    options=options,
    packages=find_packages(include=['pyomrx', 'pyomrx.*']),
    executables=[target],
    install_requires=Path('requirements.txt').read_text(),
    tests_require=['pytest']
)

# workaround for cx_freeze naming multiprocessing.pool incorrectly and files which couldn't be excluded...
# Path('build/lib/multiprocessing/Pool.pyc').rename(
#     Path('build/lib/multiprocessing/pool.pyc'))
# shutil.rmtree(str(Path('build/lib/pyomrx/tests')), ignore_errors=True)


shutil.make_archive(
    str(Path(f'build/py-omrx-{VERSION}')), 'zip', str(Path('build/')))
