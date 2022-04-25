# -*- coding: utf-8 -*-
"""
Created on 2019-07-22 15:54

@author: a002028

"""
import geopandas as gp
import pandas as pd
import shapely
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsField, QgsMapLayerRegistry
import processing
import time


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





# weekmap_path = 'C:\\Temp\\shapes\\weekmap_test.shp'
# weekmap_path = 'cyano_weekmap_20190716.shp'
# day_path = 'cyano_daymap_20190717.shp'
#
# fids = [weekmap_path, day_path]
#
# layer = QgsVectorLayer(weekmap_path, weekmap_path.split('\\')[-1], "ogr")
#
# features = []
# for feat in layer.getFeatures():
#     if feat.geometry() is None:
#         continue
#     elif feat['DATE_ID'] == '20190710':
#         continue
#     elif '20190710|' in feat['DATE_ID']:
#         feat['DATE_ID'] = feat['DATE_ID'].replace('20190710|', '')
#     elif '|20190710' in feat['DATE_ID']:
#         feat['DATE_ID'] = feat['DATE_ID'].replace('|20190710', '')
#     features.append(feat)



# layer = QgsVectorLayer(day_path, day_path.split('\\')[-1], "ogr")
#
# vpr = layer.dataProvider()
# vpr.addAttributes([QgsField('DATE_ID', QVariant.String)])
# layer.updateFields()
# attr_list = [a.name() for a in vpr.fields().toList()]
# delete_indices = [attr_list.index(attr) for attr in attr_list if not attr in ['class', 'DATE_ID']]
# vpr.deleteAttributes(delete_indices)
#
# layer.updateFields()
#
# date = [s for s in day_path.replace('.shp', '').split('\\')[-1].split('_') if s.isdigit()][0]
#
# values = {2: True, 3: True}
# for feat in layer.getFeatures():
#     if feat.geometry() is None:
#         continue
#     elif feat['class'] in values:
#         feat['DATE_ID'] = date
#         features.append(feat)
#
# layer_spec = ("Polygon?crs=epsg:3006", 'Temporary_weekmap_prod', "memory")
# attributes = [QgsField('class', QVariant.Int), QgsField('DATE_ID', QVariant.String)]
# new_layer = QgsVectorLayer(*layer_spec)
# vpr = new_layer.dataProvider()
# vpr.addAttributes(attributes)
# new_layer.updateFields()
# vpr.addFeatures(features)
# new_layer.updateExtents()
#
# QgsMapLayerRegistry.instance().addMapLayers([new_layer])

# #TODO Testa med cyano_union_bloom

# fids = ['cyano_union_bloom_20190718.shp',
#         'cyano_union_bloom_20190719.shp',
#         'cyano_union_bloom_20190720.shp',
#         'cyano_union_bloom_20190721.shp',
#         'cyano_union_bloom_20190722.shp',
#         'cyano_union_bloom_20190723.shp',
#         'cyano_union_bloom_20190724.shp']
#
# crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'
#
# values = {2: True, 3: True}
#
# features = []
# print('Number of files for composite map: %i' % len(fids))
# for i, fid in enumerate(fids):
#     print('processing %s' % fid)
#     layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
#     vpr = layer.dataProvider()
#     vpr.addAttributes([QgsField('DATE_ID', QVariant.String)])
#     layer.updateFields()
#     attr_list = [a.name() for a in vpr.fields().toList()]
#     delete_indices = [attr_list.index(attr) for attr in attr_list if not attr in ['class', 'DATE_ID']]
#     vpr.deleteAttributes(delete_indices)
#     layer.updateFields()
#
#     date = [s for s in fid.replace('.shp', '').split('\\')[-1].split('_') if s.isdigit()][0]
#     feats = []
#     for feat in layer.getFeatures():
#         if feat.geometry() is None:
#             continue
#         elif feat['class'] in values:
#             feat['DATE_ID'] = date
#             feats.append(feat)
#     features.extend(feats)
#
# layer_spec = ("Polygon?crs=epsg:3006", 'Temporary_weekmap_prod', "memory")
# attributes = [QgsField(key, QVariant.Int) for key in ['class']]
# attributes.extend([QgsField(key, QVariant.String) for key in ['DATE_ID']])
# new_layer = QgsVectorLayer(*layer_spec)
# vpr = new_layer.dataProvider()
# vpr.addAttributes(attributes)
# new_layer.updateFields()
#
# vpr.addFeatures(features)
# new_layer.updateExtents()
# # vpr.deleteAttributes([0, 1, 2, 3, 5])
# new_layer.updateFields()
#
# QgsMapLayerRegistry.instance().addMapLayers([new_layer])
#
# start_time = time.time()
# args = ('saga:polygonselfintersection', new_layer, 'DATE_ID', 'Intersection.shp')
# processing.runandload(*args)
# print("Intersection session completed in --%.3f sec\n" % (time.time() - start_time))
# # layers = [layer for layer in iface.mapCanvas().layers()]
# # for lay in layers:
# #     if 'Intersection' in lay.name():
# #         layer = lay
#
# layer.startEditing()
# for feat in layer.getFeatures():
#     if not feat['ID'] or feat.geometry() is None:
#         layer.deleteFeature(feat.id())
#         continue
#
#     if '|' in feat['ID']:
#         value = len(set(feat['ID'].split('|')))
#     # elif feat['class'] == '0':
#     #     # In case of no features, an empty shapefile has been activated with a dummy class value of 0
#     #     value = 0
#     else:
#         value = 1
#     feat['class'] = value
#     feat['DATE_ID'] = feat['ID']
#     layer.changeAttributeValue(feat.id(), 0, value)
#     layer.updateFeature(feat)
#
# layer.commitChanges()
#
# layer.dataProvider().deleteAttributes([2])  # Delete attribute "ID"
# layer.updateFields()





