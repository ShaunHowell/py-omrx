from pathlib import Path
import sys
sys.path.append(str(Path.cwd() / 'pyomrx'))
from pyomrx.gui import pyomrx_gui


def main():
    pyomrx_gui.main()


if __name__ == '__main__':
    main()
