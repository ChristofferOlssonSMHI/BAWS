# -*- coding: utf-8 -*-
"""
Created on 2019-07-22 14:15

@author: a002028

"""
from __future__ import print_function

from builtins import range
import geopandas as gp
import pandas as pd
import shapely
import re
import os
from shapely.wkt import loads
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon



def explode(indf):
    print('exploding..')
    outdf = gp.GeoDataFrame(columns=indf.columns)
    for idx, row in indf.iterrows():
        if type(row.geometry) == Polygon:
            outdf = outdf.append(row, ignore_index=True)
        if type(row.geometry) == MultiPolygon:
            multdf = gp.GeoDataFrame(columns=indf.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row]*recs, ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom, 'geometry'] = row.geometry[geom]
            outdf = outdf.append(multdf, ignore_index=True)
    return outdf


def mround(match):
    return "{:.0f}".format(float(match.group()))


fids = [
    '\\cyano_daymap_20190720.shp',
]

# changes = {path: os.path.getmtime(path) for path in file_paths}

crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

values = {2: True, 3: True}
simpledec = re.compile(r"\d*\.\d+")


for fid in fids:
    print(fid)
    shapes = gp.read_file(fid)
    crs = shapes.crs
    crs[u'init'] = u'epsg:3006'
    date = int(fid.split(u'_')[-1].replace(u'.shp', u''))
    shapes = explode(shapes)
    for i, row in shapes.iterrows():
        if len(row.geometry.exterior.coords.xy[0]) < 3:
            print('HHEEEEJ')
    shapes_boolean = shapes[u'class'].isin([2, 3])
    shapes_filter = shapes.loc[shapes_boolean]
    shapes_filter[u'geometry'] = shapes_filter.buffer(0)
    # polys = []
    # for i, row in shapes_filter.iterrows():
    #     polys.append(row[u'geometry'])
    # polys = shapes_filter['geometry'].tolist()
    # polyout = shapely.ops.unary_union(polys)
    #
    # # shape_header = ['cloud', 'sub_surface', 'surface', 'no_data', 'class', 'color_hex']
    # shape_header = ['class']
    # features = {key: [3]*len(polyout) for key in shape_header}
    # features = pd.DataFrame(features, columns=shape_header)
    # outpath = fid.replace(u'cyano_daymap', u'cyano_union_bloom')
    # output = gp.GeoDataFrame(features, crs=crs, geometry=[p for p in polyout])
    # print('rounding coords..')
    # output.geometry = output.geometry.apply(lambda x: loads(re.sub(simpledec, mround, x.wkt)))
    # print('rounding completed')
    # output.to_file(driver=u'ESRI Shapefile', crs_wkt=crs_wkt, filename=outpath)
    #
