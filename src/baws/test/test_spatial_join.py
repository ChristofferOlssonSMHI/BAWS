# -*- coding: utf-8 -*-
"""
Created on 2019-07-29 08:18

@author: a002028

"""
import time
import geopandas as gp
import matplotlib.pyplot as plt
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon


def explode(indf):
    print('Explode..')
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


path = 'C:\\Temp\\shapes\\'

fid1 = 'cyano_daymap_20190727.shp'
fid2 = 'cyano_daymap_20190728.shp'

gf1 = gp.read_file(path+fid1)
gf2 = gp.read_file(path+fid2)

gf1.drop([u'cloud', u'sub_surfac', u'surface', u'no_data', u'color_hex'], axis=1, inplace=True)
gf2.drop([u'cloud', u'sub_surfac', u'surface', u'no_data', u'color_hex'], axis=1, inplace=True)

values = [2, 3]

boolean1 = gf1['class'].isin(values)
boolean2 = gf2['class'].isin(values)

filter_shapes_1 = gf1.loc[boolean1]
filter_shapes_2 = gf2.loc[boolean2]

print('Buffering...')
filter_shapes_1[u'geometry'] = filter_shapes_1.buffer(0.1)
filter_shapes_2[u'geometry'] = filter_shapes_2.buffer(0.1)

filter_shapes_1 = explode(filter_shapes_1)
filter_shapes_2 = explode(filter_shapes_2)

filter_shapes_1.loc[:, ['class']] = 1
filter_shapes_2.loc[:, ['class']] = 2

start_time = time.time()
# spatial_join = gp.sjoin(filter_shapes_1, filter_shapes_2, how="inner", op='intersects')
# index_list = spatial_join.index
print('gp.overlay, intersection...')
spatial_join = gp.overlay(filter_shapes_1, filter_shapes_2, how='intersection')

print("overlay session completed in --%.3f sec\n" % (time.time() - start_time))

start_time = time.time()
print('gp.overlay, symmetric_difference...')
res_symdiff = gp.overlay(filter_shapes_1, filter_shapes_2, how='symmetric_difference')
print("symmetric_difference session completed in --%.3f sec\n" % (time.time() - start_time))

# spatial_join.plot()

# for i, row in spatial_join.iterrows():
#     if not row['class_left'] == 1 or not row['class_right'] == 2:
#         print(row[['class_left', 'class_right']])






