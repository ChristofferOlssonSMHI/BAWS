# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:07

@author: a002028
"""
from qgis.core import QgsVectorLayer
import geopandas as gp


class QGISShapeReaderBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(QGISShapeReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """"""
        layer = QgsVectorLayer(*args)
        if not layer.isValid():
            print("Layer failed to load!")
        else:
            return layer


class GeoPandasReaderBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(GeoPandasReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """"""
        return gp.read_file(*args, **kwargs)


class NoneReaderBase:
    """Dummy base."""

    def __init__(self):
        """Initialize."""
        super(NoneReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """"""
        print('Warning! No shape was read due to unrecognizable datatype')


def shape_reader(reader_type, *args, **kwargs):
    """"""
    if reader_type is 'geopandas':
        base = GeoPandasReaderBase
    elif reader_type is 'qgis':
        base = QGISShapeReaderBase
    else:
        base = NoneReaderBase

    class ShapeReader(base):
        """"""

        def __init__(self):
            """Initialize."""
            super(ShapeReader, self).__init__()

    sr = ShapeReader()
    return sr.read(*args, **kwargs)
