# -*- coding: utf-8 -*-
"""
Created on 2019-08-30 15:05

@author: a002028

"""
import numpy as np


class BaseBoolean:
    """"""

    def __init__(self):
        """Initialize."""
        super(BaseBoolean, self).__init__()
        self.data = None
        self._boolean = True

    def add_boolean_duplicated(self, parameter):
        """"""
        self.boolean = self.data[parameter].duplicated()

    def add_boolean_from_list(self, parameter, value_list):
        """
        :param parameter:
        :param value_list:
        :return: Adds boolean to self.boolean. See property: self.boolean
        """
        self.boolean = self.data[parameter].isin(value_list)

    def add_boolean_month(self, month):
        """"""
        self.boolean = self.data['timestamp'].dt.month == month

    def add_boolean_month_list(self, month_list):
        """"""
        self.boolean = self.data['timestamp'].dt.month.isin(month_list)

    def add_boolean_equal(self, param, value):
        """"""
        self.boolean = self.data[param] == value

    def add_boolean_greater_or_equal(self, param, value):
        """"""
        self.boolean = self.data[param] >= value

    def add_boolean_less_or_equal(self, param, value):
        """"""
        self.boolean = self.data[param] <= value

    def add_boolean_isnan(self, param):
        """"""
        self.boolean = self.data[param].isna()

    def add_boolean_notnan(self, param):
        """"""
        self.boolean = self.data[param].notna()
        try:
            self.boolean = self.data[param] != ''
        except:
            pass

    def reset_boolean(self):
        """Resets boolean to True."""
        self._boolean = True

    @property
    def index(self):
        """"""
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        """"""
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """Sets a combined boolean."""
        self._boolean = self._boolean & add_bool
