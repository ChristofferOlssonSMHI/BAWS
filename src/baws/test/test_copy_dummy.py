# -*- coding: utf-8 -*-
"""
Created on 2019-07-23 12:23

@author: a002028

"""

# from PyQt4.QtCore import *
# import processing
#
#
# fids = []
# features = []
# for i, fid in enumerate(fids):
#     print('processing %s' % fid)
#     args = (fid, fid.split('\\')[-1], "ogr")
#     layer = QgsVectorLayer(fid, fid.split('\\')[-1], "ogr")
#     feats = []
#     for feat in layer.getFeatures():
#         if feat.geometry() is None:
#             continue
#         elif feat['class'] in [2, 3]:
#             feat['class'] = i + 1
#             feats.append(feat)
#
#     features.extend(feats)
#
# layer_spec = ("Polygon?crs=epsg:3006", 'Temporary', "memory")
# attributes = [QgsField(key, QVariant.Int) for key in ['cloud', 'sub_surface', 'surface', 'no_data', 'class']]
# attributes.append(QgsField("color_hex", QVariant.String))
#
# new_layer = QgsVectorLayer(*layer_spec)
# vpr = new_layer.dataProvider()
# vpr.addAttributes(attributes)
# new_layer.updateFields()
#
# vpr.addFeatures(features)
# new_layer.updateExtents()
# vpr.deleteAttributes([0, 1, 2, 3, 5])
# new_layer.updateFields()