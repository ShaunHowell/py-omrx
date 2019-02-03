from pathlib import Path
import os
import sys
from cx_Freeze import setup, Executable
import matplotlib
import opcode
import shutil

VIRTUALENV_PYTHON_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(VIRTUALENV_PYTHON_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(VIRTUALENV_PYTHON_DIR, 'tcl', 'tk8.6')

SYSTEM_PYTHON_DLLS_FOLDER = str(Path(opcode.__file__).parent.parent / 'DLLs')
SYSTEM_PYTHON_LIB_FOLDER = str(Path(opcode.__file__).parent.parent / 'Lib')

options = {
    'build_exe': {
        'includes': [
            'omr_tool.omr',
            'omr_tool.gui',
            'omr_tool.default_configs',
            'omr_tool.omr.utils.visualisation'
        ],
        'path': sys.path + ['modules'],
        # explicitly include packages which cx_freeze doesn't find
        'packages': ["numpy",
                     "scipy",
                     "matplotlib.backends.backend_tkagg"
                     ],
        "excludes": [
            "scipy.spatial.cKDTree",  # bug: cKDTree causes ckdtree to not copy
            "distutils",  # because of virtualenv
            "omr_tool.demo",
            "omr_tool.tests",
        ],
        "include_files": [(matplotlib.get_data_path(), "mpl-data"),
                          os.path.join(SYSTEM_PYTHON_DLLS_FOLDER, 'tk86t.dll'),  # this might not be needed
                          os.path.join(SYSTEM_PYTHON_DLLS_FOLDER, 'tcl86t.dll'),  # this might not be needed
                          os.path.join(SYSTEM_PYTHON_DLLS_FOLDER, 'sqlite3.dll'),
                          (os.path.join(SYSTEM_PYTHON_LIB_FOLDER, 'distutils'), 'distutils')
                          ],
        "build_exe": 'build'
    }
}

target = Executable(script="app.py",
                    base="Win32GUI" if sys.platform == "win32" else None,
                    icon='logo.ico',
                    targetName='run.exe'
                    )
if Path('build/').exists():
    shutil.rmtree(str(Path('build/')))
setup(name="omr_tool",
      version="1.0",
      description="Tool for extracting data from attendance registers by optical mark recognition",
      options=options,
      executables=[target])

# hacky workaround for cx_freeze naming multiprocessing.pool incorrectly and files which couldn't be excluded...
Path('build/lib/multiprocessing/Pool.pyc').rename(Path('build/lib/multiprocessing/pool.pyc'))
shutil.rmtree(str(Path('build/lib/omr_tool/demo')))
shutil.rmtree(str(Path('build/lib/omr_tool/tests')))
shutil.make_archive('omr_tool.zip', 'zip', 'build')
shutil.copy(str(Path('build_res/vcruntime140.dll')),str(Path('build/vcruntime140.dll')))
