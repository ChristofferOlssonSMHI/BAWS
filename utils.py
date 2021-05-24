# -*- coding: utf-8 -*-
"""
Created on 2019-05-20 16:42

@author: a002028

"""
from __future__ import print_function

from builtins import str
import os
import time
from decimal import Decimal, ROUND_HALF_UP
from collections import Mapping
from threading import Thread


def valid_baws_area():
    """
    valid_area = 5000000 m2 (5 pixels (1km3 x 1km3))
    1: valid_area * 2
    2: valid_area
    3: valid_area
    4: valid_area * 100

    1: cloud (grey)
    2: subsurface bloom (yellow)
    3: surface bloom (orange)
    4: no data on satellite scene (black)
    """
    return {
        1: 10000000,
        2: 5000000,
        3: 5000000,
        4: 500000000
    }


def sleep_while_saving(file_paths):
    changes = {path: os.path.getmtime(path) for path in file_paths}
    change = True
    while change:
        change = False
        for f in file_paths:
            if changes.get(f) != os.path.getmtime(f):
                # fix_print_with_import
                print("File {} has been modified".format(f))
                changes[f] = os.path.getmtime(f)
                change = True
        if change:
            time.sleep(0.1)


def get_file_sizes(files):
    """
    :param files:
    :return:
    """
    dictionary = {}
    for path in files:
        dictionary[path] = os.stat(path).st_size
    return dictionary


def round_value(value, nr_decimals=2, out_format=str):
    """
    Calculate rounded value
    :param value:
    :param nr_decimals:
    :param out_format:
    :return:
    """
    return out_format(Decimal(str(value)).quantize(Decimal('%%1.%sf' % nr_decimals % 1), rounding=ROUND_HALF_UP))


def recursive_dict_update(d, u):
    """
    Recursive dictionary update using
    Copied from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        via satpy
    :param d: Dictionary to update
    :param u: New dictionary to insert to d
    :return: d updated with u
    """
    for k, v in list(u.items()):
        if isinstance(v, Mapping):
            r = recursive_dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def thread_process(call_function, *args, **kwargs):
    """
    :param call_function:
    :param args:
    :param kwargs:
    :return:
    """
    Thread(target=call_function, args=args, kwargs=kwargs).start()
