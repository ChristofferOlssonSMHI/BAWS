# -*- coding: utf-8 -*-
"""
Created on 2019-06-11 16:50

@author: a002028

"""
from __future__ import print_function
from builtins import object
import os
import time
from .. import utils
from .. import readers
from .. import writers


class StatHandler(object):
    """
    """
    def __init__(self, settings, objects=[]):
        self.settings = settings
        self.objects = objects

    def _queue(self):
        """
        :return:
        """
        while not all([obj.active_area for obj in self.objects]):
            time.sleep(0.1)
        return

    def _get_dictionary(self):
        """
        :return:
        """
        dictionary = {}
        for obj in self.objects:
            dictionary = utils.recursive_dict_update(dictionary, obj.area_dict)
        return dictionary

    def save_statistics(self):
        """
        :param dictionary:
        :return:
        """
        self._queue()
        dictionary = self._get_dictionary()
        dictionary = {self.settings.current_working_date: dictionary}
        statistics_path = os.path.join(self.settings.baws_USER_SELECTED_statistics_directory, 'baws_statistics.json')
        if os.path.isfile(statistics_path):
            stat_file = self.settings.jh.read(statistics_path)
        else:
            stat_file = {}

        stat_file = utils.recursive_dict_update(stat_file, dictionary)
        self.settings.jh.write(dictionary=stat_file, out_source=statistics_path)
        print('New statistics saved!')
        print('\nBAWS task completed!')

    def _write(self, text, dst_path):
        """
        :param text:
        :param dst_pat:
        :return:
        """
        args = (dst_path, )
        kwargs = {'df': text, 'index': None, 'header': None, 'encoding': 'utf-8'}
        writers.text_writer('pandas', *args, **kwargs)
