# -*- coding: utf-8 -*-
"""
Created on 2019-06-25 17:36

@author: a002028
"""


def replace_directory(src_path, dst_path, remove_func, copy_func):
    """"""
    try:
        remove_func(dst_path)
    except:
        print('Could not replace directory: %s ' % dst_path)
    try:
        copy_func(src_path, dst_path)
    except:
        print('Could not replace directory: %s ' % dst_path)
