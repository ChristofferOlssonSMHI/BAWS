# -*- coding: utf-8 -*-
"""
Created on 2019-07-22 15:12

@author: a002028

"""

import os


def generate_filepaths(directory, pattern='', not_pattern='DUMMY_PATTERN', pattern_list=[], endswith='',
                       only_from_dir=True):
    """
    :param directory:
    :param pattern:
    :param not_pattern:
    :param pattern_list:
    :param endswith:
    :param only_from_dir:
    :return:
    """
    for path, subdir, fids in os.walk(directory):
        if only_from_dir:
            if path != directory:
                continue
        for f in fids:
            if pattern in f and not_pattern not in f and f.endswith(endswith):
                if any(pattern_list):
                    for pat in pattern_list:
                        if pat in f:
                            yield os.path.abspath(os.path.join(path, f))
                else:
                    yield os.path.abspath(os.path.join(path, f))


def get_file_sizes(files):
    """
    :param files:
    :return:
    """
    dictionary = {}
    for path in files:
        dictionary[path] = os.stat(path).st_size
    return dictionary


if __name__ == "__main__":
    directory = 'ovning'
    generator = generate_filepaths(directory, pattern='cyano_union_bloom',  #'cyano_union_bloom'
                                   pattern_list=['20190711', '20190712', '20190713', '20190714',
                                                 '20190715', '20190716', '20190717'],
                                   endswith='.shp')
    file_sizes = get_file_sizes(generator)

    sorted_files = sorted(file_sizes, key=lambda k: file_sizes[k], reverse=True)