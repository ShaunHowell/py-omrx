import pytest
from pyomrx.core.form import *
import json


@pytest.fixture
def omr_form_1(res_folder):
    image_path = str(Path(res_folder) / 'example_omr_form_scan_1.png')
    config = json.load(
        open(str(Path(res_folder) / 'form_config' / 'omr_config.json')))
    return OmrForm(image_path, config)


def test_omr_form_1_metadata(omr_form_1):
    correct_values = {'class_name': 3, 'institution': 1, 'page': 1}
    assert omr_form_1.metadata_values == correct_values


def test_omr_form_1_data(omr_form_1):
    columns = ['dropout00'] + [f'A{i:02}' for i in range(31)]
    correct_values = pd.DataFrame(
        np.zeros([25, 32]).astype(bool), columns=columns)
    for i, j in [(0, 0), (0, 1), (0, 2), (0, 15), (0, 31), (12, 15), (-1, 0),
                 (-1, 1), (-1, 2), (-1, -1)]:
        correct_values.iloc[i, j] = True
    correct_values = correct_values.sort_index(axis=1)
    print(correct_values.to_string())
    assert omr_form_1.data.equals(correct_values)


if __name__ == '__main__':
    pytest.main(['-k', 'test_omr_form_1_data', '-s'])
