# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:27

@author: a002028

"""
from shutil import copyfile
import os

import pandas as pd

from .. import readers
from .. import writers
from .. import utils
from .auto_texting import DayTexting, WeekTexting


class TextFileHandler:
    """"""

    def __init__(self, settings, auto=False, daymap_path=None):
        """Initialize.

        Args:
            settings:
        """
        self.settings = settings
        self.user_name = settings.user_name_mapping.get(
            self.settings.user, '<...>')
        self.auto_generate = auto
        self.daymap_path = daymap_path.replace('.shp', '.tiff')
        self.weekmap_path = self.daymap_path.replace('_daymap_', '_weekmap_')
        print('self.daymap_path', self.daymap_path)
        print('self.weekmap_path', self.weekmap_path)

    def adjust_text(self, text):
        """"""
        text[0][0] = text[0][0].format(
            START_DATE=self.settings.date_range_composite[0],
            END_DATE=self.settings.date_range_composite[-1],
            USER_NAME=self.user_name
        )
        return text

    def copy_empty_files(self):
        """"""
        print('\nCopying textfiles to: %s'
              % self.settings.baws_USER_SELECTED_current_production_directory)
        pattern = 'BASE_TEXT'
        files_to_copy = utils.generate_filepaths(
            self.settings.settings_directory,
            pattern=pattern,
            only_from_dir=False
        )
        texting_kwargs = dict(
            user=self.user_name,
            text_mapper=self.settings.auto_texting,
            daymap_path=self.daymap_path,
            weekmap_path=self.weekmap_path,
            start_date=self.settings.date_range_composite[0],
            end_date=self.settings.date_range_composite[-1]
        )
        for fid in files_to_copy:
            file_name = os.path.basename(fid)
            file_name = file_name.replace(
                pattern, self.settings.current_working_date)
            dst_path = os.path.join(
                self.settings.baws_USER_SELECTED_current_production_directory,
                file_name
            )
            if 'drift_' not in file_name:
                if self.auto_generate:
                    auto_txt_class = DayTexting if 'daymap' in file_name \
                        else WeekTexting
                    text_obj = auto_txt_class(
                        self.settings.district_path,  **texting_kwargs)
                    text_str = text_obj.get_text(
                        lang='swe' if '_swe' in file_name else 'eng')
                    text = pd.DataFrame({0: [text_str]})
                else:
                    text = readers.text_reader(
                        'pandas', fid,
                        sep='\t',
                        header=None,
                        encoding='utf-8'
                    )
                    text = self.adjust_text(text)
                self._write(text, dst_path)
            else:
                copyfile(fid, dst_path)

        print('Files created!\n')

    def _write(self, text, dst_path):
        """"""
        writers.text_writer(
            'pandas', dst_path,
            df=text,
            sep='\t',
            index=None,
            header=None,
            encoding='utf-8'
        )
