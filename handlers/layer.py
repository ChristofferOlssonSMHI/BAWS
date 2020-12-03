# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:15

@author: a002028

"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import map
from builtins import str
from builtins import range
from builtins import object

from qgis.core import (QgsProject,
                       QgsVectorLayer,
                       QgsField,
                       QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer,
                       QgsSimpleLineSymbolLayer)

import os

import shapely
import descartes

from .. import readers
from .. import writers
from .. import utils


class BaseShapeHandler(object):
    """
    """
    def __init__(self):
        super(BaseShapeHandler, self).__init__()

    def append_area_to_dictionary(self, dictionary, key, attr='class', value_list=[]):
        """
        :param dictionary:
        :param key:
        :param attr:
        :param value_list:
        :return:
        """
        filter_boolean = self.shapes[attr].isin(value_list)
        filter_shapes = self.shapes.loc[filter_boolean]
        area = utils.round_value(filter_shapes['geometry'].area.sum() / 10 ** 6,
                                 nr_decimals=1, out_format=float)
        dictionary[key] = area

    def calculate_area(self, attr='class'):
        """
        :param area_dict:
        :param attr:
        :param value_list:
        :param sum_key:
        :param mapping:
        :return:
        """
        if not hasattr(self, 'shapes'):
            print('NO SHAPES LOADED! :( ')
            return

        for value in self.value_list:
            self.append_area_to_dictionary(self.area_dict, self.mapping.get(value),
                                           attr=attr, value_list=[value])

        self.append_area_to_dictionary(self.area_dict, self.sum_key,
                                       attr=attr, value_list=self.value_list)
        self.active_area = True

    def get_matplotlib_patches(self, map_obj, attr_key='class'):
        """
        :return:
        """
        patches_dict = {value: [] for value in self.prioritized_values}

        for poly, value in zip(self.shapes['geometry'], self.shapes[attr_key]):

            if int(value) == 0:
                # Dummy value '0' is regarded as a DUMMY value :)
                continue

            if poly.geom_type == 'Polygon':
                mpoly = shapely.ops.transform(map_obj.map, poly)
                patches_dict[value].append(descartes.PolygonPatch(mpoly,
                                                                  lw=0.15,
                                                                  ec=map_obj.colormap_properties[value],
                                                                  color=map_obj.colormap_properties[value]))
            elif poly.geom_type == 'MultiPolygon':
                for subpoly in poly:
                    # mpoly = shapely.ops.transform(map_obj.map, poly)
                    mpoly = shapely.ops.transform(map_obj.map, subpoly)  # correct?
                    patches_dict[value].append(descartes.PolygonPatch(mpoly,
                                                                      lw=0.15,
                                                                      ec=map_obj.colormap_properties[value],
                                                                      color=map_obj.colormap_properties[value]))
            else:
                print('Not working......')

        patches_list = []
        # Extend patches_list accoring to backward class priority.
        # This way geometries for the last class is plotted on top of all other classes.
        for i in self.prioritized_values:
            patches_list.extend(patches_dict[i])

        return patches_list

    def change_csr(self):
        """
        :return:
        """
        self.shapes['geometry'] = self.shapes['geometry'].to_crs(epsg=self.as_epsg)

    def read(self, path):
        """
        ERROR: geometries that are None
        k=0
        for i in range(1729):
            if shapes.iloc[i].geometry == None:
                k+=1
        :param path: path to shape file
        :return: GeoPandas.DataFrame
        """
        self.shapes = readers.shape_reader('geopandas', *(path, ))


class DailyShapeHandler(BaseShapeHandler):
    """
    """
    def __init__(self):
        super(DailyShapeHandler, self).__init__()
        self.area_dict = {}
        self.active_area = False
        self.as_epsg = 4326
        self.value_list = [2, 3]
        self.sum_key = 'daily_bloom_area'
        self.mapping = {2: 'subsurface_area', 3: 'surface_area'}
        self.prioritized_values = [4, 2, 3, 1]


