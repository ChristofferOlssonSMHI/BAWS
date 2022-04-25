# -*- coding: utf-8 -*-
"""
Created on 2019-06-24 16:30

@author: a002028
"""
import os
import numpy as np
import fiona
import rasterio
from rasterio import features


def area2transform_baws10000_sweref99tm():
    """"""
    west, south, east, north = (-49739.0, 5954123.0, 1350261.0, 7354123.0)
    height, width = (140, 140)
    transform = rasterio.transform.from_bounds(west, south,
                                               east, north,
                                               width, height)
    return transform, (140, 140)


def get_stw_lats_lons(lon_path, lat_path, bloom_idx):
    """"""
    lons = np.load(lon_path)
    lats = np.load(lat_path)
    return np.array([lats[bloom_idx], lons[bloom_idx]]).transpose()


def save_empty_file(save_path):
    """"""
    with open(save_path, 'w') as file:
        file.write('no_stw')
    file.close()


def create_stw(cyano_file_path, file_tag, lon_path, lat_path):
    """"""
    out_folder = os.path.dirname(os.path.realpath(cyano_file_path))
    stw_file_path = os.path.join(
        out_folder,
        '_'.join(['stw', file_tag]) + '.txt'
    )
    transform, shape = area2transform_baws10000_sweref99tm()
    with fiona.open(cyano_file_path, "r") as shapefile:
        shapes = []
        for shp in shapefile:
            if shp['properties']['class'] == 3:
                shapes.append((shp['geometry'], 3))

    burned = features.rasterize(shapes=shapes, fill=0, out=np.zeros(shape),
                                transform=transform)
    bloom_indices = np.where(burned == 3)
    if np.shape(bloom_indices)[1] > 5:
        coordinates = get_stw_lats_lons(lon_path, lat_path, bloom_indices)
        np.savetxt(stw_file_path, coordinates, delimiter='\t',
                   fmt='%1.4f')
    else:
        save_empty_file(stw_file_path)
