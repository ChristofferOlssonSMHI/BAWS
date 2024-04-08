# -*- coding: utf-8 -*-
"""
Created on 2019-07-22 16:19

@author: a002028

"""
import geopandas as gp
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.linestring import LineString
import pandas as pd
import shapely

def explode(indf):
    outdf = gp.GeoDataFrame(columns=indf.columns)
    for idx, row in indf.iterrows():
        # if type(row.geometry) == LineString:
        #     print('LINE!')
        if type(row.geometry) == Polygon:
            outdf = outdf.append(row, ignore_index=True)
        if type(row.geometry) == MultiPolygon:
            multdf = gp.GeoDataFrame(columns=indf.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row]*recs, ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom, 'geometry'] = row.geometry[geom]
            outdf = outdf.append(multdf, ignore_index=True)
        # else:
        #     print(type(row.geometry))
    return outdf

fid = '\\cyano_weekmap_20190717.shp'

crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

shapes = gp.read_file(fid)
crs = shapes.crs
crs[u'init'] = u'epsg:3006'
date = int(fid.split(u'_')[-1].replace(u'.shp', u''))

geometries = []
values = []
print('Looping...')

shapes_exp = explode(shapes)
print(shapes_exp.shape)

#TODO https://stackoverflow.com/questions/55176573/count-number-of-polygons-with-same-geometry-in-single-dataframe
# Kan vi göra en df_union = gpd.overlay(df_in, df_in, how='union') med weekmap ocj daymap som de två dataframesen?


# for n in range(1, 8):
#     print(n)
#     shapes_boolean = shapes[u'class'] == n
#     if not any(shapes_boolean):
#         continue
#     shapes_filter = shapes.loc[shapes_boolean]
#     shapes_filter[u'geometry'] = shapes_filter.buffer(0.1)
#     polys = []
#     for i, row in shapes_filter.iterrows():
#         polys.append(row[u'geometry'])
#
#     polyout = shapely.ops.unary_union(polys)
#     for p in polyout:
#         geometries.append(p)
#         values.append(n)
#
# shape_header = ['cloud', 'sub_surface', 'surface', 'no_data', 'class', 'color_hex']
# features = {key: values for key in shape_header}
# features = pd.DataFrame(features, columns=shape_header)
# geometry = [p for p in geometries]
# outpath = fid.replace(u'cyano_daymap', u'cyano_union_bloom')
# output = gp.GeoDataFrame(features, crs=crs, geometry=geometry)
# # output.to_file(driver=u'ESRI Shapefile', crs_wkt=crs_wkt,
# #                filename=outpath)
# dissolved = output.dissolve(by='class')
# # week_shp['geometry'] = week_shp.buffer(0.01)
# # print('dissolving...')
# # dissolved = week_shp.dissolve(by='class')
# # # dissolved = dissolved.to_crs(epsg=3006)
# # print('Done.. \n\nSaving..')
# # week_shp.to_file(driver='ESRI Shapefile', crs_wkt=crs_wkt,
# #                   filename="C:\\Temp\\shapes\\week_shp_weekmap.shp")
#
# polys = explode(shapes_filter)
#
# new_polys = []
# for p in polys['geometry']:
#     if not p.is_valid:
#         p = p.buffer(0.1)
#         if p.is_valid:
#             new_polys.append(p)
#     else:
#         new_polys.append(p)
#
# test = gp.GeoDataFrame({'class': [1]*len(new_polys)}, crs=crs, geometry=new_polys)
