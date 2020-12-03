# -*- coding: utf-8 -*-
"""
Created on 2019-07-24 11:22

@author: a002028

"""
from __future__ import print_function
import geopandas as gp
from shapely.wkt import loads
import re


simpledec = re.compile(r"\d*\.\d+")
def mround(match):
    return "{:.0f}".format(float(match.group()))


fids = [
    'cyano_daymap_20190717.shp'
]

for fid in fids:
    fid = fid.replace('union_bloom', 'daymap')
    print(fid)
    shapes = gp.read_file(fid)
    shapes.geometry = shapes.geometry.apply(lambda x: loads(re.sub(simpledec, mround, x.wkt)))
    shapes.to_file(fid)


# def change_coord(tup):
#     return QgsPoint(int(tup[0]), int(tup[1]))
#
#
# def convert_polygon_type(geom):
#     new_points = []
#     if geom.wkbType() == QgsWKBTypes.Polygon:
#         polys = geom.asPolygon()
#         for p in polys:
#             if isinstance(p, QgsPoint):
#                 point = change_coord(p)
#                 new_points.append(point)
#             elif isinstance(p, list):
#                 for pp in p:
#                     if isinstance(pp, QgsPoint):
#                         point = change_coord(pp)
#                         new_points.append(point)
#     else:
#         print('Not a polygon!', geom.wkbType())
#     return new_points
