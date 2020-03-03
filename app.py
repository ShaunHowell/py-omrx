from pathlib import Path
import sys
sys.path.append(str(Path.cwd() / 'pyomrx'))
from pyomrx.gui.app import main

if __name__ == '__main__':
    main()
