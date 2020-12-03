# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:33

@author: a002028

"""
from __future__ import print_function
from builtins import object
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.cbook as cbook

from mpl_toolkits.basemap import Basemap


class BaseMapping(object):
    """
    """
    def __init__(self):
        super(BaseMapping, self).__init__()
        self._cmap = None

    @property
    def colormap_properties(self):
        return self._cmap

    @colormap_properties.setter
    def colormap_properties(self, mapping):
        if mapping:
            self._cmap = mapping
        else:
            self._cmap = {0: '#000000',
                          1: '#7a7a7a',
                          2: '#Ffff00',
                          3: '#Ff9900',
                          4: '#000000'}


class MapHandler(BaseMapping):
    """
    """
    def __init__(self, source=None, source_path=None, colormap_properties=None):
        super(MapHandler, self).__init__()
        self.source_path = source_path

        if colormap_properties is None:
            try:
                self.colormap_properties = self._set_cmap_porperties(source_path)
            except:
                self.colormap_properties = colormap_properties
        else:
            self.colormap_properties = colormap_properties

    def initialize_map(self):
        """
        Initiate map according to old configurations.
        :return:
        """
        self.map_figure = plt.figure(figsize=(4.84251968503937, 4.84251968503937))
        self.map_axes = self.map_figure.add_subplot(111)

        self.map = Basemap(resolution='i', projection='laea', ellps='bessel',
                           width=1400000, height=1400000,
                           lon_0=14., lat_1=60., lat_2=60., lat_0=60,
                           llcrnrlon=6.8869748038970524, llcrnrlat=53.330819380313962,
                           urcrnrlon=33.733114510263896, urcrnrlat=64.902858589601166,
                           area_thresh=500,
                           ax=self.map_axes)

        self.map.drawcoastlines(linewidth=0.2)
        self.map.fillcontinents(color='#E4F4E7', lake_color='white')
        self.map.drawmapboundary(fill_color='white')

    def add_picture_to_figure(self, path_picture='', axes_settings=[]):
        """
        :param path_picture:
        :return:
        """
        if not any(axes_settings):
            axes_settings = [0, 1, 2, 3]
        img = plt.imread(cbook.get_sample_data(path_picture))  #
        new_ax = self.map_figure.add_axes(axes_settings, zorder=3)
        new_ax.imshow(img)

        if 'smhi-logo' in path_picture:
            labels = [item.get_text() for item in new_ax.get_xticklabels()]
            labels[3] = '1'
            new_ax.set_xticklabels(labels)

        elif 'legend' in path_picture:
            new_ax.tick_params(axis="x", direction="in", pad=-22)
            new_ax.tick_params(axis="y", direction="in", pad=-22)

        new_ax.axis('off')

    def plot_patches(self, patches, map_axes=None):
        """
        :return:
        """
        if any(patches):
            map_axes.add_collection(PatchCollection(patches, match_original=True))

    def _set_map_porperties(self, path_prop):
        """
        :param unique_raster_values:
        :return:
        """
        raise NotImplementedError

    def save_figure(self, path, **kwargs):
        """
        kwargs = {bbox_inches='tight', dpi=312, pad_inches=-0.003}
        :return:
        """
        plt.tight_layout()
        plt.savefig(path, **kwargs)
