# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:10

@author: a002028
"""
import numpy as np
import pandas as pd


class PandasWriterBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(PandasWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """"""
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


class NumpyWriterBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(NumpyWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """"""
        np.savetxt(*args, **kwargs)


class NoneWriterBase:
    """Dummy base."""

    def __init__(self):
        """Initialize."""
        super(NoneWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """"""
        print('Warning! No text was written due to unrecognizable datatype')


def text_writer(writer_type, *args, **kwargs):
    """"""
    if writer_type is 'pandas':
        base = PandasWriterBase
    elif writer_type is 'numpy':
        base = NumpyWriterBase
    else:
        base = NoneWriterBase

    class TextWriter(base):
        """"""

        def __init__(self):
            """Initialize."""
            super(TextWriter, self).__init__()

    tw = TextWriter()
    tw.write(*args, **kwargs)
