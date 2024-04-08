"""
Created on 2021-06-29 15:12

@author: johannes
"""
import os
import time


def check_while_saving(path, file_type, number_of_files):
    """"""
    if not file_type and not number_of_files:
        return

    start_time = time.time()

    while len([True for f in os.listdir(path)
               if f.endswith(file_type)]) != number_of_files:
        time.sleep(0.1)

    print('\nReady to merge shapefiles! (Rasterized shapes in %.1f sec)'
          '\n' % (time.time() - start_time))
