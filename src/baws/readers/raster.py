# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:07

@author: a002028
"""
from qgis.core import QgsRasterLayer


class QGISRasterReaderBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(QGISRasterReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """"""
        layer = QgsRasterLayer(*args)
        if not layer.isValid():
            print("Layer failed to load!")
        else:
            return layer


class NoneReaderBase:
    """Dummy base."""

    def __init__(self):
        """Initialize."""
        super(NoneReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """"""
        print('Warning! No shape was read due to unrecognizable datatype')


def raster_reader(reader_type, *args, **kwargs):
    """"""
    if reader_type is 'qgis':
        base = QGISRasterReaderBase
    else:
        base = NoneReaderBase

    class RasterReader(base):
        """"""

        def __init__(self):
            """Initialize."""
            super(RasterReader, self).__init__()

    rr = RasterReader()
    return rr.read(*args, **kwargs)
