# -*- coding: utf-8 -*-
"""
Created on 2020-05-15 17:53

@author: a002028
"""
import os
import rasterio as rio
from rasterio import features
import geopandas as gpd
from .. import utils


def filter_feature(gp_shapes):
    """Valid area (m3). If not used, data look somewhat stochastic."""
    valid_class_areas = utils.valid_baws_area()

    boolean = False
    for cls, val_area in valid_class_areas.items():
        cls_boolean = gp_shapes['class'] == cls
        cls_boolean = cls_boolean & (gp_shapes.geometry.area >= val_area)
        boolean = boolean | cls_boolean
    return gp_shapes.loc[boolean, :]


def rasterize_file(meta, folder_path, fid):
    """"""
    shapes = gpd.read_file(fid)
    shapes = filter_feature(shapes)
    shapes.geometry = shapes.buffer(0)
    save_path = os.path.join(folder_path,
                             os.path.basename(fid).replace('.shp', '.tiff'))
    with rio.open(save_path, 'w+', **meta) as out:
        out_arr = out.read(1)
        shapes = ((geom, value) for geom, value in zip(shapes['geometry'],
                                                       shapes['class']))
        burned = features.rasterize(shapes=shapes, fill=0, out=out_arr,
                                    transform=out.transform)
        out.write_band(1, burned)
