# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:09

@author: a002028

"""
from __future__ import print_function

from builtins import object
import geopandas as gp
import qgis
from qgis.core import QgsVectorFileWriter
import qgis


class GeoPandasShapeWriterBase(object):
    """
    """
    def __init__(self):
        super(GeoPandasShapeWriterBase, self).__init__()

    @staticmethod
    def write(layer, **kwargs):
        """
        :param layer:
        :param kwargs:
        :return:
        """
        layer.to_file(**kwargs)


class QGISShapeWriterBase(object):
    """
    """
    def __init__(self):
        super(QGISShapeWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """
        *args should equal (layer, output_path, "utf-8", None, "ESRI Shapefile")
        :param args:
        :param kwargs:
        :return:
        """
        QgsVectorFileWriter.writeAsVectorFormat(*args, **kwargs)


class NoneWriterBase(object):
    """
    Dummy base
    """
    def __init__(self):
        super(NoneWriterBase, self).__init__()

    def write(self, layer, *args, **kwargs):
        # fix_print_with_import
        print(('Warning! No shape was written due to unrecognizable datatype:', type(layer)))


def shape_writer(writer_type, *args, **kwargs):
    """
    :param layer:
    :param args:
    :param kwargs:
    :return:
    """
    if writer_type is 'geopandas':
        base = GeoPandasShapeWriterBase
    elif writer_type is 'qgis':
        base = QGISShapeWriterBase
    else:
        base = NoneWriterBase

    class ShapeWriter(base):
        """
        """
        def __init__(self):
            super(ShapeWriter, self).__init__()

    sw = ShapeWriter()
    sw.write(*args, **kwargs)
