# -*- coding: utf-8 -*-

"""
/***************************************************************************
 BAWS
                                 A QGIS plugin
 Manully adjust algae maps
                              -------------------
        begin                : 2019-04-17
        copyright            : (C) 2019 by SMHI
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from __future__ import absolute_import

from builtins import filter
from builtins import object
__author__ = 'SMHI'
__date__ = '2019-04-17'
__copyright__ = '(C) 2019 by SMHI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from .__init__ import __version__

import os
import sys

from itertools import chain
import inspect
import pandas as pd
import time

from .baws_provider import BAWSProvider
from .config import Settings
from .utils import thread_process

from qgis.PyQt.QtCore import QCoreApplication, QDate, Qt
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (QAction,
                                 QFileDialog,
                                 QMessageBox,
                                 QMainWindow,
                                 QWidget,
                                 QVBoxLayout,
                                 QCalendarWidget,
                                 QLabel,
                                 QPushButton)
import qgis

from qgis.core import (QgsVectorLayer,
                       QgsField,
                       QgsProject,
                       QgsProcessingProvider,
                       QgsApplication)

# IMPORTANT TO LOAD resources in order to reach pictures etc..
from . import resources

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from . import readers
from . import handlers
from . import subprocesses


def arrange_layer_order(layers):
    """
    QgsProject.instance().legendLayersAdded.connect(arrange_layer_order)
    :param layers:
    :return:
    """
    root = QgsProject.instance().layerTreeRoot()
    order = root.customLayerOrder()
    for layer in layers:
        if '_coastline_' not in layer.name():
            print('new layer:', layer.name())
            order.insert(1, order.pop())  # New layer to second position
    root.setCustomLayerOrder(order)


class BAWSPlugin(object):

    def __init__(self, iface):

        self.iface = iface
        qgis.utils.iface.actionShowPythonDialog().trigger()

        self.settings = Settings(__version__)
        self.settings.set_environment(self.qmb)
        self.settings.check_production_folders(self.qmb)
        self._date_check = self.settings.selected_date

        self.provider = BAWSProvider()
        self.provider.baws.initializeLayerHandler(self.iface,
                                                  self.settings)
        self.provider.baws.initializeFerryBoxHandler(self.settings)

        self.provider.baws.initializeRasterHandler(self.settings.raster_template_file_path)

        # self.calendar = Calendar(self.settings)
        self.calendar = Calendar(self)

        self.actions = []
        self.menu = '&BAWSPlugin'
        self.toolbar = self.iface.addToolBar('BAWSPlugin')
        self.toolbar.setObjectName('BAWSPlugin')

    def initGui(self):
        """
        # In order to compile resources.py do the following:

        ##########      ONLY WORKS WITH QGIS 2 Shell      ##########
        # in OSGeo4W Shell: [C:/Users/{USER_NAME_HERE}/.qgis2/python/plugins/BAWS>] pyrcc4 -py3 resources.qrc -o resources.py

        :return:
        """
        QgsApplication.processingRegistry().addProvider(self.provider)
        QgsProject.instance().legendLayersAdded.connect(arrange_layer_order)

        self.add_action(':/plugins/BAWS/resources/icons8-download-from-cloud-filled-32.png',
                        text=self.tr('Load production data'),
                        checkable=False,
                        callback=self._load_data,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-merge-files-32.png',
                        text=self.tr('Merge shapefiles'),
                        checkable=False,
                        callback=self._merge_shapes,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-minus-32.png',
                        text=self.tr('Exclude class geometries'),
                        checkable=False,
                        callback=self._exclude_geometries,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-categorize-32.png',
                        text=self.tr('Categorize BAWS-layer'),
                        checkable=False,
                        callback=self._categorize_tool,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-transfer-32.png',
                        text=self.tr('Change class value'),
                        checkable=False,
                        callback=self._change_attribute_value,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-save-as-filled-32.png',
                        text=self.tr('Save BAWS-files'),
                        checkable=False,
                        callback=self._save_files,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-world-map-32.png',
                        text=self.tr('Create BAWS-maps and statistics'),
                        checkable=False,
                        callback=self._create_maps_and_statistics,
                        parent=self.iface.mainWindow(),
                        )

        self.add_action(':/plugins/BAWS/resources/icons8-event-24.png',
                        text=self.tr('Calendar settings'),
                        checkable=False,
                        callback=self._change_calendar_date,
                        parent=self.iface.mainWindow(),
                        )

    def _change_calendar_date(self):
        """
        :return:
        """
        self.calendar.show()

    def dummy_func(self):
        print('dummy_func')

    def unload(self):
        """
        :return:
        """
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def add_action(self,
                   icon_path,
                   text,
                   callback,
                   enabled_flag=True,
                   checkable=False,
                   add_to_menu=True,
                   add_to_toolbar=True,
                   status_tip=None,
                   whats_this=None,
                   menu=None,
                   parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if menu is not None:
            action.setMenu(menu)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def _load_data(self):
        """
        :return:
        """
        if (self.settings.current_working_timestamp < self.settings.timestamp_yesterday
            and self.settings.current_working_timestamp in self.settings.log.dict) \
                or self.settings.data_in_production_folder_with_working_date:
            selected_data_source = self.qmb_reanalysis()
        else:
            selected_data_source = 'raw'

        if selected_data_source == 'old':
            self.settings.reanalyse = True
            rst_path = self.settings.baws_USER_SELECTED_tiff_archive_directory
            shp_path = self.settings.baws_USER_SELECTED_manuell_algtolkning_directory

        elif selected_data_source == 'raw':
            self.settings.reanalyse = False
            rst_path = self.settings.baws_USER_SELECTED_level_1_directory
            shp_path = self.settings.baws_USER_SELECTED_level_2_directory

        else:
            self.settings.reanalyse = False
            return

        self._load_rasterfiles(path=rst_path, backup_path=self.settings.baws_USER_SELECTED_tiff_archive_directory)
        self._load_shapefiles(path=shp_path, categorize=True)
        self._load_baltic_coastline()

        # print('\nBAWS task completed!')

    def _load_shapefiles(self, path='', categorize=False):
        """
        :param path:
        :return:
        """
        # self.provider.baws.ferrybox_handler.read()
        # fb_check = self.provider.baws.ferrybox_handler.process()
        fb_check = False

        print('Loading shapefiles for date %s ' % self.settings.current_working_date)
        if self.settings.reanalyse:
            files = self.settings.generate_filepaths(path,
                                                     pattern='_'.join(('daymap', self.settings.current_working_date)),
                                                     endswith='.shp')
        else:
            files = self.settings.generate_filepaths(path,
                                                     pattern=self.settings.current_working_date,
                                                     endswith='.shp')

        if self.settings.PROD_system and not self.settings.reanalyse:
            # If PROD environment is set, we look for data in TEST-folder as well as in the PROD-data folder.
            files_in_test = self.settings.generate_filepaths(self.settings.baws_TEST_level_2_directory,
                                                             pattern=self.settings.current_working_date,
                                                             endswith='.shp')
            files = chain(files, files_in_test)

        if fb_check and not self.settings.reanalyse:
            ferry_box_file = self.settings.generate_filepaths(self.settings.user_temporary_folder,
                                                              pattern=self.settings.current_working_date, endswith='.shp')
            files = chain(files, ferry_box_file)

        inform_data_manager = []
        files_checked = {}
        for fid in files:
            layer_name = fid.split('\\')[-1]
            if layer_name in files_checked:
                # File already loaded from PROD-data folder.
                print('layer {} already loaded'.format(layer_name))
                continue

            args = (fid, layer_name, "ogr")
            layer = readers.shape_reader('qgis', *args)
            if self.settings.reanalyse:
                layer.setName('Cyano_merged')
            QgsProject.instance().addMapLayer(layer)
            files_checked[layer_name] = fid
            print('Alrighty then! Shapefile loaded: %s\n' % layer.name())
            if categorize:
                self.provider.baws.layer_handler.categorize_layer(layer=layer, attr='class')
            if self.settings.PROD_system and 'prodtest' in fid:
                # Means that we are now using data from TEST-environment. Inform SATSA-Teknik of this..
                inform_data_manager.append(layer_name)

        self.provider.baws.rasterize_shapefiles(list(files_checked.values()),
                                                save_path=self.settings.user_temporary_folder)
        print('rasterize_shapefiles in progress, as thread process!')
        if any(inform_data_manager):
            self.mbx('Satellite Level 2 data have been found in TEST data-folder but are missing in PROD-data folder '
                     '(not good). '
                     '\nPlease inform SATSA-Teknik of this error!'
                     '\n\nMissing files:\n' +
                     '\n'.join(inform_data_manager))

    def _load_rasterfiles(self, path='', backup_path=''):
        """
        :param path:
        :return:
        """
        def import_layer(args):
            layer = readers.raster_reader('qgis', *args)
            QgsProject.instance().addMapLayer(layer)
            print('Alrighty then! Raster loaded: %s\n' % layer.name())

        def loop_files(generator, time_filter, files_checked=None):
            for fid in generator:
                file_name = fid.split('\\')[-1]
                print(file_name)
                if file_name not in files_checked:
                    files_checked[file_name] = True
                    if time_filter(file_name):
                        continue
                    args = (fid, file_name)
                    import_layer(args)

        print('Loading raster files for date %s ' % self.settings.current_working_date)
        files = self.settings.generate_filepaths(path,
                                                 pattern=self.settings.current_working_date,
                                                 endswith='.tif')
        backup_files = self.settings.generate_filepaths(backup_path,
                                                        pattern=self.settings.current_working_date,
                                                        endswith='.tif')
        files_checked = {}
        loop_files(files, self.settings.time_filter, files_checked=files_checked)
        loop_files(backup_files, self.settings.time_filter, files_checked=files_checked)

    def _load_baltic_coastline(self):
        """
        :return:
        """
        start_time = time.time()
        args = (self.settings.baltic_coastline_file_path,
                'Baltic_coastline_sweref99',
                "ogr")
        layer = readers.shape_reader('qgis', *args)
        QgsProject.instance().addMapLayer(layer)
        self.provider.baws.layer_handler.categorize_line_layer(layer=layer,
                                                               attr='FID_1',
                                                               layer_name='Baltic_coastline_sweref99')
        print("Baltic_costline_sweref99 loaded in --%.3f sec" % (time.time() - start_time))

    def _categorize_tool(self):
        """
        :return:
        """
        layer_name = None
        for name in self.provider.baws.layer_handler.active_layers_name:
            if '_costline_' in name:
                continue
            else:
                layer_name = name
                break

        if layer_name:
            layer = self.provider.baws.layer_handler.get_layer_by_name(layer_name)
            self.provider.baws.layer_handler.categorize_layer(layer=layer, attr='class')
            print('\nBAWS task completed!')
        else:
            print('No active layer given ?')

    def _change_attribute_value(self):
        """
        :return:
        """
        selected_class_value = self.qmb_change_attribute_value()
        if selected_class_value:
            layer_name = None
            for name in self.provider.baws.layer_handler.active_layers_name:
                if name == 'Cyano_merged' or name.startswith('cyano_daymap_'):
                    layer_name = name
                    break

            if layer_name:
                layer = self.provider.baws.layer_handler.get_layer_by_name(layer_name)
                self.provider.baws.layer_handler.change_class_values(layer=layer,
                                                                     attr='class',
                                                                     class_value=selected_class_value)
                print('\nBAWS task completed!')
            else:
                print('No active layer given ?')

    def _merge_shapes(self):
        """
        :return:
        """
        if any(self.provider.baws.layer_handler.active_layers):
            self.provider.baws.merge_selected_shapefiles(self.settings)
            print('\nBAWS task completed!')
        else:
            print('No active layer given ?')

    def _save_files(self):
        """
        :return:
        """
        # if not self.settings.reanalyse:
        if True:
            question = ['Save your adjusted Cyano_merged layer with accompanying tif files.\n',
                        'Is this selection of tif files correct?']
            string_list = question + self.provider.baws.layer_handler.active_tif_layer_names
            user_answer = self.qmb(*('BAWS (%s) Question' % __version__, '\n'.join(string_list)))
            if user_answer:
                self.provider.baws.save_files(self.settings, self.mbx)
                print('\nBAWS task completed!')
                self._continue_with_plotting_maps()
            else:
                print('\nPlease select files and click save again.\n')

        # else:
        #     # reanalyse
        #     question = 'Save your adjusted Cyano_merged layer?'
        #     user_answer = self.qmb(*('BAWS (%s) Question' % __version__, question))
        #     if user_answer:
        #         # self.provider.baws.save_files(self.settings, None, layer_name=self.rh.current_filename,
        #         #                               daily_outpath=self.settings.reanalysis_reanalyzed_data_directory,
        #         #                               save_union_bloom=False,
        #         #                               copy_tif_files=False,
        #         #                               create_text_files=False,
        #         #                               create_stw_files=False,
        #         #                               create_weekly_map=False)
        #         # Delete layer
        #         # self.provider.baws.layer_handler.delete_layers(name=self.rh.current_filename)
        #         self.provider.baws.layer_handler.delete_layers(all=True)
        #         self.rh.update_file()
        #         self._reanalyse_tool()
        #     else:
        #         print('\nNo file saved.')

    def _continue_with_plotting_maps(self):
        """
        :return:
        """
        question = 'Would you like to plot daily and weekly maps based on your saved files?'
        user_answer = self.qmb(*('BAWS (%s) Question' % __version__, question))
        if user_answer:
            self._create_maps_and_statistics(daymap_path=self.settings.cyano_daymap_path,
                                             weekmap_path=self.settings.cyano_weekmap_path)

    def process_daily_map(self, handler, path):
        """"""
        handler.read(path)
        handler.calculate_area()
        handler.change_csr()
        self.provider.baws.daily_map(handler, file_path=path)

    def process_weekly_map(self, handler, path):
        """"""
        handler.read(path)
        handler.calculate_area()
        handler.change_csr()
        self.provider.baws.weekly_map(handler, file_path=path)

    def _create_maps_and_statistics(self, daymap_path=None, weekmap_path=None):
        """
        :return:
        """
        if not (daymap_path and weekmap_path):
            file_path = self.qfd(*('BAWS ({}) Open File'.format(__version__), self.settings.baws_USER_SELECTED_current_production_directory))
            # daymap_path = file_path[0].replace('/', '\\')
            daymap_path = file_path[0]
            weekmap_path = self.find_path(daymap_path,
                                          replace_tag='cyano_daymap',
                                          replace_with='cyano_weekmap')

        print('Drawing daily map from {}'.format(daymap_path))
        print('Drawing weekly map from {}'.format(weekmap_path))

        dm_shape_handler = handlers.DailyShapeHandler()
        wm_shape_handler = handlers.WeeklyShapeHandler()

        start_time = time.time()
        if daymap_path and weekmap_path:
            # Daily data / stats
            stat_handler = handlers.StatHandler(self.settings, objects=[dm_shape_handler, wm_shape_handler])
            thread_process(stat_handler.save_statistics)

        # Matplotlib is not thread safe
        # thread_process(self.process_daily_map, dm_shape_handler, daymap_path)
        if daymap_path:
            self.process_daily_map(dm_shape_handler, daymap_path)
        # dm_shape_handler.read(daymap_path)

        # Weekly data / stats
        # Matplotlib is not thread safe
        # thread_process(self.process_weekly_map, wm_shape_handler, weekmap_path)
        if weekmap_path:
            self.process_weekly_map(wm_shape_handler, weekmap_path)

        if self.settings.PROD_system:
            thread_process(self.settings.test_handler.copy_prod_files_to_test_system)

        print("_create_maps_and_statistics completed in --%.1f sec" % (time.time() - start_time))
        print('\nBAWS task completed!')

    def _summarize_statistics(self):
        """
        :return:
        """
        raise NotImplementedError

    def find_path(self, path, replace_tag='', replace_with=''):
        """
        :param path:
        :param replace_tag:
        :param replace_with:
        :return:
        """
        path = path.replace(replace_tag, replace_with)
        if os.path.isfile(path):
            pass
        else:
            print('Warning! Could not find match for weekmap shapefile!')
            path = None
        return path

    def _exclude_geometries(self):
        """
        :return:
        """
        class_list = self.qmb_exclude_geometries()
        if any(class_list):
            layer = self.provider.baws.layer_handler.get_layer_by_name('Cyano_merged')
            if layer:
                self.provider.baws.layer_handler.delete_class_geometries(layer, class_list=class_list)
                print('\nBAWS task completed!')
            else:
                print('No layer named Cyano_merged')

    @property
    def date_check(self):
        return self._date_check

    @date_check.setter
    def date_check(self, new_value):
        """
        Callback
        When the user changes the working date, the user will get the
        option of deleting previously loaded data
        :param new_value:
        :return:
        """
        old_date = self._date_check
        self._date_check = new_value
        if old_date != new_value and any(self.provider.baws.layer_handler.all_layers):
            question = 'You have change date. Would you like delete all layers before loading new ones?'
            user_answer = self.qmb(*('BAWS (%s) Question' % __version__, question))
            if user_answer:
                self.provider.baws.layer_handler.delete_layers(all=True)
                self.settings.reset_folder(self.settings.user_temporary_folder)

    @staticmethod
    def qfd(*args):
        """
        QFileDialog.getOpenFileName(qfd, title, path)
        :param args: title, path
        :return:
        """
        return QFileDialog.getOpenFileName(QFileDialog(), *args)

    @staticmethod
    def qmb_exclude_geometries():
        """
        :return:
        """
        msgBox = QMessageBox()
        msgBox.setText('Choose which type of polygons you would like to delete? All polygons based on your selection will be deleted!')
        msgBox.setWindowTitle("BAWS (%s) Question" % __version__)
        red_button = msgBox.addButton('Only red', QMessageBox.YesRole)
        yellow_button = msgBox.addButton('Only yellow', QMessageBox.NoRole)
        both_button = msgBox.addButton('Both red and yellow', QMessageBox.ActionRole)
        cancel_button = msgBox.addButton('Cancel', QMessageBox.RejectRole)
        msgBox.exec_()

        if msgBox.clickedButton() == red_button:
            return [3]
        elif msgBox.clickedButton() == yellow_button:
            return [2]
        elif msgBox.clickedButton() == both_button:
            return [2, 3]
        elif msgBox.clickedButton() == cancel_button:
            return []
        else:
            return []

    @staticmethod
    def qmb_change_attribute_value():
        """
        :return:
        """
        msgBox = QMessageBox()
        msgBox.setText('Swap geometry class values with..')
        msgBox.setWindowTitle("BAWS (%s) Question" % __version__)
        red_button = msgBox.addButton('Red (3)', QMessageBox.YesRole)
        yellow_button = msgBox.addButton('Yellow (2)', QMessageBox.NoRole)
        cancel_button = msgBox.addButton('Cancel', QMessageBox.RejectRole)
        msgBox.exec_()

        if msgBox.clickedButton() == red_button:
            return 3
        elif msgBox.clickedButton() == yellow_button:
            return 2
        elif msgBox.clickedButton() == cancel_button:
            return None
        else:
            return None

    @staticmethod
    def qmb_reanalysis():
        """
        :return:
        """
        msgBox = QMessageBox()
        msgBox.setText('You have selected an old date. \nWould you like to load raw data or old data from a previous production work?')
        msgBox.setWindowTitle("BAWS (%s) Question" % __version__)
        raw_button = msgBox.addButton('Raw data', QMessageBox.YesRole)
        old_button = msgBox.addButton('Old production data', QMessageBox.NoRole)
        cancel_button = msgBox.addButton('Cancel', QMessageBox.RejectRole)
        msgBox.exec_()

        if msgBox.clickedButton() == raw_button:
            return 'raw'
        elif msgBox.clickedButton() == old_button:
            return 'old'
        elif msgBox.clickedButton() == cancel_button:
            return None
        else:
            return None

    @staticmethod
    def qmb(*args):
        """
        QMessageBox.question()
        :param args: title, path
        :return:
        """
        qm = QMessageBox
        args = args + (qm.Yes | qm.No, )
        user_answer = qm.question(QMessageBox(), *args)

        return user_answer == qm.Yes

    @staticmethod
    def mbx(text, picture_path=None):
        """
        :param text:
        :return:
        """
        msgBox = QMessageBox()
        msgBox.setWindowTitle("BAWS (%s) Message" % __version__)
        if picture_path:
            msgBox.setIconPixmap(QPixmap(picture_path))
        msgBox.setText(text)
        msgBox.exec_()

    @staticmethod
    def tr(message):
        """
        :param message:
        :return:
        """
        return QCoreApplication.translate('', message)


class Calendar(QWidget):
    """
    A QCalendarWidget
    """
    def __init__(self, main_plugin):
        # create GUI
        QMainWindow.__init__(self)
        self.plugin = main_plugin

        self.selected_date = None
        self.setWindowTitle('Calendar widget')
        # Set the window dimensions
        self.resize(400, 300)

        # vertical layout for widgets
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        # Create a calendar widget and add it to our layout
        self.cal = QCalendarWidget()
        self.cal.setFirstDayOfWeek(Qt.Monday)

        self.vbox.addWidget(self.cal)
        qd = self.get_qdate()
        self.cal.setSelectedDate(QDate(*qd))

        # Create a label which we will use to show the date a week from now
        self.lbl = QLabel()
        self.vbox.addWidget(self.lbl)

        self.ok_box = QPushButton('Ok!')
        self.vbox.addWidget(self.ok_box)

        # Connect the clicked signal to the centre handler
        self.cal.selectionChanged.connect(self.date_changed)

        # Connect the clicked signal to the centre handler
        # self.ok_box.clicked.connect(self.ok_selected)
        self.ok_box.clicked.connect(self.ok_selected)

    def date_changed(self):
        """
        Handler called when the date selection has changed
        """
        # Fetch the currently selected date, this is a QDate object
        date = self.cal.selectedDate()
        # This gives us the date contained in the QDate as a native
        pydate = date.toPyDate()
        print('Temporary selection:', pydate, type(pydate))
        self.selected_date = pd.Timestamp(pydate)

    def ok_selected(self):
        """
        """
        self.plugin.settings.change_working_date(self.selected_date)
        self.close()
        self.plugin.date_check = self.selected_date

    def get_qdate(self):
        """
        """
        return (self.plugin.settings.current_working_timestamp.year,
                self.plugin.settings.current_working_timestamp.month,
                self.plugin.settings.current_working_timestamp.day, )
