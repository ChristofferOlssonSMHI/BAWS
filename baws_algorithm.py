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

__author__ = 'SMHI'
__date__ = '2019-04-17'
__copyright__ = '(C) 2019 by SMHI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import time
from shutil import copyfile
from .utils import thread_process

from qgis.PyQt.QtCore import QSettings, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingOutputNumber,
                       QgsVectorFileWriter,
                       QgsProcessingParameterFeatureSource,
                       QgsPointXY,
                       QgsProject,
                       QgsField,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry)

from processing.tools import dataobjects, vector

from . import readers
from . import handlers
from . import subprocesses


class BAWSAlgorithm(QgsProcessingAlgorithm):
    """Based on example algorithm class.. methods could probably be moved to BAWSProvider
    """
    def initializeLayerHandler(self, iface, settings):
        if not hasattr(self, 'layer_handler'):
            self.layer_handler = handlers.LayerHandler(iface, settings)

    def initializeFerryBoxHandler(self, settings):
        if not hasattr(self, 'ferrybox_handler'):
            self.ferrybox_handler = handlers.FerryBoxHandler(settings)

    def initializeRasterHandler(self, rst_template_path):
        if not hasattr(self, 'raster_handler'):
            self.raster_handler = handlers.RasterHandler(rst_template_path)

    def rasterize_shapefiles(self, args, save_path=None):
        for fid in args:
            thread_process(subprocesses.rasterize_file,
                           self.raster_handler.raster_meta,
                           save_path,
                           fid)
        thread_process(subprocesses.check_while_saving,
                       save_path,
                       '.tiff',
                       len(args))

    def merge_selected_shapefiles(self, settings, categorize=True):
        """
        :return:
        """
        print('Starting merging work. Usually takes ~5-30 seconds, depending on size and number of geometries..')
        start_time = time.time()
        merge_file_path = os.path.join(settings.user_temporary_folder, 'Cyano_merged.shp')
        self.raster_handler.merge_scene_shapes(layer_names=self.layer_handler.active_layers_name,
                                               output_filename=merge_file_path,
                                               mask_path=settings.raster_valid_area_file_path)

        args = (merge_file_path, 'Cyano_merged', "ogr")
        layer = readers.shape_reader('qgis', *args)
        not_valid_feature_ids = self.layer_handler.get_not_valid_feature_ids(layer=layer)
        self.layer_handler.delete_features(layer, feature_ids=not_valid_feature_ids)
        QgsProject.instance().addMapLayer(layer)
        if categorize:
            self.layer_handler.categorize_layer(layer_name='Cyano_merged', attr='class')

        self.layer_handler.deactivate_layers(self.layer_handler.active_layers, exclude_layers=['Cyano_merged'])
        print("merge_scene_shapes completed in --%.2f sec\n" % (time.time() - start_time))

    def intersect_geometries(self):
        raise NotImplementedError

    def _copy_tif_files(self, settings):
        if not any(self.layer_handler.active_tif_layer_names):
            return
        files_to_copy = settings.generate_filepaths(settings.baws_USER_SELECTED_level_1_directory,
                                                    pattern_list=self.layer_handler.active_tif_layer_names)
        for fid in files_to_copy:
            file_name = fid.split('\\')[-1]
            print('Copying %s to tif_archive' % file_name)
            dst_path = os.path.join(settings.baws_USER_SELECTED_tiff_archive_directory, file_name)
            thread_process(copyfile, fid, dst_path)

        print('\nTif files are being copied in background threads')

    def save_files(self, settings, gui_mxb, layer_name='Cyano_merged', daily_outpath=None,
                   copy_tif_files=True, create_text_files=True, create_stw_files=True, create_weekly_map=True):
        """
        :return:
        """
        # Daily tif files
        if copy_tif_files:
            self._copy_tif_files(settings)

        # Daily Textfiles
        if create_text_files:
            text_handler = handlers.TextFileHandler(settings)
            thread_process(text_handler.copy_empty_files)

        # Daily map
        print('Daily shape process...')
        daily_map_path = self.layer_handler.get_output_path_for_shape('cyano_daymap_', daily_outpath)
        self.layer_handler.save_shapefile(layer_name=layer_name,
                                          path=daily_map_path,
                                          output_prefix='cyano_daymap_')

        # Rasterize the daily map. Super duper much more efficient than merging shapefiles when creating 7day composites
        self.raster_handler.read_shp(daily_map_path)
        self.raster_handler.filter_shapes()
        self.raster_handler.rasterize()

        # Sea Track Web output
        if create_stw_files:
            start_time = time.time()
            subprocesses.create_stw(settings.stw_handler.coordframe, daily_map_path, settings.current_working_date,
                                    readers.shape_reader,
                                    QgsPointXY, QgsField, QgsFeature, QgsGeometry, QVariant
                                    )
            print("STW session completed in --%.2f sec\n" % (time.time() - start_time))

        # Weekly map
        if create_weekly_map:
            start_time = time.time()
            weekmap_path = self.layer_handler.create_7day_composite()
            print('sleeping for 2 seconds..')
            time.sleep(2)
            if weekmap_path:
                self.raster_handler.shapeify(weekmap_path)

            print("Weekly map session completed in --%.1f sec\n" % (time.time() - start_time))

        if not settings.log.date_in_log(settings.current_working_date):
            settings.log.append_date_to_list(settings.current_working_date)
            settings.log.save()

        if create_stw_files:
            self._check_for_stw_file(settings, gui_mxb)

    @staticmethod
    def _check_for_stw_file(settings, gui_func):
        """
        :return:
        """
        stw_path = os.path.join(settings.baws_USER_SELECTED_current_production_directory,
                                '_'.join(['stw', settings.current_working_date]) + '.txt')
        remove_file = False
        with open(stw_path) as searchfile:
            found = False
            while not found:
                for line in searchfile:
                    if 'no_stw' in line:
                        gui_func('No large surface accumulations and therefore no drift forecast is needed.')
                        found = True
                        remove_file = True
                        break
                    elif '' in line:
                        found = True
                        gui_func('A SeaTrackWeb file has been saved. '
                                 'Perform forecast on stw.smhi.se',
                                 picture_path=':/plugins/BAWS/resources/stw_pic.png')
                        break
                else:
                    searchfile.seek(0)  # reset file to the beginning for next search
                    time.sleep(0.05)
        if remove_file:
            searchfile.close()
            try:
                os.remove(stw_path)
            except:
                pass

    @staticmethod
    def daily_map(shape_handler, file_path=''):
        """
        Produces the daily Cyano-PNG-map over the Baltic Sea according to old format (during the transition period of
        summer 2019).
        :return:
        """
        print('Creating daily PNG-map..')
        plot_handler = handlers.MapHandler()

        __path__ = os.path.dirname(os.path.abspath(__file__))

        plot_handler.initialize_map()

        plot_handler.add_picture_to_figure(path_picture=__path__ + '/resources/smhi-logo.png',
                                           axes_settings=[0.835, 0.86, 0.1, 0.12])

        plot_handler.add_picture_to_figure(path_picture=__path__ + '/resources/legend.png',
                                           axes_settings=[0.74, 0.056, 0.2, 0.2])

        patches = shape_handler.get_matplotlib_patches(plot_handler)
        plot_handler.plot_patches(patches, map_axes=plot_handler.map_axes)

        plot_handler.save_figure(file_path.replace('.shp', '.png'),
                                 **{'bbox_inches': 'tight', 'dpi': 312, 'pad_inches': -0.003})
        print('Daily PNG-map saved!')

    @staticmethod
    def weekly_map(shape_handler, file_path=''):
        """
        Produces the daily Cyano-PNG-map over the Baltic Sea according to old format (during the transition period of
        summer 2019).
        :return:
        """
        print('Creating weekly PNG-map..')
        if file_path:
            plot_handler = handlers.MapHandler(colormap_properties={0: '#000000',
                                                                    1: '#0066ff',
                                                                    2: '#00ccff',
                                                                    3: '#99e2ff',
                                                                    4: '#Ffff33',
                                                                    5: '#Ff9933',
                                                                    6: '#Ff3300',
                                                                    7: '#990000'})
        else:
            return

        __path__ = os.path.dirname(os.path.abspath(__file__))

        plot_handler.initialize_map()

        plot_handler.add_picture_to_figure(path_picture=__path__ + '/resources/smhi-logo.png',
                                           axes_settings=[0.835, 0.86, 0.1, 0.12])

        patches = shape_handler.get_matplotlib_patches(plot_handler)
        plot_handler.plot_patches(patches, map_axes=plot_handler.map_axes)

        plot_handler.save_figure(file_path.replace('.shp', '.png'),
                                 **{'bbox_inches': 'tight', 'dpi': 312, 'pad_inches': -0.003})
        print('Weekly PNG-map saved!')
