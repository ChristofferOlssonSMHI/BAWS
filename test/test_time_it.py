# -*- coding: utf-8 -*-
"""
Created on 2019-07-26 11:02

@author: a002028

"""
import time
import os


path = 'C:\\Temp\\shapes\\week_a_20190725.shp'

start_time = time.time()

# os.stat(path).st_size

os.path.getsize(path)


print("Session completed in --%.9f sec\n" % (time.time() - start_time))


