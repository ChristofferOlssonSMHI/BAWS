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
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.ops import polygonize
import rasterio
from rasterio import features
from rasterio.features import shapes, rasterize
from .. import utils


def area2transform_baws1000_sweref99tm():
    crs = rasterio.crs.CRS.from_string('epsg:3006')
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
        gdf['geometry'] = gdf.buffer(0)

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

    def merge_scene_rasters(self, layer_names=None, directory=None, output_filename=None):
        crs, transform, shape = area2transform_baws1000_sweref99tm()

        daily_array = np.array(())
        for fid in layer_names:
            rst = rasterio.open(os.path.join(directory, fid))
            array = rst.read()
            array = array[0].astype(int)

            if not daily_array.size:
                daily_array = array
            else:
                daily_array = np.where(np.logical_and(daily_array == 1, array == 0), 0, daily_array)
                daily_array = np.where(daily_array == 4, array, daily_array)
                daily_array = np.where(np.logical_and(daily_array != 3, array == 2), 2, daily_array)
                daily_array = np.where(array == 3, 3, daily_array)

        bloom_array = np.where(np.logical_or(daily_array == 3, daily_array == 2), 2, np.zeros(daily_array.shape))
        bloom_array = np.where(daily_array == 1, 1, bloom_array).astype(np.uint8)

        bloom_shape_list = self.get_shapes_from_raster(bloom_array, None, daymaps=False)
        valid_areas = utils.valid_baws_area()
        mask_features = []
        for shape in bloom_shape_list:
            if type(shape['geometry']['coordinates'][0]) == list:
                poly = Polygon(shape['geometry']['coordinates'][0])
            else:
                poly = Polygon(shape['geometry']['coordinates'])

            if not poly.is_empty:
                if poly.area < valid_areas[2]:
                    # valid_areas[2]: valid area for class 2 (and 3) bloom
                    mask_features.append(shape["geometry"])
                elif shape['properties']['class'] == 1:
                    if poly.area < valid_areas[1]:
                        # valid_areas[1]: valid area for class 1 (cloud))
                        mask_features.append(shape["geometry"])

        mask = rasterize(mask_features, bloom_array.shape, transform=transform)
        daily_array = np.where(mask == 1, 0, daily_array)

        shapes_from_raster = self.get_shapes_from_raster(daily_array, None, daymaps=False)
        shape_list = []
        for shape in shapes_from_raster:
            if type(shape['geometry']['coordinates'][0]) == list:
                poly = Polygon(shape['geometry']['coordinates'][0])
            else:
                poly = Polygon(shape['geometry']['coordinates'])
            if not poly.is_valid:
                be = poly.exterior
                mls = be.intersection(be)
                polygons = polygonize(mls)
                valid_bowtie = MultiPolygon(polygons)
                for poly_of_multi in list(valid_bowtie):
                    if poly_of_multi.is_valid:
                        new_shape = shape.copy()
                        new_shape['geometry'] = mapping(poly_of_multi)
                        shape_list.append(new_shape)
            else:
                shape_list.append(shape)

        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}
        with fiona.open(output_filename, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)
