import pytest
from pyomrx.core.form import *


@pytest.fixture
def omr_sub_form_1(res_folder):
    image_path = str(Path(res_folder) / 'omr_sub_form.png')
    image = load_and_check_image(image_path)
    template = {
        'circles': [{
            'rectangle': {
                'top': 0.03846153846153845,
                'bottom': 0.9999999999999999,
                'left': 0.30977734753146174,
                'right': 1.0
            },
            'allowed_row_filling':
            'many',
            'column_prefix':
            'A',
            'radius':
            0.008976157082748949,
            'circles_per_row': [
                31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31,
                31, 31, 31, 31, 31, 31, 31, 31, 31
            ],
            'possible_columns':
            31,
            'name':
            'attendance'
        },
                    {
                        'rectangle': {
                            'top': 0.03846153846153845,
                            'bottom': 0.9999999999999999,
                            'left': 0.2749273959341723,
                            'right': 0.30977734753146174
                        },
                        'allowed_row_filling':
                        'many',
                        'column_prefix':
                        'dropout',
                        'radius':
                        0.01029239766081871,
                        'circles_per_row': [
                            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                            1, 1, 1, 1, 1, 1, 1, 1
                        ],
                        'possible_columns':
                        1,
                        'name':
                        'dropout'
                    }],
        'metadata_requirements': {}
    }

    return OmrSubForm(image, template)


def test_omr_sub_form_1_data(omr_sub_form_1):
    columns = ['dropout00'] + [f'A{i:02}' for i in range(31)]
    correct_values = pd.DataFrame(
        np.zeros([25, 32]).astype(bool), columns=columns)
    correct_values.iloc[0, 0] = True
    correct_values.iloc[0, 1] = True
    correct_values.iloc[0, -1] = True
    correct_values.iloc[-1, -1] = True
    correct_values.iloc[-1, 0] = True
    correct_values.iloc[-1, 1] = True
    correct_values.iloc[12, 16] = True
    correct_values = correct_values.sort_index(axis=1)
    print(correct_values.to_string())
    assert omr_sub_form_1.values.equals(correct_values)


if __name__ == '__main__':
    pytest.main(['-k', 'test_omr_sub_form_1_data', '-s'])
