from pathlib import Path
import shutil
import pyomrx
import subprocess

VERSION = pyomrx.__version__

if Path('build/').exists():
    shutil.rmtree(str(Path('build/')))

assert subprocess.call("python setup.py build_exe") == 0, 'exe build failed'

# shutil.copy(
#     str(Path('lib/vcruntime140.dll')), str(Path('build/vcruntime140.dll')))

shutil.make_archive(
    str(Path(f'build/py-omrx-{VERSION}')), 'zip', str(Path('build/')))
