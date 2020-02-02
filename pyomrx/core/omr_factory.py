import datetime
import os
from pathlib import Path
import pandas as pd
from pyomrx.core.form import OmrForm
from pathlib import Path
import pyomrx
from pyomrx.core.exceptions import EmptyFolderException
from threading import Event
from pyomrx.core.meta import Abortable
from pubsub import pub
from pyomrx.gui import DATA_EXTRACTION_TOPIC


class OmrFactory(Abortable):
    def __init__(self, form_config, abort_event=None, id=None):
        Abortable.__init__(self, abort_event)
        self.id = id
        self.form_config = form_config

    def process_images_folder(self, input_folder_path, output_file_path=None):
        dfs = []
        for image_path in Path(input_folder_path).iterdir():
            self.raise_for_abort()
            if image_path.suffix not in pyomrx.IMAGE_SUFFIXES:
                print(f'{image_path} is not an image, skipping')
                continue
            form = OmrForm(
                str(image_path),
                self.form_config,
                abort_event=self.abort_event)
            dfs.append(form.df)
            pub.sendMessage(f'{self.id}.{DATA_EXTRACTION_TOPIC}')
        if not dfs:
            raise EmptyFolderException(
                f'no images found in {input_folder_path}')
        folder_df = pd.concat(dfs, axis=0)
        if output_file_path:
            output_file_path = Path(output_file_path)
            if not output_file_path.parent.exists():
                os.makedirs(str(output_file_path.parent))
            folder_df.to_csv(str(output_file_path))
        return folder_df
