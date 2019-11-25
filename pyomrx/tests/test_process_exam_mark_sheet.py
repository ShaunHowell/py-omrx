import os
from pyomrx.omr.accuracy import *
import pytest
from pathlib import Path
from pyomrx.tests.fixtures import *
from pyomrx.omr.core import response_from_darknesses


def test_good_response_from_darknesses():
    example = [
        0.17548420642142207, 0.21935525802677758, 0.20798128168464836,
        0.15436110750032495, 0.180358767710906, 0.20473157415832574,
        0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
        0.20960613544780968
    ]
    assert response_from_darknesses(example) == 6


def test_no_response_from_darknesses():
    example = [0.1706096451319381, 0.2915782024062279]
    assert response_from_darknesses(example) == -1


def test_double_response_from_darknesses():
    example = [
        0.17548420642142207, 0.21935525802677758, 0.9960353568178864,
        0.15436110750032495, 0.180358767710906, 0.20473157415832574,
        0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
        0.20960613544780968
    ]
    assert response_from_darknesses(example) == -2


def test_middle_ground_abstention_response_from_darknesses():
    example = [0.5, 0.5, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
    assert response_from_darknesses(example) == -3


def test_closeness_abstention_response_from_darknesses():
    example = [0.59, 0.7, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
    assert response_from_darknesses(example) == -3


if __name__ == '__main__':
    pytest.main(['-sxk', 'mark_sheet'])
