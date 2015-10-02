.. linedirectionhistogram documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

*******************************************
The QGIS Histogram Plugin
*******************************************

.. toctree::
   :maxdepth: 2

   
Functionality
=================

- The QGIS Histogram Plugin can be used to investigate the
  distribution of numerical values for vector layer attributes.

- Feature selections are supported.

- The number of bins for the histogram can be specified.

- All the bins are distributed equally.

- The minimum and maximum value for the histogram can be set by
  the user.

- A cutoff value can be used for the histogram's frequency axis.

- A histogram is displayed, showing the distribution of the
  values according to the chosen bins.
  
- The histogram can be saved to a CSV file.

- If the plugin window is resized, the direction histogram is also
  resized.
  

The displayed histogram
========================

The displayed histogram is normalised, so that the maximum value of
the bins will result in a bar with a maximum length, and
the lengths of the bars of the rest of the bins are scaled
proportionally.


The saved histogram
====================

The saved histogram is a CSV file with four columns:

- The first column ("StartValue") contains the start value of the
  bin.
- The second column ("EndValue") contains the end value of the
  bin.
- The third column ("Number") contains the number of elements
  that fall inside the bin.
"." is used as the decimal separator in the CSV file.

The CSV file is accompanied by a CSVT file that describes the
data types of the CSV file columns.


Options
=============

- The user can specify if only selected features are to be used
  (but if no features are selected, all features will be used)

- The user can specify the number of bins.

- The user can specify the minimum and maximum values to be
  considered for the histogram.

- The user can specify a cutoff value for the frequency axis (to
  focus on the distribution among those bins that have fewer
  elements.

- The user can specify an output CSV file for the histogram.


Implementation
================

The calculations of the histogram is performed in a separate thread.


Versions
===============
The current version is 1.0.

- 1.0: First official version.


Links
=======

`Histogram Plugin`_

`Histogram code repository`_

`Histogram issues`_


.. _Histogram code repository: https://github.com/havatv/qgishistogramplugin.git
.. _Histogram Plugin: http://arken.umb.no/~havatv/gis/qgisplugins/Histogram
.. _Histogram issues: https://github.com/havatv/qgishistogramplugin/issues
.. |N2| replace:: N\ :sup:`2`
