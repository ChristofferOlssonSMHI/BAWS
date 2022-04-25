# -*- coding: utf-8 -*-
"""
Created on 2019-05-10 15:41

@author: a002028
"""
import os
import re
import glob
import shutil
from pathlib import Path
from distutils.dir_util import copy_tree

from datetime import datetime
import pandas as pd

from . import handlers
from . import utils
from .__init__ import __version__


class Log:
    """Logger for BAWS."""

    def __init__(self, log_list, writer=None, file_path=None):
        """Initialize.

        Args:
            log_list: Present log.
            writer: Writer instance.
            file_path: Path to file.
        """
        self.list = log_list
        self.dict = {}
        for d in log_list:
            self.dict[d] = True
            self.dict[pd.Timestamp(d)] = True
        self.writer = writer
        self.file_path = file_path

    def date_in_log(self, date):
        """Return True or False.

        Args:
            date: str or timestamp.
        """
        return date in self.dict

    def append_date_to_list(self, date):
        """Add date to log list and dictionary.

        Args:
            date: str or timestamp.
        """
        if date not in self.dict:
            if type(date) == pd.Timestamp:
                date = date.strftime('%Y%m%d')
            self.list.append(date)
            self.dict[date] = True
            self.dict[pd.Timestamp(date)] = True

    def save(self):
        """Write log to file."""
        self.writer(dictionary=self.list,
                    out_source=self.file_path,
                    indent=4)


