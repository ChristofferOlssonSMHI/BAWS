# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:13

@author: a002028

"""
from __future__ import print_function
from builtins import zip
from builtins import object
import numpy as np
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsPoint, QgsField, QgsVectorLayer, QgsFeature, QgsGeometry
from .. import readers


class STWHandler(object):
    """
    """
    def __init__(self, path):
        self.coordframe = pd.read_csv(path, sep='\t', header=0)
        for key in self.coordframe:
            self.coordframe[key] = self.coordframe[key].astype(float)

    def _reset_coords(self, method='qgis'):
        """
        :return:
        """
        if method in ['geopandas', 'shapely']:
            self.coordframe['Coordinates'] = list(zip(self.coordframe.lon_sweref, self.coordframe.lat_sweref))
            self.coordframe['Coordinates'] = self.coordframe['Coordinates'].apply(Point)
            self.geocoordframe = gp.GeoDataFrame(self.coordframe, geometry='Coordinates')
            self.geocoordframe['geometry'] = self.coordframe['Coordinates'].apply(lambda x: x.coords[0])
        else:
            PointList = []
            for index, row in self.coordframe.iterrows():
                sweref_point = QgsPoint(row['lon_sweref'], row['lat_sweref'])
                PointList.append(sweref_point)

            attr = ("Point?crs=epsg:3006", "baws_points", "memory")
            self.coordlayer = readers.shape_reader('qgis', *attr)
            vpr = self.coordlayer.dataProvider()
            attributes = [QgsField('b_points', QVariant.Int)]
            vpr.addAttributes(attributes)
            self.coordlayer.updateFields()

            self.coordlayer.startEditing()
            features = []
            for p in PointList:
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPoint(p))
                feature.setAttributes([1])
                features.append(feature)

            vpr.addFeatures(features)
            self.coordlayer.commitChanges()

    def _get_index_list_using_shapely(self, filter_shapes):
        """
        :param filter_shapes:
        :return:
        """
        selected = []
        for poly in filter_shapes['geometry']:
            try:
                if poly.is_valid:
                    for i, point in enumerate(self.geocoordframe['Coordinates']):
                        if poly.contains(point):
                            selected.append(i)
            except ValueError:
                print('Warning! Null geometry in shapefile', poly)

        return selected

    def _get_index_list_using_qgis(self, selected_features):
        """
        :param selected_features:
        :return:
        """
        indices = []
        for feat in selected_features:
            if feat.geometry() is None:
                continue
            poly = feat.geometry()
            for i, coord_feat in enumerate(self.coordlayer.getFeatures()):
                coord_geom = coord_feat.geometry()
                if poly.contains(coord_geom) or poly.touches(coord_geom):
                    indices.append(i)
        return indices

    def extract_point_info(self, path, gui_func, polygon_key='class', value_list=[3], file_tag='', method='qgis'):
        """
        :param path:
        :param polygon_key:
        :param value_list:
        :param file_tag:
        :param using_geopandas:
        :return:
        """
        if not hasattr(self, 'coordframe') or (method != 'qgis' and not hasattr(self, 'geocoordframe')):
            self._reset_coords(method=method)

        if method in ['geopandas', 'shapely']:
            shapes = gp.read_file(path)
            print('Searching for points in polygons..')
            filter_boolean = shapes[polygon_key].isin(value_list)
            if len(filter_boolean) == 0:
                gui_func('No large surface accumulations and therefore no drift forecast is needed.')
                print('No large surface accumulations were found. No STW file saved.')
                return

            print('Creating STW file...')
            filter_shapes = shapes.loc[filter_boolean]
            filter_shapes.reset_index(drop=True, inplace=True)
        else:
            filter_shapes = None
            args = (path, path.split('\\')[-1], "ogr")
            layer = readers.shape_reader('qgis', *args)
            selected_features = [feat for feat in layer.getFeatures() if feat[polygon_key] in value_list]
            if len(selected_features) == 0:
                gui_func('No large surface accumulations and therefore no drift forecast is needed.')
                print('No large surface accumulations were found. No STW file saved.')
                return

        if method == 'geopandas':
            spatial_join = gp.sjoin(self.geocoordframe, filter_shapes, how="inner", op='intersects')
            index_list = spatial_join.index
        elif method == 'shapely':
            index_list = self._get_index_list_using_shapely(filter_shapes)
        elif method == 'qgis':
            index_list = self._get_index_list_using_qgis(selected_features)
        else:
            index_list = 0

        if len(index_list) > 5:  # or len(np.where(filter_boolean)[0]) > 5:
            print('Saving STW file')
            df_pos = pd.DataFrame(self.coordframe.loc[index_list, ['lat_wgs84', 'lon_wgs84']])
            # path = '\\'.join([p for p in path.split('\\')[:-1]]) + '\\' + '_'.join(['stw_', file_tag]) + '.txt'
            path = os.path.join(
                os.path.join(path.split('\\')[:-1]),
                ''.join(['stw_', file_tag, '.txt'])
            )

            df_pos.to_csv(path, sep='\t', header=None, index=False, encoding='cp1252')
            gui_func('A SeaTrackWeb file have been saved. '
                     'Perform forecast on stw.smhi.se',
                     picture_path=':/plugins/BAWS/resources/stw_pic.png')
        else:
            gui_func('No large surface accumulations and therefore no drift forecast is needed.')
            print('No large surface accumulations were found. No STW file saved.')
