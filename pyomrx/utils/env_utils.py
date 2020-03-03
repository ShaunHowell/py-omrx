import os


def debug_mode():
    return os.environ.get('debug', '').lower() == 'true'
