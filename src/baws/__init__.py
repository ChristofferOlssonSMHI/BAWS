# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BAWS
                                 A QGIS plugin
 Manully adjust algae maps
                              -------------------
        begin                : 2019-04-17
        copyright            : (C) 2019 by SMHI
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'SMHI-JJ'
__date__ = '2019-04-17'
__copyright__ = '(C) 2019 by SMHI'
__version__ = '3.2.3'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load BAWS class from file BAWS.

    iface (QgisInterface): A QGIS interface instance.
    """
    #
    from .baws import BAWSPlugin
    return BAWSPlugin(iface)
