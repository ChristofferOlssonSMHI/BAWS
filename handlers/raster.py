# -*- coding: utf-8 -*-
"""
Created on 2020-05-13 16:39

@author: a002028

"""
import os
import numpy as np
import fiona
from fiona.crs import to_string
from shapely.geometry import MultiPolygon, mapping, shape
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


class RasterHandler:
    """"""

    def __init__(self, raster_template_path=None):
        """Initialize.

        Args:
            raster_template_path:
        """
        try:
            assert type(raster_template_path) == str
            rst = rasterio.open(raster_template_path)
            self.raster_meta = rst.meta.copy()
            self.raster_meta.update(compress='lzw')
        except:
            pass
        self.save_path = None
        self.shapes = None

    def rasterize(self, cyano_file_path, save_path=None):
        """"""
        print('Rasterizing...')
        save_path = save_path or cyano_file_path.replace('.shp', '.tiff')
        with fiona.open(cyano_file_path, "r") as shapefile:
            classes = {c: [] for c in range(1, 5)}
            for shp in shapefile:
                if shp['properties']['class'] in classes:
                    classes[shp['properties']['class']].append(
                        (shp['geometry'], shp['properties']['class'])
                    )
        shapes = []
        for c in (4, 2, 3, 1):
            shapes.extend(classes[c])
        with rasterio.open(save_path, 'w+', **self.raster_meta) as out:
            out_arr = out.read(1)
            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr,
                                        transform=out.transform)
            out.write_band(1, burned)

    def shapeify(self, array, weekday_rst_path):
        """"""
        print('get_shapes_from_raster')
        shape_list = self.get_shapes_from_raster(array, None)

        fname = weekday_rst_path.replace('.tiff', '.shp')
        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

        crs, _, _ = area2transform_baws1000_sweref99tm()

        with fiona.open(fname, 'w', driver='ESRI Shapefile',
                        crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)
        print('shapeify completed!')

    @staticmethod
    def get_shapes_from_raster(raster, mask_file, daymaps=False):
        """"""
        shapes_with_properties = []
        _, transform, area_shape = area2transform_baws1000_sweref99tm()

        classes = {int(cls): {'class': int(cls)} for cls in np.unique(raster)}
        classes[0] = None

        if mask_file:
            with fiona.open(mask_file, "r") as shapefile:
                mask_features = [feature["geometry"] for feature in shapefile]
            mask = rasterize(mask_features, area_shape, transform=transform)
        else:
            mask = None

        blooms = {0, 2, 3}
        others = {0, 1, 4}
        if daymaps:
            covered = False
            for s, v in shapes(raster, mask=mask, transform=transform):
                if v != 4:
                    covered = True
                if v in others:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)],
                                               'geometry': s})
            if not covered:
                return None

            # Clouds ontop!
            for s, v in shapes(raster, transform=transform):
                if v in blooms:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)],
                                               'geometry': s})
        else:
            for s, v in shapes(raster, mask=mask, transform=transform):
                if v == 0:
                    continue
                shapes_with_properties.append({'properties': classes[int(v)],
                                               'geometry': s})
        return shapes_with_properties

    def merge_scene_shapes(self, layer_names=None, output_filename=None,
                           mask_path=None):
        """"""
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
            rst = rasterio.open(
                os.path.join(os.path.dirname(output_filename),
                             os.path.basename(fid).replace('.shp', '.tiff'))
            )
            array = rst.read()
            array = array[0].astype(int)

            if 'ferry_box_data' in fid:
                # FerryBox data only covers the actual ferrybox transect and
                # can't "see" any other area.
                array = np.where(array == 0, 4, array)

            # Exclude areas marked with class value 2 or 3 outside
            # of our "valid_baws_area".
            # Mask value 1 marks valid area; Maske value 0 marks not valid area
            array = np.where(
                np.logical_and(
                    mask == 0, np.logical_or(array == 2, array == 3)),
                0, array
            )
            arrays.append(array)

        daily_array = arrays[0]
        if len(arrays) == 1:
            pass
        else:
            for scene in arrays[1:]:
                daily_array = np.where(
                    np.logical_and(daily_array == 1,
                                   scene == 0), 0, daily_array
                )
                daily_array = np.where(daily_array == 4, scene, daily_array)
                daily_array = np.where(
                    np.logical_and(daily_array != 3,
                                   scene == 2), 2, daily_array
                )
                daily_array = np.where(scene == 3, 3, daily_array)

        shape_list = self.get_shapes_from_raster(
            daily_array, None, daymaps=False
        )
        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}
        crs, transform, area_shape = area2transform_baws1000_sweref99tm()

        with fiona.open(output_filename, 'w', driver='ESRI Shapefile',
                        crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)

    def merge_scene_rasters(self, layer_paths=None, output_filename=None):
        """"""
        crs, transform, _ = area2transform_baws1000_sweref99tm()
        daily_array = np.array(())
        for fid in layer_paths:
            rst = rasterio.open(fid)
            array = rst.read()
            array = array[0].astype(int)

            if not daily_array.size:
                daily_array = array
            else:
                daily_array = np.where(
                    np.logical_and(daily_array == 1,
                                   array == 0), 0, daily_array
                )
                daily_array = np.where(daily_array == 4, array, daily_array)
                daily_array = np.where(
                    np.logical_and(daily_array != 3,
                                   array == 2), 2, daily_array
                )
                daily_array = np.where(array == 3, 3, daily_array)

        bloom_array = np.where(
            np.logical_or(daily_array == 3, daily_array == 2), 2,
            np.zeros(daily_array.shape)
        )
        bloom_array = np.where(daily_array == 1, 0,
                               bloom_array).astype(np.uint8)

        valid_areas = utils.valid_baws_area()
        if bloom_array.any():
            bloom_shape_list = self.get_shapes_from_raster(bloom_array, None)
            mask_features = []
            for shp in bloom_shape_list:
                poly = shape(shp['geometry'])
                if not poly.is_empty:
                    if poly.area < valid_areas[2]:
                        # valid_areas[2]: valid area for class 2 (and 3) bloom
                        mask_features.append(shp["geometry"])
            mask = rasterize(mask_features, bloom_array.shape,
                             transform=transform)
            daily_array = np.where(mask == 1, 0, daily_array)

        shapes_from_raster = self.get_shapes_from_raster(daily_array, None)

        shape_list = []
        for shp in shapes_from_raster:
            poly = shape(shp['geometry'])
            if not poly.is_valid:
                # This might be completely unnecessary since shapely 1.8
                be = poly.exterior
                mls = be.intersection(be)
                polygons = polygonize(mls)
                valid_bowtie = MultiPolygon(polygons)
                for poly_of_multi in list(valid_bowtie):
                    if poly_of_multi.is_valid:
                        if shp['properties']['class'] == 1:
                            if poly_of_multi.area < valid_areas[1]:
                                continue
                        new_shape = shp.copy()
                        new_shape['geometry'] = mapping(poly_of_multi)
                        shape_list.append(new_shape)
            else:
                if shp['properties']['class'] == 1:
                    if poly.area < valid_areas[1]:
                        continue
                shape_list.append(shp)

        schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}
        with fiona.open(output_filename, 'w', driver='ESRI Shapefile',
                        crs=to_string(crs), schema=schema) as dst:
            dst.writerecords(shape_list)
