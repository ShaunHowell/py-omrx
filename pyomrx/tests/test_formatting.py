import subprocess
import pyomrx


def test_src_yapf_formatted():
    assert subprocess.call(['yapf', '--diff', '-r', './pyomrx']) == 0


def test_version_bumped():
    tags = subprocess.run(
        ['git', 'tag'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
    assert not any([pyomrx.__version__ in tag for tag in tags])