class Settings:
    """The BAWS settings class."""

    def __init__(self):
        """Initialize."""
        self.base_directory = Path(__file__).parent
        self.settings_directory = self.base_directory.joinpath('etc')
        self.local_settings_folder = Path(
            '/'.join((self.base_directory.drive, 'BAWS'))
        )
        self.user = Path('~').expanduser().parts[-1]
        self.user_temporary_folder = Path('~').expanduser().joinpath(
            'baws_temp')
        self.create_folder(self.user_temporary_folder)
        utils.thread_process(self.reset_folder, self.user_temporary_folder)

        self.jh = handlers.JSONHandler()
        self._load_settings()

        self.copy_folder_tree(self.server_info_directory,
                              self.local_server_info_directory)
        # self._load_server_info()
        self.log = None
        self._load_production_log()

        # PROD_system: True or False
        self.PROD_system = False

        # If the user later select to reanalyse data
        self.reanalyse = False

        self.selected_date = None
        self.daytime_start = datetime.strptime('0600', '%H%M').time()
        self.daytime_end = datetime.strptime('1800', '%H%M').time()

        self.baws_10000_paths = [
            self.settings_directory.joinpath('longitude_baws10000.npy'),
            self.settings_directory.joinpath('latitude_baws10000.npy')
        ]

        self.test_handler = handlers.TESTHandler(self)
        print('USER: {}'.format(self.user))

    def __setattr__(self, name, value):
        """Defines the setattr for self."""
        if name in ['base_directory', 'settings_directory']:
            pass
        elif isinstance(value, str) and 'etc_root' in value:
            value = value.replace('etc_root', str(self.settings_directory))
            print(name, value)
        elif isinstance(value, dict) and (
                'directories' in name or 'file_paths' in name):
            self.set_attributes(self, **value)
        super(Settings, self).__setattr__(name, value)

    def change_working_date(self, date):
        """Change current date.

        The selected_date is used when loading data.

        Args:
            date (str): Date (YYYY-MM-DD)
        """
        self.selected_date = date
        print(f'New working date: {self.selected_date}')

    def set_environment(self, gui_func):
        """User selection of environment (PROD/TEST)."""
        user_answer = gui_func(*(f'BAWS ({__version__}) Question',
                                 'Would you like to set PROD environment?'
                                 ' (Yes: PROD, No: TEST)'))
        if user_answer:
            self.PROD_system = True

        self._set_user_selected_directories()

    @staticmethod
    def create_folder(folder_path):
        """Create directory if it doesn't exists."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print('Folder created:\n%s' % folder_path)

    @staticmethod
    def reset_folder(folder_path):
        """Reset the 'baws_tempo' folder."""
        folder_path = str(folder_path)
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

    @staticmethod
    def copy_folder_tree(src_path, dst_path, overwrite=False):
        """Copy directory tree."""
        src_path = str(src_path)
        dst_path = str(dst_path)
        if not os.path.exists(dst_path) or overwrite:
            try:
                copy_tree(src_path, dst_path)
                print('Folder %s copied to %s' % (src_path, dst_path))
            except:
                print('WARNING! Could not copy folder %s' % src_path)

    def check_production_folders(self, gui_func):
        """User choice about cleaning the selected production folder.

        If yes: All data will be deleted in the working production folder.
        """
        self.create_folder(self.baws_USER_SELECTED_current_production_directory)

        if len(os.listdir(
                self.baws_USER_SELECTED_current_production_directory)) != 0:
            user_answer = gui_func(
                f'BAWS ({__version__}) Question',
                f'Would you like to delete all files in the production folder? '
                f'({self.baws_USER_SELECTED_current_production_directory})'
            )
            if user_answer:
                for fid in glob.glob(
                        self.baws_USER_SELECTED_current_production_directory + '/*'):
                    utils.thread_process(os.remove, fid)
                    # os.remove(fid)
                print(f'All files deleted from folder: '
                      f'{self.baws_USER_SELECTED_current_production_directory}')
        else:
            print('\nProduction folder is empty and ready to go!\n')

    def _load_production_log(self):
        """Initialize log."""
        log_list = self.jh.read(file_path=self.production_log_file_path)
        self.log = Log(log_list, writer=self.jh.write,
                       file_path=self.production_log_file_path)

    def _load_server_info(self):
        """WISKI sever info.

        WISKI data is currently not used in BAWS.
        """
        settings_path = os.path.join(self.local_server_info_directory,
                                     'srv.json')
        info = self.jh.read(file_path=settings_path)
        self.set_attributes(self, **info)

    def _load_settings(self):
        """Updates attributes of self."""
        settings_path = os.path.join(self.local_settings_folder,
                                     'baws_settings.json')
        if not os.path.exists(settings_path):
            raise ImportError(
                'Could not load settings file. You need to copy '
                'baws_settings.json into the folder: {} (or set your '
                'own local folder of your choosing). You can find this file '
                'under the folder "/algproduktion/"'.format(
                    self.local_settings_folder)
            )

        settings = self.jh.read(file_path=settings_path)
        self.set_attributes(self, **settings)
        print('\nBAWS settings loaded\n')

    def _set_user_selected_directories(self):
        """Set selected directories to use during BAWS work event."""
        user_selected_directories = [attr for attr in dir(self)
                                     if 'USER_SELECTED' in attr]

        if self.PROD_system:
            print('Setting PROD-environment')
            directories_to_copy = {attr: getattr(self, attr)
                                   for attr in dir(self) if 'PROD' in attr}
            replace_string = 'PROD'
        else:
            print('Setting TEST-environment')
            directories_to_copy = {attr: getattr(self, attr)
                                   for attr in dir(self) if 'TEST' in attr}
            replace_string = 'TEST'

        change_dict = {
            key: directories_to_copy.get(key.replace('USER_SELECTED',
                                                     replace_string))
            for key in user_selected_directories
        }

        self.set_attributes(self, **change_dict)

    @staticmethod
    def set_attributes(obj, **kwargs):
        """Set attributes to self."""
        for key, value in list(kwargs.items()):
            setattr(obj, key, value)

    def time_filter(self, file_name):
        """Return True|False.

        Check if the file name match time string of selected date.
        """
        time_match = re.search(r'\d{6}_\d{4}', file_name)
        time = datetime.strptime(time_match.group(), '%y%m%d_%H%M').time()
        if self.daytime_start < time < self.daytime_end:
            # Time ok, no filter passed
            return False
        else:
            # Time not ok, filter passed
            return True

    @property
    def data_in_production_folder_with_working_date(self):
        """Return True|False.

        Check if the created cyano_daymap_path is a file.
        """
        return os.path.isfile(self.cyano_daymap_path)

    @property
    def current_working_date(self):
        """Return date string of the working date."""
        if self.selected_date:
            return self.selected_date.strftime("%Y%m%d")
        else:
            return self.date_yesterday

    @property
    def current_working_timestamp(self):
        """Return pandas timestamp of the working date."""
        return pd.Timestamp(self.current_working_date)

    @property
    def date_yesterday(self):
        """Return date string for yesterday."""
        return self.timestamp_yesterday.strftime("%Y%m%d")

    @property
    def date_range_composite(self):
        """Return list of dates for the weekly composite product."""
        dr = pd.date_range(self.current_working_timestamp -
                           pd.Timedelta('6 days'), periods=7)
        return [ts.strftime("%Y%m%d") for ts in dr]

    @property
    def time(self):
        """Return time string of right now."""
        return self.today.strftime("%H%M")

    @property
    def today(self):
        """Return pandas timestamp of right now."""
        return pd.Timestamp.today()

    @property
    def timestamp_yesterday(self):
        """Return pandas timestamp of yesterday."""
        return self.today - pd.Timedelta('1 days')

    @property
    def cyano_daymap_path(self):
        """Return path of the daily cyano product."""
        if hasattr(self, 'baws_USER_SELECTED_current_production_directory'):
            return os.path.join(
                self.baws_USER_SELECTED_current_production_directory,
                f'cyano_daymap_{self.current_working_date}.shp'
            )
        else:
            return None

    @property
    def cyano_weekmap_path(self):
        """Return path of the weekly cyano product."""
        if hasattr(self, 'baws_USER_SELECTED_current_production_directory'):
            return os.path.join(
                self.baws_USER_SELECTED_current_production_directory,
                f'cyano_weekmap_{self.current_working_date}.shp'
            )
        else:
            return None
