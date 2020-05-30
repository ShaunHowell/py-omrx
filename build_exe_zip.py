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

version_file_path = str(Path(__file__).parent / 'VERSION.txt')
PYTHON_FOLDER_ROOT = Path(os.__file__).parent.parent
print(f'python root folder: {PYTHON_FOLDER_ROOT}')
TCL_PATH = PYTHON_FOLDER_ROOT / 'tcl' / 'tcl8.6'
TK_PATH = PYTHON_FOLDER_ROOT / 'tcl' / 'tk8.6'
if TCL_PATH.exists():
    print(f'tcl8.6 exists at path {TCL_PATH}')
else:
    raise FileNotFoundError(f'{TCL_PATH} does not exist')
if TK_PATH.exists():
    print(f'tk8.6 exists at path {TK_PATH}')
else:
    raise FileNotFoundError(f'{TK_PATH} does not exist')

os.environ['TCL_LIBRARY'] = str(TCL_PATH)
os.environ['TK_LIBRARY'] = str(TK_PATH)

SYSTEM_PYTHON_DLLS_FOLDER = str(Path(opcode.__file__).parent.parent / 'DLLs')
SYSTEM_PYTHON_LIB_FOLDER = str(Path(opcode.__file__).parent.parent / 'Lib')
TK_DLL_PATH = Path(SYSTEM_PYTHON_DLLS_FOLDER) / 'tk86t.dll'
TCL_DLL_PATH = Path(SYSTEM_PYTHON_DLLS_FOLDER) / 'tcl86t.dll'
if TK_DLL_PATH.exists():
    print(f'tk8.6t.dll exists at path {TK_DLL_PATH}')
else:
    raise FileNotFoundError(f'{TK_DLL_PATH} does not exist')
if TCL_DLL_PATH.exists():
    print(f'tcl86t.dll exists at path {TCL_DLL_PATH}')
else:
    raise FileNotFoundError(f'{TCL_DLL_PATH} does not exist')

with open(version_file_path) as version_file:
    VERSION = version_file.read()
build_root = f'build/pyomrx_{VERSION}'
options = {
    'build_exe': {
        'includes': ['pyomrx', 'tkinter', 'matplotlib.backends.backend_tkagg'],
        'path':
        sys.path + ['modules'],
        # explicitly include packages which cx_freeze doesn't find
        'packages': ["numpy", "scipy", "matplotlib.backends.backend_tkagg", 'tkinter'],
        "excludes": [
            "scipy.spatial.cKDTree",  # bug: cKDTree causes ckdtree to not copy
            "distutils",  # because of virtualenv
            "tests"
        ],
        "include_files": [(matplotlib.get_data_path(), "mpl-sub_form_data"),
                          str(TK_DLL_PATH),
                          str(TCL_DLL_PATH),
                          (os.path.join(SYSTEM_PYTHON_LIB_FOLDER,
                                        'distutils'), 'distutils'),
                          (version_file_path, 'lib/VERSION.txt')],
        "build_exe":
        build_root,
        "include_msvcr":
        True
    }
}
target = Executable(
    script="app.py",
    base="Win32GUI" if sys.platform == "win32" else None,
    icon='res/logo.ico',
    targetName='run.exe')

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
    tests_require=['pytest'])

# workaround for cx_freeze naming multiprocessing.pool incorrectly
Path(f'{build_root}/lib/multiprocessing/Pool.pyc').rename(
    Path(f'{build_root}/lib/multiprocessing/pool.pyc'))
# workaround for tkinter being called Tkinter
os.rename(f'{build_root}/lib/Tkinter', f'{build_root}/lib/tkinter')
os.makedirs('dist', exist_ok=True)
shutil.make_archive(
    str(Path(f'dist/py-omrx-{VERSION}')), 'zip', build_root)
