# -*- coding: utf-8 -*-
"""
Created on 2019-05-16 15:09

@author: a002028
"""
from qgis.core import QgsVectorFileWriter


class GeoPandasShapeWriterBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(GeoPandasShapeWriterBase, self).__init__()

    @staticmethod
    def write(layer, **kwargs):
        """"""
        layer.to_file(**kwargs)


class QGISShapeWriterBase:
    """"""

    def __init__(self):
        """Initialize."""
        super(QGISShapeWriterBase, self).__init__()

    @staticmethod
    def write(*args, **kwargs):
        """Write to shp file.

        *args should equal (layer, output_path, "utf-8", None, "ESRI Shapefile")
        """
        QgsVectorFileWriter.writeAsVectorFormat(*args, **kwargs)


class NoneWriterBase:
    """Dummy base."""

    def __init__(self):
        """Initialize."""
        super(NoneWriterBase, self).__init__()

    def write(self, layer, *args, **kwargs):
        """"""
        print('Warning! No shape was written due to unrecognizable datatype:',
              type(layer))


def shape_writer(writer_type, *args, **kwargs):
    """"""
    if writer_type is 'geopandas':
        base = GeoPandasShapeWriterBase
    elif writer_type is 'qgis':
        base = QGISShapeWriterBase
    else:
        base = NoneWriterBase

    class ShapeWriter(base):
        """"""

        def __init__(self):
            """Initialize."""
            super(ShapeWriter, self).__init__()

    sw = ShapeWriter()
    sw.write(*args, **kwargs)
