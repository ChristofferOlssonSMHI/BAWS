# -*- coding: utf-8 -*-
"""
Created on 2019-06-17 12:34

@author: a002028
"""
from shutil import copyfile
from .. import readers
from .. import writers
from .. import utils
import os


class TESTHandler:
    """TEST as in TEST-file-server."""

    def __init__(self, settings):
        """Initialize.

        Args:
            settings:
        """
        self.settings = settings

    def _get_adjusted_text(self, text, swedish=False):
        """"""
        if swedish:
            text[0][0] = text[0][0].replace('Utfärdat av: <...>',
                                            'Utfärdat av: T. TEST')
            text[0][0] = text[0][0].replace(
                '<...>',
                'TEST-text för datum %s.' % self.settings.current_working_date
            )
        else:
            text[0][0] = text[0][0].replace('Written by: <...>',
                                            'Written by: T. TEST')
            text[0][0] = text[0][0].replace(
                '<...>',
                'TEST-text for date %s.' % self.settings.current_working_date
            )
        return text

    def adjust_text(self, file_name):
        """"""
        text = readers.text_reader(
            'pandas', file_name,
            sep='\t',
            header=None,
            encoding='utf-8'
        )
        lang = 'swe' in file_name
        try:
            text = self._get_adjusted_text(text, swedish=lang)
        except:
            print('\nCould not adjust text string for file %s' % file_name)
        return text

    def copy_prod_files_to_test_system(self):
        """"""
        files_to_copy = utils.generate_filepaths(
            self.settings.baws_USER_SELECTED_current_production_directory,
            pattern=self.settings.current_working_date,
            only_from_dir=True
        )

        for fid in files_to_copy:
            file_name = os.path.basename(fid)
            dst_path = os.path.join(
                self.settings.baws_TEST_manuell_algtolkning_directory,
                file_name
            )
            if file_name.endswith('.txt') and 'stw' not in file_name:
                text = self.adjust_text(fid)
                self._write(text, dst_path)
            else:
                copyfile(fid, dst_path)

        print('Files copied to test environment\n')

    def _write(self, text, dst_path):
        """"""
        writers.text_writer(
            'pandas', dst_path,
            df=text,
            index=None,
            header=None,
            encoding='utf-8'
        )
