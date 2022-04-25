# BAWS - The Baltic Algal Watch System (2002 - Present)
QGIS 3 plugin - Python 3 developed by Sh at SMHI.

Usage:
- Mapping of cyanobacteria surface accumulations
- Loading Sentinel 3 OLCI Level 2 (BAWS algorithm data)
- Loading GeoTiff rasters "Ocean-color"
    - Sentinel 3A, 3B
    - EOS Aqua
    - Suomi-NPP
    - NOAA-20
- Manual adjustment using standard QGIS functionality.

Out formats:
- Shapefiles
- Geotiff
- Png
- Txt

TODO:
- Continue with clean up. Work started in 2022 but needs extra care..
- Look over Level 2 resolution, can we start using 300m? Is it needed?
- Evaluate use of newly updated algorithm
    - Lower threshold value for subsurface accumulation
    - Extreme surface accumulation


Example in QGIS
---------------
![BAWS Example](resources/example_screenshot.png "BAWS Example")
