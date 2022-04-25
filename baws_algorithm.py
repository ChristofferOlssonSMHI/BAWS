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

import os
from pathlib import Path
import time
from shutil import copyfile

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingOutputNumber,
    QgsVectorFileWriter,
    QgsProcessingParameterFeatureSource,
    QgsPointXY,
    QgsProject,
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry
)

from . import readers
from . import handlers
from . import subprocesses
from . import utils


class BAWSAlgorithm(QgsProcessingAlgorithm):
    """Based on example algorithm class."""

    def initialize_layer_handler(self, iface, settings):
        """Initialize the layer handler.

        Args:
            iface (QgisInterface): The QGIS interface instance.
            settings: The BAWS settings object.
        """
        if not hasattr(self, 'layer_handler'):
            self.layer_handler = handlers.LayerHandler(iface, settings)

    def initialize_ferrybox_handler(self, settings):
        """Initialize the ferrybox handler.

        Args:
            settings: The BAWS settings object.
        """
        if not hasattr(self, 'ferrybox_handler'):
            self.ferrybox_handler = handlers.FerryBoxHandler(settings)

    def initialize_raster_handler(self, rst_template_path):
        """Initialize the raster handler.

        Args:
            rst_template_path: path to raster meta template
        """
        if not hasattr(self, 'raster_handler'):
            self.raster_handler = handlers.RasterHandler(rst_template_path)

    def initialize_plot_handler(self, reset=False):
        """Initialize the plot handler.

        Args:
            reset: True/False
        """
        if reset or not hasattr(self, 'plot_handler'):
            self.plot_handler = handlers.MapHandler()
            utils.thread_process(self.plot_handler.initialize_maps)

    def rasterize_shapefiles(self, args, save_path=None):
        """Create raster files from shapefiles.

        Args:
            args: iterable of paths to shapefiles.
            save_path: path to save files.
        """
        for fid in args:
            utils.thread_process(subprocesses.rasterize_file,
                                 self.raster_handler.raster_meta,
                                 save_path,
                                 fid)
        utils.thread_process(subprocesses.check_while_saving,
                             save_path,
                             '.tiff',
                             len(args))

    def merge_selected_shapefiles(self, settings, categorize=True):
        """Merge the selected shape layers.

        Args:
            settings: The BAWS settings object.
            categorize: If true the layer will be categorized using
                        the classes 1-4
        """
        print('Starting merging work. Usually takes ~5-30 seconds, '
              'depending on size and number of geometries..')
        start_time = time.time()
        merge_file_path = os.path.join(settings.user_temporary_folder,
                                       'Cyano_merged.shp')
        self.raster_handler.merge_scene_shapes(
            layer_names=self.layer_handler.active_layers_name,
            output_filename=merge_file_path,
            mask_path=settings.raster_valid_area_file_path
        )

        self.import_merged_file(merge_file_path, categorize=categorize)

        print("merge_selected_shapefiles completed in --%.2f sec"
              "\n" % (time.time() - start_time))

    def merge_selected_rasterfiles(self, settings, categorize=True):
        """Merge the selected raster layers.

        Args:
            settings: The BAWS settings object.
            categorize: If true the layer will be categorized using
                        the classes 1-4
        """
        print('Starting merging work. Usually takes ~5-30 seconds, '
              'depending on size and number of geometries..')
        start_time = time.time()
        merge_file_path = os.path.join(settings.user_temporary_folder,
                                       'Cyano_merged.shp')
        self.raster_handler.merge_scene_rasters(
            layer_paths=self.layer_handler.active_cyano_tiff_layers_path,
            output_filename=merge_file_path,
        )
        self.import_merged_file(merge_file_path, categorize=categorize)

        print("merge_selected_rasterfiles completed in "
              "--%.2f sec\n" % (time.time() - start_time))

    def import_merged_file(self, merge_file_path, categorize=False,
                           filter_invalid_areas=False):
        """Import the merged file.

        Args:
            merge_file_path: path to file.
            categorize: If true the layer will be categorized using
                        the classes 1-4
            filter_invalid_areas: Exclude invalid geometries.
        """
        layer = readers.shape_reader('qgis', merge_file_path,
                                     'Cyano_merged', "ogr")
        if filter_invalid_areas:
            not_valid_feature_ids = \
                self.layer_handler.get_not_valid_feature_ids(layer=layer)
            self.layer_handler.delete_features(
                layer, feature_ids=not_valid_feature_ids
            )
        QgsProject.instance().addMapLayer(layer)
        if categorize:
            self.layer_handler.categorize_layer(
                layer_name='Cyano_merged',
                attr='class'
            )

        self.layer_handler.deactivate_layers(
            self.layer_handler.active_layers,
            exclude_layers=['Cyano_merged']
        )

    def _copy_tif_files(self, settings):
        """Copy file to path."""
        if not any(self.layer_handler.active_tif_layer_names):
            return
        files_to_copy = utils.generate_filepaths(
            settings.baws_USER_SELECTED_level_1_directory,
            pattern_list=self.layer_handler.active_tif_layer_names
        )
        for fid in files_to_copy:
            file_name = fid.split('\\')[-1]
            print('Copying %s to tif_archive' % file_name)
            dst_path = os.path.join(
                settings.baws_USER_SELECTED_tiff_archive_directory,
                file_name
            )
            utils.thread_process(copyfile, fid, dst_path)

        print('\nTif files are being copied in background threads')

    def save_files(self, settings, gui_mxb, layer_name='Cyano_merged',
                   daily_outpath=None, copy_tif_files=True,
                   create_text_files=True, create_stw_files=True,
                   create_weekly_map=True):
        """Save all BAWS files (shp, tiff, png).

        Includes format transformations (shp --> tiff and tiff --> shp)

        Args:
            settings:
            gui_mxb:
            layer_name:
            daily_outpath:
            copy_tif_files:
            create_text_files:
            create_stw_files:
            create_weekly_map:
        """
        # Daily tif files
        if copy_tif_files:
            self._copy_tif_files(settings)

        # Daily Textfiles
        if create_text_files:
            text_handler = handlers.TextFileHandler(settings)
            utils.thread_process(text_handler.copy_empty_files)

        # Daily shp and raster file
        print('Daily shape process...')
        start_time = time.time()
        daily_map_path = self.layer_handler.get_output_path_for_shape(
            'cyano_daymap_', daily_outpath)
        self.layer_handler.save_shapefile(layer_name=layer_name,
                                          path=daily_map_path,
                                          output_prefix='cyano_daymap_')

        # Rasterize the daily map. Super duper much more efficient than merging
        # shapefiles when creating 7day composites
        self.raster_handler.rasterize(daily_map_path)
        print("Daily shape/raster session completed in --%.1f sec"
              "\n" % (time.time() - start_time))

        # Sea Track Web output
        if create_stw_files:
            utils.thread_process(
                subprocesses.create_stw,
                daily_map_path,
                settings.current_working_date,
                *settings.baws_10000_paths
            )

        # Weekly shp and raster file
        if create_weekly_map:
            start_time = time.time()
            array, weekmap_path = self.layer_handler.create_7day_composite()
            if weekmap_path:
                self.raster_handler.shapeify(array, weekmap_path)
            print("Weekly shape session completed in --%.1f sec"
                  "\n" % (time.time() - start_time))

        if not settings.log.date_in_log(settings.current_working_date):
            settings.log.append_date_to_list(settings.current_working_date)
            settings.log.save()

        if create_stw_files:
            self._check_for_stw_file(settings, gui_mxb)

    @staticmethod
    def _check_for_stw_file(settings, gui_func):
        """Search for the creation of the SeaTrackWeb file."""
        stw_path = os.path.join(
            settings.baws_USER_SELECTED_current_production_directory,
            '_'.join(['stw', settings.current_working_date]) + '.txt'
        )
        remove_file = False
        with open(stw_path) as searchfile:
            found = False
            while not found:
                for line in searchfile:
                    if 'no_stw' in line:
                        gui_func('No large surface accumulations and therefore '
                                 'no drift forecast is needed.')
                        found = True
                        remove_file = True
                        break
                    elif '' in line:
                        found = True
                        gui_func(
                            'A SeaTrackWeb file has been saved. '
                            'Perform forecast on stw.smhi.se',
                            picture_path=':/plugins/BAWS/resources/stw_pic.png'
                        )
                        break
                else:
                    # reset file to the beginning for next search
                    searchfile.seek(0)
                    time.sleep(0.05)
        if remove_file:
            searchfile.close()
            try:
                os.remove(stw_path)
            except:
                pass

    def daily_map(self, shape_handler, file_path=''):
        """Produce the daily Cyano-PNG-map over the Baltic Sea."""
        print('Creating daily PNG-map..')
        directory = Path(__file__).parent

        self.plot_handler.add_picture_to_figure(
            self.plot_handler.day_figure,
            path_picture=str(directory.joinpath('resources/smhi-logo.png')),
            axes_settings=[0.835, 0.86, 0.1, 0.12]
        )

        self.plot_handler.add_picture_to_figure(
            self.plot_handler.day_figure,
            path_picture=str(directory.joinpath('resources/legend.png')),
            axes_settings=[0.74, 0.056, 0.2, 0.2]
        )

        patches = shape_handler.get_matplotlib_patches(
            self.plot_handler.day_map,
            self.plot_handler.day_colormap_properties
        )
        self.plot_handler.plot_patches(
            patches,
            map_axes=self.plot_handler.day_axes
        )

        self.plot_handler.save_figure(
            file_path.replace('.shp', '.png'),
            self.plot_handler.day_figure
        )
        print('Daily PNG-map saved!')

    def weekly_map(self, shape_handler, file_path=''):
        """Produce the weekly Cyano-PNG-map over the Baltic Sea."""
        print('Creating weekly PNG-map..')
        if not file_path:
            return

        self.plot_handler.add_picture_to_figure(
            self.plot_handler.week_figure,
            path_picture=str(Path(__file__).parent.joinpath(
                'resources/smhi-logo.png')),
            axes_settings=[0.835, 0.86, 0.1, 0.12]
        )

        patches = shape_handler.get_matplotlib_patches(
            self.plot_handler.week_map,
            self.plot_handler.week_colormap_properties
        )
        self.plot_handler.plot_patches(
            patches,
            map_axes=self.plot_handler.week_axes
        )

        self.plot_handler.save_figure(
            file_path.replace('.shp', '.png'),
            self.plot_handler.week_figure
        )
        print('Weekly PNG-map saved!')
