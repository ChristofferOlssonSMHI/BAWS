# -*- coding: utf-8 -*-
"""
Created on 2019-07-24 15:22

@author: a002028

"""
from __future__ import print_function
from builtins import range
import re
import shapely
from shapely.wkt import loads
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import geopandas as gp
import pandas as pd


def explode(indf):
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


# simpledec = re.compile(r"\d*\.\d+")
#
# fid = 'C:/Temp/shapes/week_b_20190725.shp'
# shapes = gp.read_file(fid)
# crs = shapes.crs
# crs[u'init'] = u'epsg:3006'
# crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'
#
# print('Exploding..')
# shapes = explode(shapes)
# print('Exploding Done!')
#
# shapes[u'geometry'] = shapes.buffer(0.1)
#
# print('Looping..')
# classes = []
# geoms = []
#
# #TODO vi kan inte göra en union och sedan ta bort dag 1.. den informationen är borta då..
#
# for cls in shapes['class'].unique():
#     # fix_print_with_import
#     print(('Class:', cls))
#     boolean_equals = shapes['class'] == cls
#     shapes_filter = shapes.loc[boolean_equals]
#     polys = shapes_filter[u'geometry'].tolist()
#     # fix_print_with_import
#     # fix_print_with_import
# print(('len(polys)', len(polys)))
#     polyout = shapely.ops.unary_union(polys)
#     # fix_print_with_import
#     # fix_print_with_import
# print(('len(polyout)', len(polyout)))
#     classes.extend([cls] * len(polyout))
#     geoms.extend([p for p in polyout])
#
#     # shape_header = ['cloud', 'sub_surface', 'surface', 'no_data', 'class', 'color_hex']
# shape_header = ['class']
# features = {'class': classes}
# features = pd.DataFrame(features, columns=shape_header)
# outpath = fid.replace(u'week', u'week_union')
# output = gp.GeoDataFrame(features, crs=crs, geometry=[p for p in geoms])
# print('rounding coords..')
# output.geometry = output.geometry.apply(lambda x: loads(re.sub(simpledec, mround, x.wkt)))
# print('rounding completed')
# output.to_file(driver=u'ESRI Shapefile', crs_wkt=crs_wkt, filename=outpath)



    # if any(boolean_larger):
    #     print('Filtering out polys within..')
    #     print(shapes_filter.shape)
    #     shapes_larger = shapes.loc[boolean_larger]
    #     selected = []
    #     for i, poly in enumerate(shapes_filter['geometry']):
    #         print(i)
    #         if poly.is_valid:
    #             for higher_poly in shapes_larger['geometry']:
    #                 if higher_poly.is_valid:
    #                     if higher_poly.contains(poly):
    #                         selected.append(i)
    # break




# delete_date = '20190713'
# delete_indices = []
# for i, row in shapes.iterrows():
#     # '20190713|20190713' should not be possible due to earlier steps
#     if row['DATE_ID'] == delete_date:
#         delete_indices.append(i)
#         continue
#     if delete_date+'|' in row['DATE_ID']:
#         row['DATE_ID'] = row['DATE_ID'].replace(delete_date+'|', '')
#     if '|'+delete_date in row['DATE_ID']:
#         row['DATE_ID'] = row['DATE_ID'].replace('|'+delete_date, '')
#     if delete_date in row['DATE_ID']:
#         row['DATE_ID'] = row['DATE_ID'].replace(delete_date, '')
#     if row['DATE_ID'].startswith('|') or row['DATE_ID'].endswith('|'):
#         not_breaking = True
#         while not_breaking:
#             if row['DATE_ID'].startswith('|'):
#                 row['DATE_ID'] = row['DATE_ID'][1:]
#             elif row['DATE_ID'].endswith('|'):
#                 row['DATE_ID'] = row['DATE_ID'][:-1]
#             else:
#                 not_breaking = False
#     not_breaking = True
#     while not_breaking:
#         if '||' in row['DATE_ID']:
#             row['DATE_ID'] = row['DATE_ID'].replace('||', '|')
#         else:
#             not_breaking = False
#
# print('Deleting nr of rows:', len(delete_indices))
# shapes = shapes.drop(delete_indices)
# shapes = shapes.reset_index()


"""

from PyQt4.QtCore import *
import processing
import time

file_set = ['C:\\Users\\\\baws_temp\\week_a_20190801.shp',
                'C:\\Users\\\\baws_temp\\week_b_20190801.shp']

print('Process: intersect_weekly_file_set..')
features = []
for i, fid in enumerate(file_set):
    print('processing %s' % fid)
    layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
    vpr = layer.dataProvider()
    idx_list = [a.name() for a in layer.dataProvider().fields().toList()]
    clas_idx = idx_list.index('class')
    idx_list = range(len(idx_list))
    idx_list.pop(clas_idx)
    vpr.deleteAttributes(idx_list)
    layer.updateFields()
    vpr.addAttributes([QgsField('class_id', QVariant.String)])
    layer.updateFields()

    suffix = '_'+'20190801'+'.shp'
    idx_id = layer.name().index(suffix) - 1
    layer_id = layer.name()[idx_id]
    print('layer_id:', layer_id)
    feats = []
    for feat in layer.getFeatures():
        if feat.geometry() is None:
            continue
#        print(feat['class'])
#        print('_'.join([str(feat['class']), layer_id]))
        feat['class_id'] = '_'.join([str(feat['class']), layer_id])

        feats.append(feat)
    features.extend(feats)

layer_spec = ("Polygon?crs=epsg:3006", 'Temporary_weekmap_prod', "memory")
attributes = [QgsField(key, QVariant.Int) for key in ['class']]
attributes.extend([QgsField(key, QVariant.String) for key in ['class_id']])
new_layer = QgsVectorLayer(*layer_spec)
vpr = new_layer.dataProvider()
vpr.addAttributes(attributes)
new_layer.updateFields()

vpr.addFeatures(features)
new_layer.updateExtents()
# vpr.deleteAttributes([0, 1, 2, 3, 5])
new_layer.updateFields()

QgsMapLayerRegistry.instance().addMapLayers([new_layer])

start_time = time.time()

args = ('saga:polygonselfintersection', new_layer, 'class_id',
             'C:\\Users\\\\baws_temp\\intersected_20190801.shp')
processing.runandload(*args)

print("Intersection session completed in --%.1f sec\n" % (time.time() - start_time))


"""

"""
from PyQt4.QtCore import *
import processing
import time

file_set = ['C:\\Users\\\\baws_temp\\week_a_20190801.shp',
                'C:\\Users\\\\baws_temp\\week_b_20190801.shp']

layer = [layer for layer in iface.mapCanvas().layers()][0]

start_time = time.time()

layer.startEditing()
for feat in layer.getFeatures():
    if not feat['ID'] or feat.geometry() is None:
        layer.deleteFeature(feat.id())
        continue

    if '|' in feat['ID']:
        multi_cls = feat['ID'].split('|')
        a = 0
        b = 0
        for c in multi_cls:
            if 'a' in c:
                if int(c[0]) > a:
                    a = int(c[0])
            if 'b' in c:
                if int(c[0]) > b:
                    b = int(c[0])
        value = a + b
    else:
        value = feat['class']
    feat['class'] = value
    layer.changeAttributeValue(feat.id(), 0, value)
    layer.updateFeature(feat)

layer.commitChanges()

layer.dataProvider().deleteAttributes([2])  # Delete attribute "ID"
layer.updateFields()

print("Intersection session completed in --%.1f sec\n" % (time.time() - start_time))


"""