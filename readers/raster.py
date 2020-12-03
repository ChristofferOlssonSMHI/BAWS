# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:07

@author: a002028

"""
from __future__ import print_function

from builtins import object
from qgis.core import QgsRasterLayer
import geopandas as gp


class QGISRasterReaderBase(object):
    """
    """
    def __init__(self):
        super(QGISRasterReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        layer = QgsRasterLayer(*args)
        if not layer.isValid():
            print("Layer failed to load!")
        else:
            return layer


class GeoPandasRasterReaderBase(object):
    """
    """
    def __init__(self):
        super(GeoPandasRasterReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        return gp.read_file(*args, **kwargs)


class NoneReaderBase(object):
    """
    Dummy base
    """
    def __init__(self):
        super(NoneReaderBase, self).__init__()

    def read(self, *args, **kwargs):
        print('Warning! No shape was read due to unrecognizable datatype')


def raster_reader(reader_type, *args, **kwargs):
    """
    :param reader_type:
    :param args:
    :param kwargs:
    :return:
    """
    if reader_type is 'geopandas':
        base = GeoPandasRasterReaderBase
    elif reader_type is 'qgis':
        base = QGISRasterReaderBase
    else:
        base = NoneReaderBase

    class RasterReader(base):
        """
        """
        def __init__(self):
            super(RasterReader, self).__init__()

    rr = RasterReader()
    return rr.read(*args, **kwargs)
