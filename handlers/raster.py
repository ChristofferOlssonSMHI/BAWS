# -*- coding: utf-8 -*-
"""
Created on 2020-05-13 16:39

@author: a002028

"""
import os
import numpy as np
import geopandas as gpd
import fiona
from fiona.crs import to_string
import rasterio
from rasterio import features
from rasterio.features import shapes, rasterize


def area2transform_baws1000_sweref99tm():
    crs = rasterio.crs.CRS.from_string('+init=epsg:3006')
    west, south, east, north = (-49739.0, 5954123.0, 1350261.0, 7354123.0)
    height, width = (1400, 1400)
    transform = rasterio.transform.from_bounds(west, south,
                                               east, north,
                                               width, height)
    return crs, transform, (height, width)


def area2transform_baws300_sweref99tm():
    crs = rasterio.crs.CRS.from_string('+init=epsg:3006')
    west, south, east, north = (-49739.0, 5954123.0, 1350361.0, 7354223.0)
    height, width = (4667, 4667)
    transform = rasterio.transform.from_bounds(west, south,
                                               east, north,
                                               width, height)
    return crs, transform, (height, width)


class RasterHandler(object):
    """
    """
    def __init__(self, raster_template_path=None):
        try:
            assert type(raster_template_path) == str
            rst = rasterio.open(raster_template_path)
            self.raster_meta = rst.meta.copy()
            self.raster_meta.update(compress='lzw')
        except:
            pass
        self.save_path = None
        self.shapes = None

    @staticmethod
    def buffer_geom(gdf):
        """
        :param gdf:
        :return:
        """
        gdf[u'geometry'] = gdf.buffer(0)

    def read_shp(self, path):
        """
        :return:
        """
        print('Reading shapefile..')
        self.save_path = path.replace('.shp', '.tiff')
        self.shapes = gpd.read_file(path)

    def filter_shapes(self, polygon_key='class', value_list=None):
        """
        :param polygon_key:
        :param value_list:
        :return:
        """
        print('Searching for points in polygons..')
        value_list = value_list or [1, 2, 3, 4]

        filter_boolean = self.shapes[polygon_key].isin(value_list)
        filter_shapes = self.shapes.loc[filter_boolean]
        filter_shapes['sort_order'] = ''

        # Value 1 (cloud) will be printed on top of all other.
        # Value 4 (No data) will only be printed if there are no other values to be printed.
        sorting_mapping = {1: 'D', 2: 'B', 3: 'C', 4: 'A'}
        for key, value in sorting_mapping.items():
            boolean = filter_shapes['class'] == key
            filter_shapes.loc[boolean, 'sort_order'] = value

        filter_shapes.sort_values(by='sort_order', ascending=True, inplace=True)

        self.buffer_geom(filter_shapes)

        self.shapes = filter_shapes

    def rasterize(self, save_path=None):
        """
        :param save_path:
        :return:
        """
        print('Rasterizing...')
        with rasterio.open(save_path or self.save_path, 'w+', **self.raster_meta) as out:
            out_arr = out.read(1)
            shapes = ((geom, value) for geom, value in list(zip(self.shapes['geometry'],
                                                                self.shapes['class'])))  # self.shapes.index))
            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)

    def shapeify(self, weekday_rst_path):
        rst = rasterio.open(weekday_rst_path)
        array = rst.read()
        array = array[0]
        array = array.astype(int)

        print('get_shapes_from_raster')
        shape_list = self.get_shapes_from_raster(array, None, daymaps=False)

        fname = weekday_rst_path.replace('.tiff', '.shp')
        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

        # crs, transform, area_shape = area2transform_baws300_sweref99tm()
        crs, transform, area_shape = area2transform_baws1000_sweref99tm()

        with fiona.open(fname, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)

        print('shapeify completed!')

    @staticmethod
    def get_shapes_from_raster(raster, mask_file, daymaps=False):
        shapes_with_properties = []
        # crs, transform, area_shape = area2transform_baws300_sweref99tm()
        crs, transform, area_shape = area2transform_baws1000_sweref99tm()

        classes = {int(cls): {'class': int(cls)} for cls in np.unique(raster)}
        classes[0] = None

        if mask_file:
            with fiona.open(mask_file, "r") as shapefile:
                mask_features = [feature["geometry"] for feature in shapefile]
            mask = rasterize(mask_features, area_shape, transform=transform)
        else:
            mask = None

        if daymaps:
            covered = False
            for i, (s, v) in enumerate(shapes(raster, mask=mask, transform=transform)):
                if v != 4:
                    covered = True
                if v in [0, 1, 4]:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)], 'geometry': s})
            if not covered:
                return None

            # Clouds ontop!
            for i, (s, v) in enumerate(shapes(raster, transform=transform)):
                if v in [0, 2, 3]:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)], 'geometry': s})
        else:
            covered = False
            for i, (s, v) in enumerate(shapes(raster, mask=mask, transform=transform)):
                if v == 0:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)], 'geometry': s})

        return shapes_with_properties

    def merge_scene_shapes(self, layer_names=None, output_filename=None, mask_path=None):
        """
        :param shp_files_path:
        :return:
        """
        assert output_filename is not None

        if mask_path:
            print('Applying valid area mask')
            mask = rasterio.open(mask_path)
            mask = mask.read()
            mask = mask[0].astype(int)
        else:
            # If no mask given: All area is valid (value 1)
            mask = np.zeros((1400, 1400)) + 1

        arrays = []
        for fid in layer_names:
            rst = rasterio.open(os.path.join(os.path.dirname(output_filename),
                                             os.path.basename(fid).replace('.shp', '.tiff')))
            array = rst.read()
            array = array[0].astype(int)

            if 'ferry_box_data' in fid:
                # FerryBox data only covers the actual ferrybox transect and can't "see" any other area.
                array = np.where(array == 0, 4, array)

            # Exclude areas marked with class value 2 or 3 outside of our "valid_baws_area".
            # Mask value 1 marks valid area; Maske value 0 marks not valid area
            array = np.where(np.logical_and(mask == 0,
                                            np.logical_or(array == 2, array == 3)),
                             0, array)
            arrays.append(array)

        daily_array = arrays[0]
        if len(arrays) == 1:
            pass
        else:
            for scene in arrays[1:]:
                daily_array = np.where(np.logical_and(daily_array == 1, scene == 0), 0, daily_array)
                daily_array = np.where(daily_array == 4, scene, daily_array)
                daily_array = np.where(np.logical_and(daily_array != 3, scene == 2), 2, daily_array)
                daily_array = np.where(scene == 3, 3, daily_array)

        shape_list = self.get_shapes_from_raster(daily_array, None, daymaps=False)
        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}
        crs, transform, area_shape = area2transform_baws1000_sweref99tm()

        with fiona.open(output_filename, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)
