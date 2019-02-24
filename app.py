import sys
from pathlib import Path
import sys
sys.path.append(str(Path.cwd() / 'src'))
from src.gui import process_attendance_register_app


def main():
    process_attendance_register_app.main()


if __name__ == '__main__':
    main()
