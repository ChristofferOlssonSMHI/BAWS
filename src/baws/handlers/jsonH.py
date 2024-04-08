# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:13

@author: a002028
"""
import json


class JSONHandler:
    """"""

    @staticmethod
    def write(dictionary=None, out_source='', indent=4):
        """"""
        dictionary = dictionary or {}
        with open(out_source, "w") as outfile:
            json.dump(dictionary, outfile, indent=indent)

    @staticmethod
    def read(file_path=''):
        """"""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
        print('file loaded: {}'.format(file_path))
        return json_file
