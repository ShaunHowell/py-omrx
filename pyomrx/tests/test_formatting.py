import subprocess


def test_src_yapf_formatted():
    assert subprocess.call(['yapf', '--diff', '-r', './pyomrx']) == 0
