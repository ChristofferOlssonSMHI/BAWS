# -*- coding: utf-8 -*-
"""
Created on 2019-05-10 15:41

@author: a002028

"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import os
import re
import sys
import shutil
import win32com.shell.shell as shell
from distutils.dir_util import copy_tree

from datetime import datetime
import pandas as pd

import time
import glob
from . import handlers


class Log:
    """
    """
    def __init__(self, log_list, writer=None, file_path=None):
        self.list = log_list
        self.dict = {d: True for d in log_list}
        self.time_stamps = [pd.Timestamp(d) for d in log_list]
        for ts in self.time_stamps:
            self.dict[ts] = True

        self.writer = writer
        self.file_path = file_path

    def date_in_log(self, date):
        """
        :param date:
        :return:
        """
        if date in self.dict:
            return True
        else:
            return False

    def append_date_to_list(self, date):
        """
        :param date:
        :return:
        """
        if date not in self.dict:
            if type(date) == pd.Timestamp:
                date = date.strftime('%Y%m%d')
            self.list.append(date)
            self.dict[date] = True
            self.dict[pd.Timestamp(date)] = True

    def save(self):
        """
        :return:
        """
        self.writer(dictionary=self.list,
                    out_source=self.file_path,
                    indent=4)


class Settings(object):
    """
    """
    def __init__(self, version_number):
        self.__version__ = version_number
        self.base_directory = os.path.dirname(os.path.realpath(__file__))
        self.settings_directory = os.path.join(self.base_directory, 'etc')
        self.local_settings_folder = os.path.join(os.path.splitdrive(self.base_directory)[0], '\\BAWS')

        self.user = os.path.expanduser('~').split('\\')[-1]
        print('USER: {}'.format(self.user))
        self.user_temporary_folder = os.path.join(os.path.expanduser('~'), 'baws_temp')
        self.create_folder(self.user_temporary_folder)
        self.reset_folder(self.user_temporary_folder)

        self.jh = handlers.JSONHandler()
        self._load_settings()

        self._copy_folders()
        self._load_server_info()
        self.log = None
        self._load_production_log()

        # PROD_system: True or False
        self.PROD_system = False

        # If the user later select to reanalyse data
        self.reanalyse = False

        self.selected_date = None
        self.daytime_start = datetime.strptime('0600', '%H%M').time()
        self.daytime_end = datetime.strptime('1800', '%H%M').time()

        self.stw_handler = handlers.STWHandler(os.path.join(self.settings_directory, 'lats_lons_baws10000_sweref99tm.txt'))

        self.test_handler = handlers.TESTHandler(self)

    def __setattr__(self, name, value):
        """
        Defines the setattr for object self
        :param name: str
        :param value: any kind
        :return:
        """
        if name in ['base_directory', 'settings_directory']:
            pass
        elif isinstance(value, str) and 'etc_root' in value:
            value = value.replace('etc_root', self.settings_directory)
            print(name, value)
        elif isinstance(value, dict) and ('directories' in name or 'file_paths' in name):
            self.set_attributes(self, **value)
        super(Settings, self).__setattr__(name, value)

    def _copy_folders(self):
        """
        :return:
        """
        self.copy_folder_tree(self.server_info_directory, self.local_server_info_directory)

    def change_working_date(self, date):
        """
        :return:
        """
        self.selected_date = date
        print('New working date: %s' % self.selected_date)

    def set_environment(self, gui_func):
        """
        :return:
        """
        user_answer = gui_func(*('BAWS ({}) Question'.format(self.__version__),
                                 'Would you like to set PROD environment? (Yes: PROD, No: TEST)'))
        if user_answer:
            self.PROD_system = True

        self._set_user_selected_directories()

    @staticmethod
    def create_folder(folder_path):
        """
        :param folder_path:
        :return:
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print('Folder created:\n%s' % folder_path)

    @staticmethod
    def reset_folder(folder_path):
        """
        :param folder_path:
        :return:
        """
        start_time = time.time()
        if folder_path.endswith('baws_temp'):
            for filename in os.listdir(folder_path):
                if filename.startswith('Cyano_merged'):
                    continue
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

        print("reset_folder completed in --%.3f sec\n" % (time.time() - start_time))

    @staticmethod
    def copy_folder_tree(src_path, dst_path, overwrite=False):
        """
        :param src_path:
        :param dst_path:
        :return:
        """
        if not os.path.exists(dst_path) or overwrite:
            try:
                copy_tree(src_path, dst_path)
                print('Folder %s copied to %s' % (src_path, dst_path))
            except:
                print('WARNING! Could not copy folder %s' % src_path)

    def check_production_folders(self, gui_func):
        """
        :return:
        """
        self.create_folder(self.baws_USER_SELECTED_current_production_directory)

        if len(os.listdir(self.baws_USER_SELECTED_current_production_directory)) != 0:
            user_answer = gui_func(*('BAWS ({}) Question'.format(self.__version__),
                                     'Would you like to delete all files in the production folder? ({})'.format(
                                         self.baws_USER_SELECTED_current_production_directory)))
            if user_answer:
                for fid in glob.glob(self.baws_USER_SELECTED_current_production_directory + '/*'):
                    os.remove(fid)
                print('All files deleted from folder: {}'.format(self.baws_USER_SELECTED_current_production_directory))
        else:
            print('\nProduction folder is empty and ready to go!\n')

    def _check_for_paths(self, dictionary):
        """
        Since default path settings are set to bawspy base folder
        we need to add that base folder to all paths
        :param dictionary: Dictionary with paths as values and keys as items..
        :return: Updates dictionary with local path (self.dir_path)
        """
        for item, value in list(dictionary.items()):
            if isinstance(value, dict):
                self._check_for_paths(value)
            elif 'directory' in item:
                dictionary[item] = value

    def _load_production_log(self):
        """
        :return:
        """
        log_list = self.jh.read(file_path=self.production_log_file_path)
        self.log = Log(log_list, writer=self.jh.write, file_path=self.production_log_file_path)

    def _load_server_info(self):
        """
        :return:
        """
        settings_path = os.path.join(self.local_server_info_directory, 'srv.json')
        info = self.jh.read(file_path=settings_path)
        self.set_attributes(self, **info)

    def _load_settings(self):
        """
        :param etc_path: str, local path to settings
        :return: Updates attributes of self
        """
        settings_path = os.path.join(self.local_settings_folder, 'baws_settings.json')
        if not os.path.exists(settings_path):
            raise ImportError(
                'Could not load settings file. You need to copy baws_settings.json into the folder: {} (or set your'
                ' own local folder of your choosing). You can find this file under the folder "/algproduktion/"'.format(
                    self.local_settings_folder))

        settings = self.jh.read(file_path=settings_path)
        self.set_attributes(self, **settings)
        print('\nBAWS settings loaded\n')

    def _set_user_selected_directories(self):
        """

        :param prod:
        :param test:
        :return:
        """
        user_selected_directories = [attr for attr in dir(self) if 'USER_SELECTED' in attr]

        if self.PROD_system:
            print('Setting PROD-environment')
            directories_to_copy = {attr: getattr(self, attr) for attr in dir(self) if 'PROD' in attr}
            replace_string = 'PROD'
        else:
            print('Setting TEST-environment')
            directories_to_copy = {attr: getattr(self, attr) for attr in dir(self) if 'TEST' in attr}
            replace_string = 'TEST'

        change_dict = {key: directories_to_copy.get(key.replace('USER_SELECTED', replace_string))
                       for key in user_selected_directories}

        self.set_attributes(self, **change_dict)

    @staticmethod
    def set_attributes(obj, **kwargs):
        """
        With the possibility to add attributes to an object which is not 'self'
        :param obj: object
        :param kwargs: Dictionary
        :return: sets attributes to object
        """
        for key, value in list(kwargs.items()):
            setattr(obj, key, value)

    @staticmethod
    def generate_filepaths(directory, pattern='', not_pattern='DUMMY_PATTERN', pattern_list=[], endswith='',
                           only_from_dir=True):
        """
        :param directory:
        :param pattern:
        :param not_pattern:
        :param pattern_list:
        :param endswith:
        :param only_from_dir:
        :return:
        """
        if os.path.isdir(directory):
            for path, subdir, fids in os.walk(directory):
                if only_from_dir:
                    if path != directory:
                        continue
                for f in fids:
                    if pattern in f and not_pattern not in f and f.endswith(endswith):
                        if any(pattern_list):
                            for pat in pattern_list:
                                if pat in f:
                                    yield os.path.abspath(os.path.join(path, f))
                        else:
                            yield os.path.abspath(os.path.join(path, f))

    @staticmethod
    def generate_dir_paths(directory, pattern='', not_pattern='DUMMY_PATTERN', endswith=''):
        """
        :param directory:
        :param pattern:
        :param not_pattern:
        :param endswith:
        :return:
        """
        for path, subdir, fids in os.walk(directory):
            if not_pattern and not_pattern in path:
                continue

            if pattern:
                if endswith:
                    if pattern in path and path.endswith(endswith):
                        yield path
                else:
                    if pattern in path:
                        yield path
            if endswith and path.endswith(endswith):
                yield path

    def get_timestamp_based_on_working_timestamp(self, delta=1):
        """
        :param delta:
        :return:
        """
        result_timestamp = self.current_working_timestamp - pd.Timedelta('%i days' % delta)
        return result_timestamp.strftime("%Y%m%d")

    @staticmethod
    def get_subdirectories(directory):
        """
        :param directory: str, directory path
        :return: list of existing directories (not files)
        """
        return [subdir for subdir in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, subdir))]

    @staticmethod
    def get_filepaths_from_directory(directory):
        """
        :param directory: str, directory path
        :return: list of files in directory (not sub directories)
        """
        return [''.join([directory, fid]) for fid in os.listdir(directory)
                if not os.path.isdir(directory+fid)]

    def time_filter(self, file_name):
        """
        :param file_name:
        :return:
        """
        time_match = re.search('\d{6}_\d{4}', file_name)
        time = datetime.strptime(time_match.group(), '%y%m%d_%H%M').time()
        if self.daytime_start < time < self.daytime_end:
            # Time ok, no filter passed
            return False
        else:
            # Time not ok, filter passed
            return True

    @property
    def current_working_date(self):
        if self.selected_date:
            return self.selected_date.strftime("%Y%m%d")
        else:
            return self.date_yesterday

    @property
    def current_working_timestamp(self):
        return pd.Timestamp(self.current_working_date)

    @property
    def date_yesterday(self):
        return self.timestamp_yesterday.strftime("%Y%m%d")

    @property
    def date_range_composite(self):
        dr = pd.date_range(self.current_working_timestamp - pd.Timedelta('6 days'), periods=7)
        return [ts.strftime("%Y%m%d") for ts in dr]

    @property
    def time(self):
        return self.timestamp.strftime("%H%M")

    @property
    def timestamp(self):
        return pd.Timestamp.today()

    @property
    def timestamp_yesterday(self):
        return self.timestamp - pd.Timedelta('1 days')

    @property
    def cyano_daymap_path(self):
        if hasattr(self, 'baws_USER_SELECTED_current_production_directory'):
            return os.path.join(self.baws_USER_SELECTED_current_production_directory,
                                'cyano_daymap_{}.shp'.format(self.current_working_date))
        else:
            return None

    @property
    def cyano_weekmap_path(self):
        if hasattr(self, 'baws_USER_SELECTED_current_production_directory'):
            return os.path.join(self.baws_USER_SELECTED_current_production_directory,
                                'cyano_weekmap_{}.shp'.format(self.current_working_date))
        else:
            return None
