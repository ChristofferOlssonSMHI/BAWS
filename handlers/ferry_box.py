# -*- coding: utf-8 -*-
"""
Created on 2019-10-29 09:38

@author: a002028

"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import range
import os
import pandas as pd
import numpy as np
import geopandas as gp
from shapely.geometry import Point, Polygon, MultiPolygon

from .boolean import BaseBoolean
from .. import readers
from .. import writers


def explode(indf):
    outdf = gp.GeoDataFrame(columns=indf.columns)
    for idx, row in indf.iterrows():
        if type(row.geometry) == Polygon:
            outdf = outdf.append(row, ignore_index=True)
        if type(row.geometry) == MultiPolygon:
            multdf = gp.GeoDataFrame(columns=indf.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row] * recs, ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom, 'geometry'] = row.geometry[geom]
            outdf = outdf.append(multdf, ignore_index=True)
    return outdf


class FerryBoxHandler(BaseBoolean):
    """

    """
    def __init__(self, settings):
        super(FerryBoxHandler, self).__init__()
        self.settings = settings
        self.wh = readers.WiskiHandler(server=self.settings.server_wiski)

        self.data = None

    def read(self):
        """
        :return:
        """
        station = 38055  # TAVASTLAND
        parameter = 'PHYC'  # Phycocyanin
        channel = 'Cmd'
        start = self.settings.current_working_timestamp
        end = self.settings.current_working_timestamp + pd.Timedelta('1 days')

        self.data = self.wh.get_wiski_data(station, parameter, channel, start, end)
        self.data[['value', 'latitude', 'longitude']] = self.data[['value', 'latitude', 'longitude']].astype(np.float)

    def write(self, gdf):
        """
        :return:
        """
        print('Writing ferrybox-data to file..')
        file_name = 'ferry_box_data_{}_sweref99tm_cyano.shp'.format(self.settings.current_working_date)
        file_path = os.path.join(self.settings.user_temporary_folder, file_name)
        kwargs = {'filename': file_path,
                  'driver': 'ESRI Shapefile',
                  'crs': self.settings.crs_wkt,
                  'encoding': 'utf-8'}
        writers.shape_writer('geopandas', gdf, **kwargs)
        print('ferrybox-data to file..')

    def process(self):
        """
        :return:
        """
        self.exclude_data_based_on_location()
        if self.data.empty:
            print('No usable ferrybox data')
            return False

        self.set_time_index()
        self.resample(resample_time='5min')
        self.add_numeric_operation_to_resampled_data(operation='mean')
        self.exclude_data_based_on_value('value', 0.25)

        if self.data.empty:
            print('No usable ferrybox data')
            return False

        self.add_class_values(self.data)
        gdf = self.get_geodataframe()
        self.write(gdf)
        return True

    @staticmethod
    def add_class_values(df):
        """
        FerryBox data are measured at approximately 3 meters, therefor we set classification 2 (subsurface bloom)
        :return:
        """
        df['class'] = 2

    def exclude_data_based_on_value(self, key, value):
        """
        :return:
        """
        self.add_boolean_greater_or_equal(key, value)
        self.data = self.data.loc[self.boolean, :]
        self.reset_boolean()

    def exclude_data_based_on_location(self):
        """
        :return:
        """
        self.add_boolean_less_or_equal('latitude', 63.5)
        self.data = self.data.loc[self.boolean, :]
        self.reset_boolean()

    def set_time_index(self):
        """
        :return:
        """
        self.data = self.data.set_index('time')

    def resample(self, resample_time='5min'):
        """
        :param resample_time:
        :return:
        """
        self.data = self.data.resample(resample_time)

    def add_numeric_operation_to_resampled_data(self, operation='mean'):
        """
        :param operation:
        :return:
        """
        if operation == 'mean':
            self.data = self.data.mean()
        elif operation == 'sum':
            self.data = self.data.sum()
        elif operation == 'min':
            self.data = self.data.min()
        elif operation == 'max':
            self.data = self.data.max()

    def get_geodataframe(self):
        """
        :return:
        """
        print('Creating geodataframe for ferrybox data..')
        self.data['geometry'] = list(zip(self.data['longitude'], self.data['latitude']))
        self.data['geometry'] = self.data['geometry'].apply(Point)
        self.data = self.data.reset_index(drop=True)
        geoframe = gp.GeoDataFrame(self.data, geometry='geometry')
        geoframe.crs = self.settings.crs_epsg_4326
        geoframe = geoframe.to_crs(self.settings.crs_epsg_3006)
        geoframe['geometry'] = geoframe.buffer(2000)  # .envelope  # Converts Points to Polygon with a buffer of 1000 meters
        geoframe = geoframe.dissolve(by='class')
        geoframe = explode(geoframe)
        self.add_class_values(geoframe)

        return geoframe
