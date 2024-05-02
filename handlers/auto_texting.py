#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-07-08 16:40

@author: johannes
"""
import rasterio as rio
import numpy as np


def get_area_name_string_list(areas, lang='swe'):
    """Doc."""
    and_sign = 'och' if lang == 'swe' else 'and'
    if len(areas) == 1:
        return areas[0]
    elif len(areas) == 2:
        return f' {and_sign} '.join(areas)
    else:
        suf = ', '.join(areas[:-1])
        return f'{suf} {and_sign} {areas[-1]}'


def get_area_names(area_list, mapper=None, lang=None):
    """Doc."""
    if not area_list:
        return area_list
    name_list = []
    combo_str = '-'.join(map(str, area_list))
    for ck, item in mapper['combo_mapper'].items():
        if ck in combo_str:
            name_list.append(item.get(lang))
            combo_str = combo_str.replace(ck, '').strip('-')
            area_list = [v for v in area_list if v not in item['id_set']]
    for v in area_list:
        name_list.append(mapper['name_mapper'][str(v)].get(lang))
    return name_list


def get_cloud_area_names(area_list, mapper=None, lang=None):
    """Doc."""
    if not area_list:
        return area_list
    name_list = []
    combo_str = '-'.join(map(str, area_list))
    for ck, item in mapper['cloud_combo_mapper'].items():
        if ck in combo_str:
            name_list.append(item.get(lang))
            combo_str = combo_str.replace(ck, '').strip('-')
    return name_list


def get_week_bloom_area_lists(maxes, lang=None, mapper=None):
    """Doc."""
    few = []
    multi = []
    for i in mapper['name_mapper']['id_order']:
        v = maxes.get(i)
        if not v:
            continue
        elif v < 4:
            few.append(i)
        elif v > 3:
            multi.append(i)

    few = get_area_names(few, mapper=mapper, lang=lang)
    multi = get_area_names(multi, mapper=mapper, lang=lang)

    return few, multi


def get_day_bloom_area_lists(maxes, lang=None, mapper=None):
    """Doc."""
    surfs = []
    subs = []
    for i in mapper['name_mapper']['id_order']:
        v = maxes.get(i)
        if not v:
            continue
        elif v == 3:
            surfs.append(i)
        elif v == 2:
            subs.append(i)
    surfs = get_area_names(surfs, mapper=mapper, lang=lang)
    subs = get_area_names(subs, mapper=mapper, lang=lang)
    return surfs, subs


def open_raster(fid):
    """Doc."""
    rst = rio.open(fid)
    _array = rst.read()
    return _array[0]


class WeekTexting:
    """Doc."""
    swe_text = 'Sammanställning av de 7 senaste dagarna ({START_DATE} - ' \
               '{END_DATE}): {TEXT} Utfärdat av: {USER_NAME}'
    eng_text = 'Compilation of the last 7 days ({START_DATE} - ' \
               '{END_DATE}): {TEXT} Written by: {USER_NAME}'

    def __init__(self, path_to_districts, *args, user=None, text_mapper=None,
                 end_date=None, start_date=None, weekmap_path=None, **kwargs):
        self.mapper = text_mapper
        self.districts = open_raster(path_to_districts)
        self.user = user
        self.tiff_path = weekmap_path
        self.end_date = end_date
        self.start_date = start_date

    def get_text(self, lang=None):
        """Doc."""
        data = open_raster(self.tiff_path)
        week_text = self.generate_descriptive_text(data, lang=lang)
        text_place_holder = self.eng_text if lang == 'eng' else self.swe_text
        return text_place_holder.format(
            START_DATE=self.start_date,
            END_DATE=self.end_date,
            TEXT=week_text,
            USER_NAME=self.user
        )

    def generate_descriptive_text(self, data, *args, lang=None, **kwargs):
        """Doc."""
        not_zero = np.logical_and(data != 0, self.districts != 0)
        maxes = {}
        for area in np.unique(self.districts[not_zero]):
            area_boolean = np.logical_and(not_zero, self.districts == area)
            maxes.setdefault(area, data[area_boolean].max())

        few, multi = get_week_bloom_area_lists(maxes, lang=lang,
                                               mapper=self.mapper)

        if any(few) and any(multi):
            return self.mapper['week_text_mapper']['diverse'][lang].format(
                AREA_LIST_FEW=get_area_name_string_list(few, lang=lang),
                AREA_LIST_MULTI=get_area_name_string_list(multi, lang=lang),
            )
        elif any(few):
            return self.mapper['week_text_mapper']['few'][lang].format(
                AREA_LIST_FEW=get_area_name_string_list(few, lang=lang),
            )
        elif any(multi):
            return self.mapper['week_text_mapper']['multi'][lang].format(
                AREA_LIST_MULTI=get_area_name_string_list(multi, lang=lang),
            )
        else:
            return self.mapper['week_text_mapper']['zero'].get(lang)


class DayTexting:
    """Doc."""
    swe_text = 'Blomningen i Östersjön: {WEATHER} {TEXT} ' \
               'Utfärdat av: {USER_NAME}'
    eng_text = 'The bloom situation in the Baltic Sea: {WEATHER} {TEXT} ' \
               'Written by: {USER_NAME}'

    def __init__(self, path_to_districts, *args,
                 user=None, text_mapper=None, daymap_path=None, **kwargs):
        self.mapper = text_mapper
        self.districts = open_raster(path_to_districts)
        self.user = user
        self.tiff_path = daymap_path
        self.district_sizes = {i: np.count_nonzero(self.districts == i)
                               for i in range(1, self.districts.max() + 1)}

        self.group_district_sizes = {
            '-'.join(map(str, group)): np.count_nonzero(
                np.isin(self.districts, group))
            for group in [[4, 5, 6], [7, 8], [9], [12, 13]]
        }

    def get_text(self, lang=None):
        """Doc."""
        data = open_raster(self.tiff_path)
        weather_text = self.generate_weather_text(data, lang=lang)
        bloom_text = self.generate_bloom_text(data, lang=lang)
        text_place_holder = self.eng_text if lang == 'eng' else self.swe_text
        return text_place_holder.format(
            WEATHER=weather_text,
            TEXT=bloom_text,
            USER_NAME=self.user
        )

    def generate_weather_text(self, data, *args, lang=None, **kwargs):
        """Doc."""
        clouds = data == 1
        sizes = {}
        for group, area in self.group_district_sizes.items():
            group_list = [int(v) for v in group.split('-')]
            size = np.count_nonzero(
                np.logical_and(clouds, np.isin(self.districts, group_list)))
            sizes.setdefault(group, round(float(size) / area, 2))

        text_list = []
        for ratio_range, item in self.mapper['cloud_ratio_description'].items():
            ratio_min, ratio_max = map(float, ratio_range.split('-'))
            area_list = [
                g for g, r in sizes.items() if ratio_min <= r < ratio_max]

            if not area_list:
                continue
            area_name_list = get_cloud_area_names(
                area_list, mapper=self.mapper, lang=lang
            )
            area_name_str = get_area_name_string_list(area_name_list, lang=lang)
            names = ' '.join([item.get(lang), area_name_str]) + '.'
            text_list.append(names)
        return ' '.join(text_list)

    def generate_bloom_text(self, data, *args, lang=None, **kwargs):
        """Doc."""
        blooms = np.logical_and(np.logical_or(data == 2, data == 3),
                                self.districts != 0)
        maxes = {}
        for area in np.unique(self.districts[blooms]):
            area_boolean = np.logical_and(blooms, self.districts == area)
            maxes.setdefault(area, data[area_boolean].max())

        surfs, subs = get_day_bloom_area_lists(maxes, lang=lang,
                                               mapper=self.mapper)

        if any(subs) and any(surfs):
            return self.mapper['day_text_mapper']['diverse'][lang].format(
                AREA_LIST_SURFS=get_area_name_string_list(surfs, lang=lang),
                AREA_LIST_SUBS=get_area_name_string_list(subs, lang=lang),
            )
        elif any(surfs):
            return self.mapper['day_text_mapper']['surfs'][lang].format(
                AREA_LIST_SURFS=get_area_name_string_list(surfs, lang=lang),
            )
        elif any(subs):
            return self.mapper['day_text_mapper']['subs'][lang].format(
                AREA_LIST_SUBS=get_area_name_string_list(subs, lang=lang),
            )
        else:
            return self.mapper['day_text_mapper']['zero'].get(lang)
