# -*- coding: utf-8 -*-
"""
Created on 2019-06-24 16:30

@author: a002028

"""
import os


def create_stw(coordframe, cyano_file_path, file_tag,
               reader,
               QgsPoint, QgsField, QgsFeature, QgsGeometry, QVariant):

    def save_empty_file(save_path):
        with open(save_path, 'w') as file:
            file.write('no_stw')
        file.close()
    out_folder = os.path.dirname(os.path.realpath(cyano_file_path))
    stw_file_path = os.path.join(out_folder, '_'.join(['stw', file_tag]) + '.txt')

    args = (cyano_file_path, os.path.basename(cyano_file_path), "ogr")
    layer = reader('qgis', *args)
    selected_features = [feat for feat in layer.getFeatures() if feat['class'] in [3]]
    if len(selected_features) == 0:
        save_empty_file(stw_file_path)
        return

    PointList = []
    for index, row in coordframe.iterrows():
        sweref_point = QgsPoint(row['lon_sweref'], row['lat_sweref'])
        PointList.append(sweref_point)

    attr = ("Point?crs=epsg:3006", "baws_points", "memory")
    coordlayer = reader('qgis', *attr)
    vpr = coordlayer.dataProvider()
    attributes = [QgsField('b_points', QVariant.Int)]
    vpr.addAttributes(attributes)
    coordlayer.updateFields()

    coordlayer.startEditing()
    features = []
    for p in PointList:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(p))
        feature.setAttributes([1])
        features.append(feature)

    vpr.addFeatures(features)
    coordlayer.commitChanges()

    indices = {}
    for feat in selected_features:
        if feat.geometry() is None:
            continue
        poly = feat.geometry()
        for i, coord_feat in enumerate(coordlayer.getFeatures()):
            if i not in indices:
                coord_geom = coord_feat.geometry()
                if poly.contains(coord_geom) or poly.touches(coord_geom):
                    indices[i] = True
    if len(list(indices.keys())) > 5:
        coordframe.loc[list(indices.keys()), ['lat_wgs84', 'lon_wgs84']].to_csv(
            stw_file_path,
            sep='\t',
            header=None,
            index=False,
            encoding='cp1252'
        )
    else:
        save_empty_file(stw_file_path)
