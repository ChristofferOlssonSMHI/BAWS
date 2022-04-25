# -*- coding: utf-8 -*-
"""
Created on 2019-09-19 14:40

@author: a002028

"""
import os
import pandas as pd
from .. import readers
from .. import writers


class ReanalysisHandler:
    """"""

    def __init__(self, settings):
        """Initialize.

        Args:
            settings:
        """
        self.settings = settings
        self.df = readers.text_reader(
            'pandas', self.settings.reanalysis_log_directory,
            sep='\t',
            header=0,
            encoding='cp1252'
        )

    def change_working_date(self):
        """"""
        selected_date = pd.Timestamp(self.current_date)
        self.settings.change_working_date(selected_date)

    def update_file(self):
        """"""
        self.df.loc[self.path_boolean, 'processed'] = 'Yes'
        self._write()
        print('\nFile updated!\n')

    def _write(self):
        """"""
        writers.text_writer(
            'pandas', self.settings.reanalysis_log_directory,
            df=self.df,
            sep='\t',
            index=None,
            header=True,
            encoding='cp1252'
        )

    @property
    def current_date(self):
        """"""
        return ''.join(filter(str.isdigit, str(self.current_filename)))

    @property
    def current_filename(self):
        """"""
        return os.path.basename(self.current_file_path)

    @property
    def current_file_path(self):
        """"""
        return self.df.loc[self.processed_boolean, 'file_path'].iloc[0]

    @property
    def processed_boolean(self):
        """"""
        return self.df['processed'] == 'No'

    @property
    def path_boolean(self):
        """"""
        return self.df['file_path'] == self.current_file_path
