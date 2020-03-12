import cv2
from pyomrx.core.exceptions import *
import os
import pandas as pd
from pyomrx.core.form import OmrForm
from pathlib import Path
import pyomrx
from pyomrx.core.exceptions import EmptyFolderException
from pyomrx.core.meta import Abortable
from pubsub import pub
from pyomrx.gui import DATA_EXTRACTION_TOPIC
import zipfile
import json


class OmrFactory(Abortable):
    @classmethod
    def from_omr_file(cls, omr_file_path):
        omr_template = zipfile.ZipFile(omr_file_path, 'r')
        template_json = omr_template.read('omr_config.json')
        template_dict = json.loads(template_json.decode())
        return OmrFactory(template_dict)

    def __init__(self, form_config, abort_event=None, id=None):
        Abortable.__init__(self, abort_event)
        self.id = id
        self.form_config = form_config

    def process_images_folder(self, input_folder_path, output_file_path=None):
        dfs = []
        failed_paths = []
        image_paths = [
            image_path for image_path in Path(input_folder_path).iterdir()
            if image_path.suffix in pyomrx.IMAGE_SUFFIXES
        ]
        if not image_paths:
            raise EmptyFolderException(
                f'no images found in {input_folder_path}. '
                f'Supported extensions are{pyomrx.IMAGE_SUFFIXES}')
        for image_path in image_paths:
            try:
                self.raise_for_abort()
                form = OmrForm(
                    str(image_path),
                    self.form_config,
                    abort_event=self.abort_event)
                dfs.append(form.df)
                pub.sendMessage(f'{self.id}.{DATA_EXTRACTION_TOPIC}')
            except (CircleParseError, cv2.error, OmrException) as e:
                print(f'failed to parse circles in {image_path}')
                print(f'error: {e}')
                failed_paths.append(image_path)
        if not dfs:
            raise EmptyFolderException(
                f'no data extracted from images in {input_folder_path}')
        folder_df = pd.concat(dfs, axis=0)
        fail_df = pd.DataFrame([{
            'file': file_path.name
        } for file_path in failed_paths],
                               columns=folder_df.columns.tolist())
        if folder_df.index.name:
            fail_df.index.name = folder_df.index.name
        fail_df['omr_error'] = True
        folder_df = pd.concat([folder_df, fail_df], axis=0)
        if output_file_path:
            output_file_path = Path(output_file_path)
            if not output_file_path.parent.exists():
                os.makedirs(str(output_file_path.parent))
            folder_df.to_csv(str(output_file_path))
        return folder_df
