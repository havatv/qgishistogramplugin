# -*- coding: utf-8 -*-
from math import sqrt
from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication, QPyNullVariant
from qgis.core import QGis
from qgis.core import QgsVectorLayer

# Angles:
# Real world angles are measured clockwise from the 12 o'clock
# position (north)
# QGIS azimuth angles: clockwise in degree, starting from north
# QT angles are measured counter clockwise from the 3 o'clock
# position


class Worker(QtCore.QObject):
    '''The worker that does the heavy lifting.
    The number and length of the line segments of the inputlayer
    line or polygon vector layer is calculated for each angle bin.
    A vector of bins is returned.  Each bin contains the total
    length and the number of line segments in the bin.
    '''
    # Define the signals used to communicate
    progress = QtCore.pyqtSignal(float)  # For reporting progress
    status = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
    # Signal for sending over the result:
    finished = QtCore.pyqtSignal(bool, object)

    #directionneutral, 
    def __init__(self, inputvectorlayer, bins, minvalue,
                                  maxvalue, selectedfeaturesonly,
                                  numericalattribute):
        """Initialise.

        Arguments:
        inputvectorlayer --     (QgsVectorLayer) The base vector
                                 layer for the join
        bins --                 (int) bins for end point matching
        minvalue --             (float) lower limit for range
        #directionneutral --     (boolean) should lines in oposite
                                 directions be handled as having the
                                 same directionneutral
        maxvalue --             (float) upper limit for range
        #offsetangle --          (float) Start the bins at a different
                                 angle
        selectedfeaturesonly -- (boolean) should only selected
                                 features be considered
        numericalattribute --   (string) attribute name for the numerical attribute
        #findminmax --           (boolean) Should min and max be determined
        """

        QtCore.QObject.__init__(self)  # Essential!
        # Creating instance variables from parameters
        self.inputvectorlayer = inputvectorlayer
        self.bins = int(bins)
        self.minvalue = minvalue
        #self.directionneutral = directionneutral
        self.maxvalue = maxvalue
        #self.offsetangle = offsetangle
        self.selectedfeaturesonly = selectedfeaturesonly
        self.numericalattribute = numericalattribute
        #self.findminmax = findminmax
        #self.binsize = 360.0 / bins
        self.binsize = (self.maxvalue - self.minvalue) / self.bins
        #if self.directionneutral:
        #    self.binsize = 180.0 / bins

        # Creating instance variables for the progress bar ++
        # Number of elements that have been processed - updated by
        # calculate_progress
        self.processed = 0
        # Current percentage of progress - updated by
        # calculate_progress
        self.percentage = 0
        # Flag set by kill(), checked in the loop
        self.abort = False
        # Number of features in the input layer - used by
        # calculate_progress
        self.feature_count = self.inputvectorlayer.featureCount()
        # The number of elements that is needed to increment the
        # progressbar - set early in run()
        self.increment = self.feature_count // 1000

    def run(self):
        self.status.emit('Started! Min: ' + str(self.minvalue) + ' Max: ' + str(self.maxvalue))
        try:
            # Make sure the input layer is OK
            inputlayer = self.inputvectorlayer
            if inputlayer is None:
                self.error.emit(self.tr('No input layer defined'))
                self.finished.emit(False, None)
                return
            # Prepare for the progress bar
            self.processed = 0
            self.percentage = 0
            self.feature_count = inputlayer.featureCount()
            # Check if the layer has features
            if self.feature_count == 0:
                self.error.emit("No features in layer")
                self.finished.emit(False, None)
                return
            self.increment = self.feature_count // 1000
            # Initialise the bins
            statistics = []
            for i in range(self.bins):
                #statistics.append([0.0, 0])
                statistics.append([self.minvalue + i * self.binsize, 0])
                #self.minvalue
            # Get the features (iterator)
            if (inputlayer.selectedFeatureCount() > 0 and
                                          self.selectedfeaturesonly):
                features = inputlayer.selectedFeaturesIterator()
            else:
                features = inputlayer.getFeatures()
            # Go through the features
            for feat in features:
                # Allow user abort
                if self.abort is True:
                    break
                # Work on the attribute
                val = feat[self.numericalattribute]
                # Check if the value is meaningful
                if val is None:
                    break
                if self.binsize == 0:
                    statistics[0][1] = (statistics[0][1] + 1)
                    continue
                if isinstance(val, QPyNullVariant):
                    break
                value = float(val)
                # Check if the value is outside the range
                if (value < self.minvalue or value > self.maxvalue):
                    self.status.emit('outside range - ' + str(value))
                    continue
                #value = feat.attribute[self.numericalattribute]
                #fittingbin = (int(((value + 180)) / self.binsize)
                #                      % self.bins)
                #fittingbin = int((value - self.minvalue) / self.binsize) // self.bins
                fittingbin = int((value - self.minvalue) / self.binsize)
                #fittingbin = int((value - self.minvalue) / self.binsize) % self.bins
                # Have to handle special case to keep index in range
                if fittingbin >= self.bins:
                    self.status.emit('top border')
                    fittingbin = fittingbin-1
                if fittingbin < 0:
                    continue
                if fittingbin == 0:
                    self.status.emit('0: ' + str(value))
                # Add to the length of the bin
                # Add to the number of elements in the bin
                statistics[fittingbin][1] = (statistics[fittingbin][1] + 1)
                self.calculate_progress()

        except:
            import traceback
            self.error.emit(traceback.format_exc())
            self.finished.emit(False, None)
        else:
            if self.abort:
                self.finished.emit(False, None)
            else:
                self.finished.emit(True, statistics)

    def calculate_progress(self):
        '''Update progress and emit a signal with the percentage'''
        self.processed = self.processed + 1
        # update the progress bar at certain increments
        if self.increment == 0 or self.processed % self.increment == 0:
            percentage_new = (self.processed * 100) / self.feature_count
            if percentage_new > self.percentage:
                self.percentage = percentage_new
                self.progress.emit(self.percentage)

    def kill(self):
        '''Kill the thread by setting the abort flag'''
        self.abort = True

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Engine', message)
