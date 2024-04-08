# -*- coding: utf-8 -*-
"""
Created on 2019-05-22 12:33

@author: a002028
"""
import pickle
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.cbook as cbook

from mpl_toolkits.basemap import Basemap


def get_basemap(map_axes):
    """Return standard map object.

    We use these map settings. However,
    this function is not used in the system, instead we load a pickle file.
    """
    m = Basemap(
        resolution='i', projection='laea', ellps='bessel',
        width=1400000, height=1400000,
        lon_0=14., lat_1=60., lat_2=60., lat_0=60,
        llcrnrlon=6.8118748038970524,
        llcrnrlat=53.336819380313962,
        urcrnrlon=33.813214510263896,
        urcrnrlat=64.892858589601166,
        area_thresh=5,
        ax=map_axes
    )
    m.drawcoastlines(linewidth=0.2, zorder=3)
    m.fillcontinents(color='#E4F4E7', lake_color='#E4F4E7', zorder=3)
    m.drawmapboundary(fill_color='white', zorder=3)
    return m


class MapHandler:
    """"""

    def __init__(self, path_figure=None, path_basemap=None):
        """Initialize.

        self.map_obj is used to transform polygon coordinates to the
        map projection.
        """
        self.path_figure = path_figure
        with open(path_basemap, 'rb') as f:
            self.map_obj = pickle.load(f)
        self.week_map = None
        self.week_axes = None
        self.week_figure = None
        self.day_map = None
        self.day_axes = None
        self.day_figure = None

        self.day_colormap_properties = {
            0: '#000000',  # dummy color
            1: '#7a7a7a',
            2: '#ffff00',
            3: '#ff9900',
            4: '#000000'
        }

        self.week_colormap_properties = {
            0: '#000000',  # dummy color
            1: '#0066ff',
            2: '#00ccff',
            3: '#99e2ff',
            4: '#ffff33',
            5: '#ff9933',
            6: '#ff3300',
            7: '#990000'
        }

    def initialize_maps(self):
        """Initiate maps.

        Takes around 15 seconds per map,
        hence the threading might be a good idea.
        """
        with open(self.path_figure, 'rb') as openfile:
            self.day_figure = pickle.load(openfile)
        self.day_axes = self.day_figure.axes[0]

        with open(self.path_figure, 'rb') as openfile:
            self.week_figure = pickle.load(openfile)
        self.week_axes = self.week_figure.axes[0]

    @staticmethod
    def add_picture_to_figure(figure, path_picture='',
                              axes_settings=None):
        """Add logo and legend."""
        axes_settings = axes_settings or [0, 1, 2, 3]
        img = plt.imread(cbook.get_sample_data(path_picture))
        new_ax = figure.add_axes(axes_settings, zorder=3)
        new_ax.imshow(img)

        if 'smhi-logo' in path_picture:
            labels = [item.get_text() for item in new_ax.get_xticklabels()]
            labels[3] = '1'
            new_ax.set_xticklabels(labels)

        elif 'legend' in path_picture:
            new_ax.tick_params(axis="x", direction="in", pad=-22)
            new_ax.tick_params(axis="y", direction="in", pad=-22)

        new_ax.axis('off')

    @staticmethod
    def plot_patches(patches, map_axes=None):
        """Add color patches to map."""
        if any(patches):
            map_axes.add_collection(
                PatchCollection(patches, match_original=True)
            )

    @staticmethod
    def save_figure(path, figure):
        """Save figure.

        The pickle file used to load this figure
        already has the following settings:
        figure.tight_layout()
        figure.subplots_adjust(
            top=0.999,
            bottom=0.001,
            right=0.999,
            left=0.001
        )
        """
        figure.savefig(path, dpi=287)
