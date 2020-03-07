from pathlib import Path
import os
import sys
from cx_Freeze import setup, Executable
import matplotlib
import opcode
import shutil
import pyomrx

VERSION = pyomrx.__version__

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
            (matplotlib.get_data_path(), "mpl-data"),
            os.path.join(SYSTEM_PYTHON_DLLS_FOLDER,
                         'tk86t.dll'),
            os.path.join(SYSTEM_PYTHON_DLLS_FOLDER,
                         'tcl86t.dll'),
            (os.path.join(SYSTEM_PYTHON_LIB_FOLDER, 'distutils'), 'distutils')
        ],
        "build_exe":
        'build'
    }
}

target = Executable(
    script="app.py",
    base="Win32GUI" if sys.platform == "win32" else None,
    icon='res/logo.ico',
    targetName='run.exe')
if Path('build/').exists():
    shutil.rmtree(str(Path('build/')))

setup(
    name="pyomrx",
    version=VERSION,
    description=
    "Library and GUI for optical mark recognition form generation and data extraction",
    options=options,
    executables=[target])

# hacky workaround for cx_freeze naming multiprocessing.pool incorrectly and files which couldn't be excluded...
# Path('build/lib/multiprocessing/Pool.pyc').rename(
#     Path('build/lib/multiprocessing/pool.pyc'))
# shutil.rmtree(str(Path('build/lib/pyomrx/tests')), ignore_errors=True)
shutil.copy(
    str(Path('lib/vcruntime140.dll')), str(Path('build/vcruntime140.dll')))
shutil.make_archive(
    str(Path(f'build/py-omrx-{VERSION}')), 'zip', str(Path('build/')))
