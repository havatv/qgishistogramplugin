# -*- coding: utf-8 -*-
"""
/***************************************************************************
 histogram
                                 A QGIS plugin
 Prepare a histogram based on a numerical attribute and a number of
 bins.
                             -------------------
        begin                : 2015-10-01
        copyright            : (C) 2015 by Håvard Tveite
        email                : havard.tveite@nmbu.no
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load histogram class from file histogram.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    from .histogram import histogram
    return histogram(iface)