# layers = [layer for layer in iface.mapCanvas().layers()]
# for layer in layers:
#     if 'weekmap' in layer.name():
#         weekmap = layer
#     else:
#         daymap = layer
#
# features = []
# for feat in daymap.getFeatures():
#     if feat.geometry() is None:
#         continue
#     elif feat['class'] == 2 or feat['class'] == 3:
#         feat['class'] = 1
#         features.append(feat)
#
# for feat in weekmap.getFeatures():
#     if feat.geometry() is None:
#         continue
#     if feat['ID'] == 1:
#         continue
#     elif feat['class'] == 2 or feat['class'] == 3:
#         feat['class'] = 1
#         features.append(feat)
"""
from PyQt4.QtCore import *
import processing
import time

features = []
for i, fid in enumerate(fids):
    print('processing %s' % fid)
    args = (fid, fid.split('\\')[-1], "ogr")
    layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
    vpr = layer.dataProvider()
    attr_list = [a.name() for a in vpr.fields().toList()]
    delete_indices = [attr_list.index(attr) for attr in attr_list if not attr in ['class']]
    vpr.deleteAttributes(delete_indices)
    layer.updateFields()

    feats = []
    for feat in layer.getFeatures():
        if feat.geometry() is None:
            continue
        elif feat['class'] in [2, 3]:
            feat['class'] = i + 1
            feats.append(feat)

    features.extend(feats)

layer_spec = ("Polygon?crs=epsg:3006", 'Temporary', "memory")
attributes = [QgsField('class', QVariant.Int)]

new_layer = QgsVectorLayer(*layer_spec)
vpr = new_layer.dataProvider()
vpr.addAttributes(attributes)
new_layer.updateFields()

vpr.addFeatures(features)
new_layer.updateExtents()
new_layer.updateFields()

QgsMapLayerRegistry.instance().addMapLayers([new_layer])

print('Intersecting..')
start_time = time.time()
args = ('saga:polygonselfintersection', new_layer, 'class', 'Intersection.shp')
processing.runandload(*args)
print("Intersection session completed in --%.3f sec\n" % (time.time() - start_time))



"""







"""
UNION

from PyQt4.QtCore import *
import processing
import time

crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

values = {2: True, 3: True}

features = []
print('Number of files for composite map: %i' % len(fids))
for i, fid in enumerate(fids):
    print('processing %s' % fid)
    layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")

    feats = []
    for feat in layer.getFeatures():
        if feat.geometry() is None:
            continue
        elif feat['class'] in values:
            feat['class'] = i+1
            feats.append(feat)
    features.extend(feats)

layer_spec = ("Polygon?crs=epsg:3006", 'Temporary_weekmap_prod', "memory")
attributes = [QgsField(key, QVariant.Int) for key in ['class']]
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
args = ('saga:polygonselfintersection', new_layer, 'class', 'Intersection.shp')
processing.runandload(*args)
print("Intersection session completed in --%.3f sec\n" % (time.time() - start_time))
layers = [layer for layer in iface.mapCanvas().layers()]
for lay in layers:
    if 'Intersection' in lay.name():
        layer = lay

layer.startEditing()
for feat in layer.getFeatures():
    if not feat['ID'] or feat.geometry() is None:
        layer.deleteFeature(feat.id())
        continue

    if '|' in feat['ID']:
        value = len(set(feat['ID'].split('|')))
    # elif feat['class'] == '0':
    #     # In case of no features, an empty shapefile has been activated with a dummy class value of 0
    #     value = 0
    else:
        value = 1
    feat['class'] = value
    layer.changeAttributeValue(feat.id(), 0, value)
    layer.updateFeature(feat)

layer.commitChanges()

#layer.dataProvider().deleteAttributes([2])  # Delete attribute "ID"
layer.updateFields()



"""

