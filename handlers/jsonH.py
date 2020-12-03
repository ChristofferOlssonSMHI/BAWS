# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:13

@author: a002028

"""
from __future__ import print_function
from builtins import object
import json


class JSONHandler(object):
    """
    - Import json
    - Export to json
    - Find dictionary within json file based on a specific key
    - Add elements to dictionary
    - Fill up json/dictionary structure with relevant/desired information
    """
    @staticmethod
    def write(dictionary={}, out_source='', indent=4):
        """
        :param dictionary: dict
        :param out_source: str
        :param indent:
        :return:
        """
        with open(out_source, "w") as outfile:
            json.dump(dictionary, outfile, indent=indent)

    @staticmethod
    def read(file_path=u''):
        """
        :param file_path:
        :return: will be either a list of dictionaries or one single dictionary
                 depending on what the json file includes
        """
        with open(file_path, 'r') as f:
            json_file = json.load(f)
        print('file loaded: {}'.format(file_path))
        return json_file
