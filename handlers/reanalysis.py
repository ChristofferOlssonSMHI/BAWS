# -*- coding: utf-8 -*-
"""
Created on 2019-09-19 14:40

@author: a002028

"""
from __future__ import print_function
from builtins import filter
from builtins import str
from builtins import object
import os
import pandas as pd
from .. import readers
from .. import writers


class ReanalysisHandler(object):
    """

    """
    def __init__(self, settings):
        self.settings = settings

        args = (self.settings.reanalysis_log_directory,)
        kwargs = {'sep': '\t', 'header': 0, 'encoding': 'cp1252'}
        self.df = readers.text_reader('pandas', *args, **kwargs)

    def change_working_date(self):
        """
        :return:
        """
        selected_date = pd.Timestamp(self.current_date)
        self.settings.change_working_date(selected_date)

    def update_file(self):
        """
        :return:
        """
        self.df.loc[self.path_boolean, 'processed'] = 'Yes'
        self._write()
        print('\nFile updated!\n')

    def _write(self):
        """
        :return:
        """
        args = (self.settings.reanalysis_log_directory, )
        kwargs = {'df': self.df, 'index': False, 'header': True, 'encoding': 'cp1252', 'sep': '\t'}
        writers.text_writer('pandas', *args, **kwargs)

    @property
    def current_date(self):
        """
        :return:
        """
        return ''.join(filter(str.isdigit, str(self.current_filename)))

    @property
    def current_filename(self):
        """
        :return:
        """
        return os.path.basename(self.current_file_path)

    @property
    def current_file_path(self):
        """
        :param self:
        :return:
        """
        return self.df.loc[self.processed_boolean, 'file_path'].iloc[0]

    @property
    def processed_boolean(self):
        """
        :return:
        """
        return self.df['processed'] == 'No'

    @property
    def path_boolean(self):
        """
        :return:
        """
        return self.df['file_path'] == self.current_file_path
