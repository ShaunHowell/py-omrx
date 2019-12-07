from pyomrx.omr.omr_factory import OmrFactory
import pytest
import json
from pathlib import Path


@pytest.fixture
def omr_factory_1(res_folder):
    config = json.load(
        open(str(Path(res_folder) / 'form_config' / 'omr_config.json')))
    return OmrFactory(config)


def test_process_images_folder(res_folder, omr_factory_1):
    image_folder_path = str(Path(res_folder) / 'example_images_folder')
    df = omr_factory_1.process_images_folder(image_folder_path)
    print(df.to_string())
    trues = [(0, 'A00'), (-1, 'A00'), (0, 'dropout00'), (-1, 'dropout00')]
    for i, j in trues:
        assert df[j].iloc[i] == True


if __name__ == '__main__':
    pytest.main(['-k', 'test_omr_factory', '-s'])
