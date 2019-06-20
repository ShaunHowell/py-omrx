from pathlib import Path
import os


def make_folder_if_not_exists(folder):
    folder_path = Path(folder)
    if not folder_path.exists():
        os.makedirs(str(folder_path))