class WeeklyShapeHandler(BaseShapeHandler):
    """
    """
    def __init__(self):
        super(WeeklyShapeHandler, self).__init__()
        self.area_dict = {}
        self.active_area = False
        self.as_epsg = 4326
        self.value_list = list(range(1, 8))
        self.sum_key = 'weekly_bloom_area'
        self.mapping = {i: '%i-day bloom' % i for i in range(1, 8)}
        self.prioritized_values = list(range(1, 8))


class LayerHandler(object):
    """
    """
    def __init__(self, iface, settings):
        self.iface = iface
        self.settings = settings
        self.number_of_layers_merged = None

    @property
    def active_layers(self):
        """
        Here we intend to use only .shp files
        :return:
        """
        return [layer for layer in self.iface.mapCanvas().layers() if not layer.name().endswith('.tif')
                and 'coastline' not in layer.name()]

    @property
    def active_layers_name(self):
        """
        Here we intend to use only .tif files
        :return:
        """
        return [layer.name() for layer in self.iface.mapCanvas().layers() if not layer.name().endswith('.tif')
                and 'coastline' not in layer.name()]

    @property
    def active_tif_layers(self):
        """
        Here we intend to use only .tif files
        :return:
        """
        return [layer for layer in self.iface.mapCanvas().layers() if layer.name().endswith('.tif')]

    @property
    def active_tif_layer_names(self):
        """
        Here we intend to use only .tif files
        :return:
        """
        return [layer.name() for layer in self.active_tif_layers]

    @property
    def active_layer(self):
        """
        :return:
        """
        if len(self.active_layers) == 1:
            return self.active_layers[0]
        else:
            return None

    @property
    def all_layers(self):
        """
        :return:
        """
        return list(QgsProject.instance().mapLayers().values())

    @property
    def all_baws_shape_layers(self):
        """
        :return:
        """
        return [layer for layer in list(QgsProject.instance().mapLayers().values())
                if not layer.name().endswith('.tif')
                and 'ocean_color' not in layer.name()
                and 'coastline' not in layer.name()]

    @staticmethod
    def deactivate_layers(layers, exclude_layers=None):
        exclude_layers = exclude_layers or []
        for layer in layers:
            if layer.name() in exclude_layers:
                continue
            QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(False)

    def _delete_layers(self, layers):
        """
        :param layers:
        :return:
        """
        try:
            QgsProject.instance().removeMapLayers(layers)
        except TypeError:
            print('TypeError occurred. Trying o delete by using layer.id()')
            QgsProject.instance().removeMapLayers([l.id() for l in layers])

    def delete_layers(self, all=False, name=None, layer_list=[], name_list=[]):
        """
        :param layers:
        :param name_list:
        :return:
        """
        layers = []
        if name:
            layer_by_name = self.get_layer_by_name(name)
            if layer_by_name is not None:
                layer_list.append(layer_by_name)
        if any(layer_list):
            layers.extend(layer_list)
        if any(name_list):
            if type(name_list) == list:
                for name in name_list:
                    layer = self.get_layer_by_name(name)
                    if layer:
                        layers.append(layer)
        if all:
            layers = self.all_layers

        if any(layers):
            self._delete_layers(layers)

    @staticmethod
    def delete_features(layer, feature_ids=[]):
        """
        :return:
        """
        print('BAWS_info: Found invalid geometries, deleting features before saving..')
        layer.startEditing()
        for feat_id in feature_ids:
            layer.deleteFeature(feat_id)
        layer.commitChanges()
        print('BAWS_info: features delete! :)')

    def get_layer_by_name(self, name):
        """
        :return:
        """
        for layer in self.active_layers:
            if layer.name() == name:
                return layer
        for layer in self.all_baws_shape_layers:
            if layer.name() == name:
                return layer
        print('Warning! No layer named: "%s" was found? Already ' % name)
        return None

    def _refresh(self):
        """
        :return:
        """
        self.iface.mapCanvas().refreshAllLayers()

    def refresh_layers(self):
        """
        It seems like Python - QGIS - PyQGIS somehow needs this refresh in order to not get ahead of themselves..
        :return:
        """
        refresh = self._refresh()
        return True

    def get_not_valid_feature_ids(self, layer=None, valid_area=10000000):
        """
        :param valid_area: Valid area (m3). If not used, data look somewhat stochastic..
        :return:
        """
        feature_ids = []
        for i, feat in enumerate(layer.getFeatures()):
            geom = feat.geometry()
            if feat['class'] == 1:
                if geom.area() < valid_area * 3:
                    feature_ids.append(i)
            elif feat['class'] == 4:
                if geom.area() < valid_area * 50:
                    feature_ids.append(i)
            elif geom.area() < valid_area:
                feature_ids.append(i)
        return feature_ids

    @staticmethod
    def get_nonetype_feature_ids(layer):
        """
        :param valid_area: Valid area (m3). If not used, data look somewhat stochastic..
        :return:
        """
        feature_ids = []
        for i, feat in enumerate(layer.getFeatures()):
            geom = feat.geometry()
            if geom.area() < 1:
                feature_ids.append(i)
        return feature_ids

    def change_class_values(self, layer=None, attr='class', class_value=None):
        """
        :return:
        """
        try:
            attr_idx = layer.fields().indexFromName(attr)
        except:
            attr_idx = 0
        selection = layer.selectedFeatures()
        if any(selection):
            for feat in selection:
                layer.changeAttributeValue(feat.id(), attr_idx, class_value)

    def categorize_layer(self, layer=None, attr='class', layer_name='Cyano_merged'):
        """
        :param attr:
        :return:
        """
        if not layer:
            layer = self.get_layer_by_name(layer_name)

        try:
            attr_idx = layer.fields().indexFromName(attr)
        except:
            attr_idx = 0

        unique_values = layer.uniqueValues(attr_idx)
        categories = []

        color_map = {0: '0, 0, 0', 1: '187, 187, 187', 2: '255, 255, 26', 3: '247, 126, 60', 4: '0, 0, 0'}
        color_map_hex = {0: '#000000', 1: '#bbbbbb', 2: '#ffff1a', 3: '#f77e3c', 4: '#000000'}
        for value in unique_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            layer_style = {'color': color_map[value],
                           'outline': color_map_hex[value]}
            symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(value, symbol, str(value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(attr, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

        layer.triggerRepaint()

    def categorize_line_layer(self, layer=None, attr='FID_1', layer_name=None):
        """
        :param attr:
        :return:
        """
        if not layer:
            layer = self.get_layer_by_name(layer_name)
        try:
            attr_idx = layer.fields().indexFromName(attr)
        except:
            print('Could not get attr_idx, using 0.. correct?')
            attr_idx = 0
        unique_values = layer.uniqueValues(attr_idx)

        categories = []

        color_map = {0: '0, 0, 0', 1: '21, 153, 137'}
        color_map_hex = {0: '#000000', 1: '#159989'}
        for value in unique_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            layer_style = {'color': color_map[value],
                           'outline': color_map_hex[value]}
            symbol_layer = QgsSimpleLineSymbolLayer.create(layer_style)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(value, symbol, str(value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(attr, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

        layer.triggerRepaint()

    def get_output_layer(self, layer_name=None):
        """
        Called by self.save_shapefile()
        :return:
        """
        if layer_name:
            layer = self.get_layer_by_name(layer_name)
            if not layer:
                return self.get_output_layer()
        elif self.active_layer:
            layer = self.active_layer
        else:
            raise NameError('No layer to save. No layer_name given and self.active_layer is None')
        return layer

    def save_shapefile(self, layer_name=None, path='', output_prefix=''):
        """
        :return:
        """
        layer = self.get_output_layer(layer_name=layer_name)

        feature_ids = self.get_nonetype_feature_ids(layer)
        if any(feature_ids):
            self.delete_features(layer, feature_ids=feature_ids)

        args = (layer, path, "utf-8")
        kwargs = {'driverName': "ESRI Shapefile"}
        print('Saving shape to: %s' % path)
        writers.shape_writer('qgis', *args, **kwargs)

        self.files_ready_check(self.settings.generate_filepaths,
                               os.path.dirname(path),
                               pattern=output_prefix)

    @staticmethod
    def files_ready_check(generator_func, path, pattern=''):
        """
        :param path:
        :param pattern:
        :return:
        """
        print('Sleeping while files are being saved..')
        file_paths = generator_func(path, pattern=pattern, only_from_dir=True)
        utils.sleep_while_saving(file_paths)

    def get_output_path_for_shape(self, prefix, outpath=None, suffix='.shp'):
        """
        :return:
        """
        if not outpath:
            outpath = self.settings.baws_USER_SELECTED_current_production_directory
        return ''.join([outpath, '\\', prefix, self.settings.current_working_date, suffix])

    def delete_class_geometries(self, layer, layer_name=None, class_list=[]):
        """
        :param layer:
        :param layer_name:
        :param class_list:
        :return:
        """
        if layer:
            pass
        elif layer_name:
            layer = self.get_layer_by_name(layer_name)
        else:
            print('Could not delete dublicate geometries, due to no given layer!')
            return

        print('\nDeleting geometries with class values %s' % ', '.join(map(str, class_list)))
        delete_ids = []
        for feat in layer.getFeatures():
            if feat.geometry() is None:
                delete_ids.append(feat.id())
            elif feat['class'] in class_list:
                delete_ids.append(feat.id())

        self.delete_features(layer, feature_ids=delete_ids)
        self.refresh_layers()

    @staticmethod
    def get_size_hierarchy(files):
        """
        :param files: list of file paths
        :return: sorted file list based on file size (large --> small)
        """
        file_sizes = utils.get_file_sizes(files)
        return sorted(file_sizes, key=lambda k: file_sizes[k], reverse=True)

    @staticmethod
    def get_file_sets(files):
        """
        :return:
        """
        return [files[0::2], files[1::2]]

    def create_7day_composite(self):
        """
        :return:
        """
        # TODO Move to RasterHandler
        import rasterio as rio
        import numpy as np
        print('\nCreating 7day composite..')
        file_generator = self.select_files_for_composite()
        zeros = np.array(())
        week_bloom = None
        raster_meta = None
        for fid in file_generator:
            print('Adding {} to composite file selection'.format(os.path.basename(fid)))
            rst = rio.open(fid)
            array = rst.read()
            array = array[0]

            if not zeros.size:
                # First iteration of loop: We resets "zeros" to the shape of "array" and extract raster metadata
                # (used for creation of new tiff-file)
                zeros = np.zeros(array.shape)
                week_bloom = np.zeros(zeros.shape)
                raster_meta = rst.meta.copy()

            day_bloom = np.where(np.logical_or(array == 2, array == 3), 1, zeros)

            week_bloom = week_bloom + day_bloom

        raster_meta.update(compress='lzw')
        fid_rst_week = fid.replace('_daymap_', '_weekmap_')
        print('writing to {}'.format(fid_rst_week))
        with rio.open(fid_rst_week, 'w+', **raster_meta) as out:
            out.write(week_bloom.astype(np.uint8), 1)
        out.close()

        return fid_rst_week

    def select_files_for_composite(self):
        """
        :return:
        """
        file_generator = self.settings.generate_filepaths(self.settings.baws_USER_SELECTED_manuell_algtolkning_directory,
                                                          pattern='cyano_daymap',
                                                          pattern_list=self.settings.date_range_composite,
                                                          endswith='.tiff')
        # We exclude precreated file for current_working_date
        files = [fid for fid in file_generator if self.settings.current_working_date not in fid]

        # Now we add file for current_working_date from our production folder
        file_generator = self.settings.generate_filepaths(self.settings.baws_USER_SELECTED_current_production_directory,
                                                          pattern='cyano_daymap_'+self.settings.current_working_date,
                                                          endswith='.tiff')
        files.extend([fid for fid in file_generator])

        return files
