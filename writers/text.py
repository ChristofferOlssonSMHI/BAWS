# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:10

@author: a002028

"""
from __future__ import print_function
from builtins import object
import numpy as np
import pandas as pd


class PandasWriterBase(object):
    """
    """
    def __init__(self):
        super(PandasWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """
        :param layer:
        :param args:
        :param kwargs:
        :return:
        """
        if 'df' in kwargs:
            df = kwargs['df']
            del kwargs['df']
        else:
            for key in kwargs:
                if type(kwargs[key] is pd.core.frame.DataFrame):
                    df = kwargs[key]
                    del kwargs[key]
                    break
        if 'df' in locals():
            df.to_csv(*args, **kwargs)
        else:
            print('Could not identify any dataframe within kwargs')


class NumpyWriterBase(object):
    """
    """
    def __init__(self):
        super(NumpyWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        np.savetxt(*args, **kwargs)


class NoneWriterBase(object):
    """
    Dummy base
    """
    def __init__(self):
        super(NoneWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        print('Warning! No text was written due to unrecognizable datatype')


def text_writer(writer_type, *args, **kwargs):
    """
    :param layer:
    :param args:
    :param kwargs:
    :return:
    """
    if writer_type is 'pandas':
        base = PandasWriterBase
    elif writer_type is 'numpy':
        base = NumpyWriterBase
    else:
        base = NoneWriterBase

    class TextWriter(base):
        """
        """
        def __init__(self):
            super(TextWriter, self).__init__()

    tw = TextWriter()
    tw.write(*args, **kwargs)
