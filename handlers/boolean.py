# -*- coding: utf-8 -*-
"""
Created on 2019-08-30 15:05

@author: a002028

"""
from builtins import object
import numpy as np


class BaseBoolean(object):
    """

    """
    def __init__(self):
        super(BaseBoolean, self).__init__()
        self.data = None
        self._boolean = True

    def add_boolean_duplicated(self, parameter):
        """
        :param param:
        :return:
        """
        self.boolean = self.data[parameter].duplicated()

    def add_boolean_from_list(self, parameter, value_list):
        """
        :param parameter:
        :param value_list:
        :return: Adds boolean to self.boolean. See property: self.boolean
        """
        self.boolean = self.data[parameter].isin(value_list)

    def add_boolean_month(self, month):
        """
        :param month:
        :return:
        """
        self.boolean = self.data['timestamp'].dt.month == month

    def add_boolean_month_list(self, month_list):
        """
        :param month:
        :return:
        """
        self.boolean = self.data['timestamp'].dt.month.isin(month_list)

    def add_boolean_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] == value

    def add_boolean_greater_or_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] >= value

    def add_boolean_less_or_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] <= value

    def add_boolean_isnan(self, param):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param].isna()

    def add_boolean_notnan(self, param):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param].notna()
        try:
            self.boolean = self.data[param] != ''
        except:
            pass

    def reset_boolean(self):
        """
        Resets boolean to True
        :return:
        """
        self._boolean = True

    @property
    def index(self):
        """
        :return: indices
        """
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        """
        :return: Boolean
        """
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """
        :param add_bool: new boolean
        :return: Sets a combined boolean
        """
        self._boolean = self._boolean & add_bool
