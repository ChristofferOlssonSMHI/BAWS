# -*- coding: utf-8 -*-
"""
Created on 2019-05-20 16:42

@author: a002028
"""
import os
import time
from decimal import Decimal, ROUND_HALF_UP
from collections import Mapping
from threading import Thread


def valid_baws_area():
    """Return dictionary with acceptable area (m2) per class label.

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
    """Sleep while a file is under modification.

    Args:
        file_paths: Iterable of file paths.
    """
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
    """Return dictionary with file sizes.

    Args:
        files: Iterable of file paths.
    """
    dictionary = {}
    for path in files:
        dictionary[path] = os.stat(path).st_size
    return dictionary


def round_value(value, nr_decimals=2, out_format=str):
    """Round value.

    Args:
        value: Value to round.
        nr_decimals: Number of decimal values.
        out_format: Eg. str/float
    """
    return out_format(
        Decimal(str(value)).quantize(
            Decimal('%%1.%sf' % nr_decimals % 1),
            rounding=ROUND_HALF_UP
        )
    )


def recursive_dict_update(d, u):
    """Recursive dictionary update.

    Copied from: http://stackoverflow.com/questions/3232943/update-
                 value-of-a-nested-dictionary-of-varying-depth

    Args:
        d: Dictionary to update
        u: New dictionary to insert to d
    """
    for k, v in list(u.items()):
        if isinstance(v, Mapping):
            r = recursive_dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def thread_process(call_function, *args, **kwargs):
    """Thread a given function.

    Args:
        call_function: Function to start.
        *args: Arguments to pass to function.
        **kwargs: Keyword arguments to pass to function.
    """
    Thread(target=call_function, args=args, kwargs=kwargs).start()


def generate_filepaths(directory, pattern='', not_pattern='DUMMY_PATTERN',
                       pattern_list=None, endswith='', only_from_dir=True):
    """"""
    pattern_list = pattern_list or []
    if os.path.isdir(directory):
        for path, subdir, fids in os.walk(directory):
            if only_from_dir:
                if path != directory:
                    continue
            for f in fids:
                if pattern in f and not_pattern not in f and f.endswith(
                        endswith):
                    if any(pattern_list):
                        for pat in pattern_list:
                            if pat in f:
                                yield os.path.abspath(os.path.join(path, f))
                    else:
                        yield os.path.abspath(os.path.join(path, f))


def generate_dir_paths(directory, pattern='', not_pattern='DUMMY_PATTERN',
                       endswith=''):
    """"""
    for path, subdir, fids in os.walk(directory):
        if not_pattern and not_pattern in path:
            continue

        if pattern:
            if endswith:
                if pattern in path and path.endswith(endswith):
                    yield path
            else:
                if pattern in path:
                    yield path
        if endswith and path.endswith(endswith):
            yield path
