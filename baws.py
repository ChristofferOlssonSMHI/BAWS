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
from . import utils

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

"""
In order to compile resources.py do the following:
In OSGeo4W Shell: [C:/Users/{USER_NAME_HERE}/.qgis2/python/plugins/BAWS>] 
pyrcc4 -py3 resources.qrc -o resources.py

OBS: Might only work with QGIS 2 Shell 
# IMPORTANT TO LOAD resources in order to reach pictures etc..
"""
from . import resources  # DO NOT REMOVE IMPORT


cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from . import readers
from . import handlers


def arrange_layer_order(layers):
    """Set order of imported layers in QGIS.

    Args:
        layers: list of layer objects.
    """
    root = QgsProject.instance().layerTreeRoot()
    order = root.customLayerOrder()
    for layer in layers:
        if '_coastline_' not in layer.name():
            print('new layer:', layer.name())
            order.insert(1, order.pop())  # New layer to second position
    root.setCustomLayerOrder(order)


class BAWSPlugin:
    """The main class for this BAWS plugin."""

    def __init__(self, iface):
        """Initialize.

        Args:
            iface (QgisInterface): The QGIS interface instance.
        """
        self.iface = iface
        qgis.utils.iface.actionShowPythonDialog().trigger()

        self.settings = Settings()
        self.settings.set_environment(self.qmb)
        self.settings.check_production_folders(self.qmb)
        self._date_check = self.settings.selected_date

        self.provider = BAWSProvider()
        self.provider.baws.initialize_layer_handler(self.iface,
                                                    self.settings)
        # self.provider.baws.initialize_ferrybox_handler(self.settings)

        self.provider.baws.initialize_raster_handler(
            self.settings.raster_template_file_path)

        self.provider.baws.initialize_plot_handler(
            path_basemap=self.settings.basemap_obj_path,
            path_figure=self.settings.basemap_figure_path
        )

        self.calendar = Calendar(self)

        self.actions = []
        self.menu = '&BAWSPlugin'
        self.toolbar = self.iface.addToolBar('BAWSPlugin')
        self.toolbar.setObjectName('BAWSPlugin')

    def initGui(self):
        """Initialize QGIS plugin.

        Including the creation of buttons within the QGIS interface.
        Note that resources needs to be compiled.
        """
        QgsApplication.processingRegistry().addProvider(self.provider)
        QgsProject.instance().legendLayersAdded.connect(arrange_layer_order)

        self.add_action(
            ':/plugins/BAWS/resources/icons8-download-from-cloud-filled-32.png',
            text=self.tr('Load production data'),
            callback=self._load_data,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-merge-files-32.png',
            text=self.tr('Merge shapefiles'),
            callback=self._merge_shapes,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-minus-32.png',
            text=self.tr('Exclude class geometries'),
            callback=self._exclude_geometries,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-categorize-32.png',
            text=self.tr('Categorize BAWS-layer'),
            callback=self._categorize_tool,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-transfer-32.png',
            text=self.tr('Change class value'),
            callback=self._change_attribute_value,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-save-as-filled-32.png',
            text=self.tr('Save BAWS-files'),
            callback=self._save_files,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-world-map-32.png',
            text=self.tr('Create BAWS-maps and statistics'),
            callback=self._create_maps_and_statistics,
        )

        self.add_action(
            ':/plugins/BAWS/resources/icons8-event-24.png',
            text=self.tr('Calendar settings'),
            callback=self._change_calendar_date,
        )

    def _change_calendar_date(self):
        """Show the calendar."""
        self.calendar.show()

    def unload(self):
        """Unload the plugin."""
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def add_action(self, icon_path, text=None, callback=None):
        """Add action button to QGIS interface.

        Args:
            icon_path: path to icon.
            text: Hover text for button.
            callback: Connected method to run ones the button is triggerd.
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(True)
        action.setCheckable(False)
        self.toolbar.addAction(action)
        self.iface.addPluginToVectorMenu(self.menu, action)
        self.actions.append(action)

    def _load_data(self):
        """Load data.

        Loading data based on the users selection on:
            - Date
            - TEST / PROD
            - New data / Old production data

        Rasters to load:
            - Level 1: (true color/"ocean color")
            - Level 2: BAWS algorithm layer (class 0-4)
        """
        if (self.settings.current_working_timestamp
            < self.settings.timestamp_yesterday
            and self.settings.current_working_timestamp in
            self.settings.log.dict) \
                or self.settings.data_in_production_folder_with_working_date:
            selected_data_source = self.qmb_reanalysis()
        else:
            selected_data_source = 'raw'

        if selected_data_source == 'old':
            self.settings.reanalyse = True
            rst_path = self.settings.baws_USER_SELECTED_tiff_archive_directory

            if self.settings.data_in_production_folder_with_working_date:
                level_2_path = self.settings.baws_USER_SELECTED_current_production_directory
            else:
                level_2_path = self.settings.baws_USER_SELECTED_manuell_algtolkning_directory

        elif selected_data_source == 'raw':
            self.settings.reanalyse = False
            rst_path = self.settings.baws_USER_SELECTED_level_1_directory
            level_2_path = self.settings.baws_USER_SELECTED_level_2_directory

        else:
            self.settings.reanalyse = False
            return

        self._load_rasterfiles(
            path=rst_path,
            backup_path=self.settings.baws_USER_SELECTED_tiff_archive_directory
        )
        if self.settings.reanalyse:
            self._load_shapefiles(path=level_2_path, categorize=True)
        else:
            self._load_raster_scenes(path=level_2_path, categorize=True)

        self._load_baltic_coastline()
        print('\nBAWS task completed!')

    def _load_shapefiles(self, path='', categorize=False):
        """Load old production data.

        Args:
            path: Selected directory
            categorize: If true the layer will be categorized using
                        the classes 1-4
        """
        # self.provider.baws.ferrybox_handler.read()
        # fb_check = self.provider.baws.ferrybox_handler.process()
        fb_check = False

        print(f'Loading shapefiles for date '
              f'{self.settings.current_working_date}')
        if self.settings.reanalyse:
            files = utils.generate_filepaths(
                path,
                pattern=f'daymap_{self.settings.current_working_date}',
                endswith='.shp'
            )
        else:
            files = utils.generate_filepaths(
                path,
                pattern=self.settings.current_working_date,
                endswith='.shp'
            )

        if self.settings.PROD_system and not self.settings.reanalyse:
            # If PROD environment is set, we look for data in
            # TEST-folder as well as in the PROD-data folder.
            files_in_test = utils.generate_filepaths(
                self.settings.baws_TEST_level_2_directory,
                pattern=self.settings.current_working_date,
                endswith='.shp'
            )
            files = chain(files, files_in_test)

        if fb_check and not self.settings.reanalyse:
            ferry_box_file = utils.generate_filepaths(
                self.settings.user_temporary_folder,
                pattern=self.settings.current_working_date,
                endswith='.shp'
            )
            files = chain(files, ferry_box_file)

        inform_data_manager = []
        files_checked = {}
        for fid in files:
            layer_name = fid.split('\\')[-1]
            if layer_name in files_checked:
                # File already loaded from PROD-data folder.
                print(f'layer {layer_name} already loaded')
                continue

            layer = readers.shape_reader('qgis', fid, layer_name, "ogr")
            if self.settings.reanalyse:
                layer.setName('Cyano_merged')
            QgsProject.instance().addMapLayer(layer)
            files_checked[layer_name] = fid
            print(f'Shapefile loaded: {layer.name()}\n')
            if categorize:
                self.provider.baws.layer_handler.categorize_layer(
                    layer=layer, attr='class'
                )
            if self.settings.PROD_system and 'prodtest' in fid:
                # Means that we are now using data from TEST-environment.
                # Inform SATSA-Teknik of this..
                inform_data_manager.append(layer_name)

        self.provider.baws.rasterize_shapefiles(
            list(files_checked.values()),
            save_path=self.settings.user_temporary_folder
        )
        print('rasterize_shapefiles in progress, as thread process!')
        if any(inform_data_manager):
            self.mbx('Satellite Level 2 data have been found in TEST '
                     'data-folder but are missing in PROD-data folder '
                     '(not good). '
                     '\nPlease inform SATSA-Teknik of this error!'
                     '\n\nMissing files:\n' +
                     '\n'.join(inform_data_manager))

    def _load_raster_scenes(self, path=None, categorize=True):
        """Load level 2 BAWS algorithm data (class 0-4).

        Args:
            path: Selected directory
            categorize: If true the layer will be categorized using
                        the classes 1-4
        """
        files = utils.generate_filepaths(
            path,
            pattern=self.settings.current_working_date,
            endswith='.tiff'
        )

        if self.settings.PROD_system:
            # If PROD environment is set, we look for data in
            # TEST-folder as well.
            files_in_test = utils.generate_filepaths(
                self.settings.baws_TEST_level_2_directory,
                pattern=self.settings.current_working_date,
                endswith='.tiff'
            )
            files = chain(files, files_in_test)

        root = QgsProject.instance().layerTreeRoot()
        loaded_files = set(())
        for fid in files:
            name = os.path.basename(fid)
            if name not in loaded_files:
                layer = readers.raster_reader('qgis', fid, name)
                QgsProject.instance().addMapLayer(layer)
                if categorize:
                    self.provider.baws.layer_handler.categoraize_raster_layer(
                        layer=layer
                    )
                node = root.findLayer(layer.id())
                node.setExpanded(True)
                loaded_files.add(name)

    def _load_rasterfiles(self, path='', backup_path=''):
        """Load level 1 data (true color/"ocean color" images).

        Args:
            path: Selected directory
            backup_path: Backup directory (used in PROD mode)
        """
        root = QgsProject.instance().layerTreeRoot()

        def loop_files(generator, time_filter, files_checked=None):
            for fid in generator:
                file_name = fid.split('\\')[-1]
                print(file_name)
                if file_name not in files_checked:
                    files_checked[file_name] = True
                    if time_filter(file_name):
                        continue
                    layer = readers.raster_reader('qgis', fid, file_name)
                    QgsProject.instance().addMapLayer(layer)
                    node = root.findLayer(layer.id())
                    node.setExpanded(False)
                    print(f'Raster loaded: {layer.name()}\n')

        print(f'Loading raster files for date '
              f'{self.settings.current_working_date}')
        files = utils.generate_filepaths(
            path,
            pattern=self.settings.current_working_date,
            endswith='.tif'
        )
        backup_files = utils.generate_filepaths(
            backup_path,
            pattern=self.settings.current_working_date,
            endswith='.tif'
        )
        files_checked = {}
        loop_files(files, self.settings.time_filter,
                   files_checked=files_checked)
        loop_files(backup_files, self.settings.time_filter,
                   files_checked=files_checked)

    def _load_baltic_coastline(self):
        """Load coastline layer."""
        start_time = time.time()
        layer = readers.shape_reader(
            'qgis', self.settings.baltic_coastline_file_path,
            'Baltic_coastline_sweref99', "ogr"
        )
        QgsProject.instance().addMapLayer(layer)
        self.provider.baws.layer_handler.categorize_line_layer(
            layer=layer,
            attr='FID_1',
            layer_name='Baltic_coastline_sweref99'
        )
        root = QgsProject.instance().layerTreeRoot()
        node = root.findLayer(layer.id())
        node.setExpanded(False)
        print("Baltic_costline_sweref99 loaded in --%.3f "
              "sec" % (time.time() - start_time))

    def _categorize_tool(self):
        """Categorize an active shape layer (classes: 1-4)."""
        layer_name = None
        for name in self.provider.baws.layer_handler.active_layers_name:
            if '_costline_' in name:
                continue
            else:
                layer_name = name
                break

        if layer_name:
            layer = self.provider.baws.layer_handler.get_layer_by_name(
                layer_name)
            self.provider.baws.layer_handler.categorize_layer(
                layer=layer, attr='class')
            print('\nBAWS task completed!')
        else:
            print('No active layer given ?')

    def _change_attribute_value(self):
        """Change class value of a selected geometry in QGIS."""
        selected_class_value = self.qmb_change_attribute_value()
        if selected_class_value:
            layer_name = None
            for name in self.provider.baws.layer_handler.active_layers_name:
                if name == 'Cyano_merged' or name.startswith('cyano_daymap_'):
                    layer_name = name
                    break

            if layer_name:
                layer = self.provider.baws.layer_handler.get_layer_by_name(
                    layer_name)
                self.provider.baws.layer_handler.change_class_values(
                    layer=layer,
                    attr='class',
                    class_value=selected_class_value
                )
                print('\nBAWS task completed!')
            else:
                print('No active layer given ?')

    def _merge_shapes(self):
        """Merge layers.

        As of 2022 we use raster layers instead of shape layers.
        """
        if any(self.provider.baws.layer_handler.active_cyano_tiff_layers):
            self.provider.baws.merge_selected_rasterfiles(self.settings)
            print('\nBAWS task completed!')
        else:
            print('No active layer given ?')

    def _save_files(self):
        """Save the work."""
        if True:
            string_list = [
                'Save your adjusted Cyano_merged layer with accompanying '
                'tif files.\n',
                'Is this selection of tif files correct?'
            ]
            string_list.extend(
                self.provider.baws.layer_handler.active_tif_layer_names)
            user_answer = self.qmb(
                f'BAWS ({__version__}) Question', '\n'.join(string_list))
            if user_answer:
                user_answer_text_generate = self.qmb(
                    f'BAWS ({__version__}) Question',
                    'Would you like to automatically generate day- and weekmap '
                    'texts? If No, txt-files will look like they´ve '
                    'always done.'
                )
                self.provider.baws.save_files(
                    self.settings, self.mbx,
                    auto_generate_text=user_answer_text_generate
                )
                print('\nBAWS task completed!')
                self._continue_with_plotting_maps()
            else:
                print('\nPlease select files and click save again.\n')

    def _continue_with_plotting_maps(self):
        """Continue with plotting png (question)."""
        question = 'Would you like to plot daily and weekly maps based on ' \
                   'your saved files? '
        user_answer = self.qmb(f'BAWS ({__version__}) Question', question)
        if user_answer:
            self._create_maps_and_statistics(
                daymap_path=self.settings.cyano_daymap_path,
                weekmap_path=self.settings.cyano_weekmap_path
            )

    def process_daily_map(self, handler, path):
        """Process daily data.

        Args:
            handler: Data handler.
            path: File path
        """
        handler.read(path)
        # handler.calculate_area()
        handler.change_csr()
        self.provider.baws.daily_map(handler, file_path=path)

    def process_weekly_map(self, handler, path):
        """Process weekly data.

        Args:
            handler: Data handler.
            path: File path
        """
        handler.read(path)
        # handler.calculate_area()
        handler.change_csr()
        self.provider.baws.weekly_map(handler, file_path=path)

    def _create_maps_and_statistics(self, daymap_path=None, weekmap_path=None):
        """Plot the saved shapefiles to png files.

        Args:
            daymap_path: Path to daymap shapefile
            weekmap_path: Path to weekmap shapefile
        """
        if not (daymap_path and weekmap_path):
            file_path = self.qfd(
                f'BAWS ({__version__}) Open File',
                self.settings.baws_USER_SELECTED_current_production_directory)
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
        # if daymap_path and weekmap_path:
        #     # Daily data / stats
        #     stat_handler = handlers.StatHandler(
        #         self.settings,
        #         objects=[dm_shape_handler, wm_shape_handler]
        #     )
        #     utils.thread_process(stat_handler.save_statistics)

        if daymap_path:
            self.process_daily_map(dm_shape_handler, daymap_path)
        # dm_shape_handler.read(daymap_path)

        # Weekly data / stats
        if weekmap_path:
            self.process_weekly_map(wm_shape_handler, weekmap_path)

        self.provider.baws.initialize_plot_handler(
            reset=True,
            path_basemap=self.settings.basemap_obj_path,
            path_figure=self.settings.basemap_figure_path
        )

        if self.settings.PROD_system:
            utils.thread_process(
                self.settings.test_handler.copy_prod_files_to_test_system)

        print("maps and statistics completed in --%.1f sec"
              "" % (time.time() - start_time))
        print('\nBAWS task completed!')

    @staticmethod
    def find_path(path, replace_tag='', replace_with=''):
        """Check path.

        Args:
            path: path to file.
            replace_tag (str): string to replace
            replace_with (str): string to add
        """
        path = path.replace(replace_tag, replace_with)
        if os.path.isfile(path):
            pass
        else:
            print('Warning! Could not find match for weekmap shapefile!')
            path = None
        return path

    def _exclude_geometries(self):
        """Filter out invalid geometries."""
        class_list = self.qmb_exclude_geometries()
        if any(class_list):
            layer = self.provider.baws.layer_handler.get_layer_by_name(
                'Cyano_merged')
            if layer:
                self.provider.baws.layer_handler.delete_class_geometries(
                    layer,
                    class_list=class_list
                )
                print('\nBAWS task completed!')
            else:
                print('No layer named Cyano_merged')

    @property
    def date_check(self):
        return self._date_check

    @date_check.setter
    def date_check(self, new_value):
        """Set value to the property date_check.

        When the user changes the working date, the user will get the
        option of deleting previously loaded data.

        Args:
            new_value: New date
        """
        old_date = self._date_check
        self._date_check = new_value
        if old_date != new_value and any(
                self.provider.baws.layer_handler.all_layers):
            question = 'You have change date. Would you like to delete all ' \
                       'layers before loading new ones? '
            user_answer = self.qmb(f'BAWS ({__version__}) Question', question)
            if user_answer:
                self.provider.baws.layer_handler.delete_layers(all=True)
                self.settings.reset_folder(self.settings.user_temporary_folder)

    @staticmethod
    def qfd(*args):
        """Return dialog window."""
        return QFileDialog.getOpenFileName(QFileDialog(), *args)

    @staticmethod
    def qmb_exclude_geometries():
        """Return dialog window."""
        msgbox = QMessageBox()
        msgbox.setText('Choose which type of polygons you would like to '
                       'delete? All polygons based on your selection will be '
                       'deleted!')
        msgbox.setWindowTitle(f"BAWS ({__version__}) Question")
        red_button = msgbox.addButton('Only red', QMessageBox.YesRole)
        yellow_button = msgbox.addButton('Only yellow', QMessageBox.NoRole)
        both_button = msgbox.addButton('Both red and yellow',
                                       QMessageBox.ActionRole)
        cancel_button = msgbox.addButton('Cancel', QMessageBox.RejectRole)
        msgbox.exec_()

        if msgbox.clickedButton() == red_button:
            return [3]
        elif msgbox.clickedButton() == yellow_button:
            return [2]
        elif msgbox.clickedButton() == both_button:
            return [2, 3]
        elif msgbox.clickedButton() == cancel_button:
            return []
        else:
            return []

    @staticmethod
    def qmb_change_attribute_value():
        """Return dialog window."""
        msgbox = QMessageBox()
        msgbox.setText('Swap geometry class values with..')
        msgbox.setWindowTitle(f"BAWS ({__version__}) Question")
        red_button = msgbox.addButton('Red (3)', QMessageBox.YesRole)
        yellow_button = msgbox.addButton('Yellow (2)', QMessageBox.NoRole)
        cancel_button = msgbox.addButton('Cancel', QMessageBox.RejectRole)
        msgbox.exec_()

        if msgbox.clickedButton() == red_button:
            return 3
        elif msgbox.clickedButton() == yellow_button:
            return 2
        elif msgbox.clickedButton() == cancel_button:
            return None
        else:
            return None

    @staticmethod
    def qmb_reanalysis():
        """Return dialog window."""
        msgbox = QMessageBox()
        msgbox.setText('You have selected an old date. \nWould you like to '
                       'load raw data or old data from a previous production '
                       'work?')
        msgbox.setWindowTitle(f"BAWS ({__version__}) Question")
        raw_button = msgbox.addButton('Raw data', QMessageBox.YesRole)
        old_button = msgbox.addButton('Old production data', QMessageBox.NoRole)
        cancel_button = msgbox.addButton('Cancel', QMessageBox.RejectRole)
        msgbox.exec_()

        if msgbox.clickedButton() == raw_button:
            return 'raw'
        elif msgbox.clickedButton() == old_button:
            return 'old'
        elif msgbox.clickedButton() == cancel_button:
            return None
        else:
            return None

    @staticmethod
    def qmb(*args):
        """Return dialog window."""
        qm = QMessageBox
        args = args + (qm.Yes | qm.No, )
        user_answer = qm.question(QMessageBox(), *args)
        return user_answer == qm.Yes

    @staticmethod
    def mbx(text, picture_path=None):
        """Return dialog window.

        Args:
            text: Text.
            picture_path: Path to file.
        """
        msgbox = QMessageBox()
        msgbox.setWindowTitle(f"BAWS ({__version__}) Message")
        if picture_path:
            msgbox.setIconPixmap(QPixmap(picture_path))
        msgbox.setText(text)
        msgbox.exec_()

    @staticmethod
    def tr(message):
        """Return hover text.

        Args:
            message: Text.
        """
        return QCoreApplication.translate('', message)


class Calendar(QWidget):
    """A QCalendarWidget."""

    def __init__(self, main_plugin):
        """Initialize.

        Args:
            main_plugin: The BAWSPlugin object.
        """
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
        self.cal.setSelectedDate(
            QDate(self.plugin.settings.current_working_timestamp.year,
                  self.plugin.settings.current_working_timestamp.month,
                  self.plugin.settings.current_working_timestamp.day)
        )

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
        """Change the selected date.

        Handler called when the date selection has changed.
        """
        # Fetch the currently selected date, this is a QDate object
        date = self.cal.selectedDate()
        # This gives us the date contained in the QDate as a native
        pydate = date.toPyDate()
        print('Temporary selection:', pydate, type(pydate))
        self.selected_date = pd.Timestamp(pydate)

    def ok_selected(self):
        """Change the working date."""
        self.plugin.settings.change_working_date(self.selected_date)
        self.close()
        self.plugin.date_check = self.selected_date