"""
STEP intersection divide days during week in 2 parts


from PyQt4.QtCore import *
import processing
import time


outpath = 'C:\\Temp\\shapes\\week_a_20190725.shp'

crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

values = {2: True, 3: True}

features = []
print('Number of files for composite map: %i' % len(fids))
for i, fid in enumerate(fids):
    print('processing %s' % fid)
    layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
    vpr = layer.dataProvider()
    vpr.addAttributes([QgsField('DATE_ID', QVariant.String)])
    layer.updateFields()
    attr_list = [a.name() for a in vpr.fields().toList()]
    delete_indices = [attr_list.index(attr) for attr in attr_list if not attr in ['class', 'DATE_ID']]
    vpr.deleteAttributes(delete_indices)
    layer.updateFields()

    date = [s for s in fid.replace('.shp', '').split('\\')[-1].split('_') if s.isdigit()][0]
    feats = []
    for feat in layer.getFeatures():
        if feat.geometry() is None:
            continue
        elif feat['class'] in values:
            feat['DATE_ID'] = date
            feats.append(feat)
    features.extend(feats)

layer_spec = ("Polygon?crs=epsg:3006", 'Temporary_weekmap_prod', "memory")
attributes = [QgsField(key, QVariant.Int) for key in ['class']]
attributes.extend([QgsField(key, QVariant.String) for key in ['DATE_ID']])
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
args = ('saga:polygonselfintersection', new_layer, 'DATE_ID', 'Intersection.shp')
processing.runandload(*args)
print("Intersection session completed in --%.3f sec\n" % (time.time() - start_time))
layers = [layer for layer in iface.mapCanvas().layers()]
for lay in layers:
    if 'Intersection' in lay.name():
        layer = lay

layer.startEditing()
for feat in layer.getFeatures():
    if not feat['ID'] or feat.geometry() is None:
        layer.deleteFeature(feat.id())
        continue

    if '|' in feat['ID']:
        value = len(set(feat['ID'].split('|')))
    # elif feat['class'] == '0':
    #     # In case of no features, an empty shapefile has been activated with a dummy class value of 0
    #     value = 0
    else:
        value = 1
    feat['class'] = value
    feat['DATE_ID'] = feat['ID']
    layer.changeAttributeValue(feat.id(), 0, value)
    layer.updateFeature(feat)

layer.commitChanges()

layer.dataProvider().deleteAttributes([2])  # Delete attribute "ID"
layer.updateFields()

args = (layer, outpath, "utf-8", None, "ESRI Shapefile")
QgsVectorFileWriter.writeAsVectorFormat(*args)

 



"""


"""
SAVE LAYER

args = (layer, path, "utf-8", None, "ESRI Shapefile")
QgsVectorFileWriter.writeAsVectorFormat(*args)


"""


"""
from PyQt4.QtCore import *
import processing
import time


fids = ['C:\\Temp\\shapes\\week_union_a_20180725.shp',
           'C:\\Temp\\shapes\\week_union_b_20180725.shp']

crs_wkt = u'PROJCS["SWEREF99_TM",GEOGCS["GCS_SWEREF99",DATUM["D_SWEREF99",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

values = {2: True, 3: True}

features = []
print('Number of files for composite map: %i' % len(fids))
for i, fid in enumerate(fids):
    print('processing %s' % fid)
    layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
    vpr = layer.dataProvider()
    vpr.addAttributes([QgsField('class_id', QVariant.String)])
    layer.updateFields()
    
    idx_id = layer.name().index('_20180725.shp') -1
    layer_id = layer.name()[idx_id]
    
    feats = []
    for feat in layer.getFeatures():
        if feat.geometry() is None:
            continue
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
args = ('saga:polygonselfintersection', new_layer, 'class_id', 'Intersection.shp')
processing.runandload(*args)
print("Intersection session completed in --%.3f sec\n" % (time.time() - start_time))
layers = [layer for layer in iface.mapCanvas().layers()]
for lay in layers:
    if 'Intersection' in lay.name():
        layer = lay

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
        value = a+b
    # elif feat['class'] == '0':
    #     # In case of no features, an empty shapefile has been activated with a dummy class value of 0
    #     value = 0
    else:
        value = feat['class']
    feat['class'] = value
    layer.changeAttributeValue(feat.id(), 0, value)
    layer.updateFeature(feat)

layer.commitChanges()

layer.dataProvider().deleteAttributes([2])  # Delete attribute "ID"
layer.updateFields()

path = 'C:\\Temp\\shapes\\weekmap_test_20190725.shp'
args = (layer, path, "utf-8", None, "ESRI Shapefile")
QgsVectorFileWriter.writeAsVectorFormat(*args)


"""
