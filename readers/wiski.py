# -*- coding: utf-8 -*-
"""
Created on 2019-10-29 10:09

@author: a002028

"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
import pandas as pd
import datetime as dt

import urllib.request, urllib.error, urllib.parse
import xml.dom.minidom as minidom


class WiskiBase(object):
    def __init__(self):
        super(WiskiBase, self).__init__()
        self._site = 'server'
        self._field = '200'
        self._station = None
        self._parameter = None
        self._channel = None
        self._time_window = None
        self._offset = 0

    def update_attributes(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        for attribute, value in list(kwargs.items()):
            setattr(self, attribute, value)

    @staticmethod
    def url_combo_join(join_list, join_chr='/'):
        return join_chr.join(join_list)

    @property
    def url(self):
        return '/'.join([self.site, self.field, self.station, self.parameter, self.channel, self.time_window])

    @property
    def site(self):
        return self._site

    @site.setter
    def site(self, value):
        self._site = value

    @property
    def field(self):
        return self._field

    @field.setter
    def field(self, value):
        self._field = value

    @property
    def station(self):
        return self._station

    @station.setter
    def station(self, value):
        self._station = str(value)

    @property
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self, value):
        self._parameter = value

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def time_window(self):
        return self._time_window

    @time_window.setter
    def time_window(self, start_stop):
        start = start_stop[0]
        end = start_stop[-1]
        if type(start) == pd.Timestamp:
            start = start.isoformat()
        if type(end) == pd.Timestamp:
            end = end.isoformat()
        self._time_window = ''.join(['?from=', start, '&to=', end])


class WiskiHandler(WiskiBase):
    """

    """
    def __init__(self, server=''):
        super(WiskiHandler, self).__init__()
        self.site = server

    def get_wiski_record(self):
        """
        :param station_nr: int, station number
        :param parameter: str, parameter
        :param tname: str, channel to data
        :param start: pd.Timestamp().isoformat()
        :param end: pd.Timestamp().isoformat()
        :return: xml.dom.minicompat.NodeList
        """
        print('WiskiHandler.get_wiski_record: retrieving record for parameter %s..' % self.parameter)
        result = urllib.request.urlopen(urllib.request.Request(self.url))
        doc = minidom.parse(result)
        resRecords = doc.getElementsByTagName("timeseriesValueList")[0].getElementsByTagName("timeseriesvalue")

        return resRecords

    def get_wiski_data(self, station_nr, parameter, tname, start, end):
        """
        :param station_nr: int, station number
        :param parameter: str, parameter
        :param tname: str, channel to data
        :param start: pd.Timestamp().isoformat()
        :param end: pd.Timestamp().isoformat()
        :return: pd.DataFrame()
        """
        print('WiskiHandler.get_wiski_data: get wiski data including geoinfo..')
        self.update_attributes(**{'station': station_nr, 'parameter': parameter,
                                  'channel': tname, 'time_window': (start, end)})
        data_records = self.get_wiski_record()

        self.update_attributes(**{'parameter': 'LATX'})
        latitude_records = self.get_wiski_record()

        self.update_attributes(**{'parameter': 'LONX'})
        longitude_records = self.get_wiski_record()

        print('WiskiHandler.get_wiski_data: extracting data from %i number of rows..' % len(data_records))
        data_out = []
        for i in range(len(data_records)):
            ts = float(data_records[i].attributes["timestamp"].value)
            row_data = [pd.Timestamp(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=ts)),
                        data_records[i].childNodes[0].data,
                        data_records[i].attributes["quality"].value,
                        latitude_records[i].childNodes[0].data,
                        longitude_records[i].childNodes[0].data]
            data_out.append(row_data)

        df = pd.DataFrame(data_out, columns=['time', 'value', 'quality', 'latitude', 'longitude'])
        print('WiskiHandler.get_wiski_data: process completed. Returning pandas.DataFrame')

        return df
