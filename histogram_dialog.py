# -*- coding: utf-8 -*-
"""
/***************************************************************************
 histogramDialog
                                 A QGIS plugin
 Create histogram
                             -------------------
        begin                : 2015-10-01
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Håvard Tveite, NMBU
        email                : havard.tveite@nmbu.no
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# User interface input components:
#   histogramGraphicsView: The GraphicsView that contains the histogram
#   binsSpinBox: Spinbox to set the number of bins
#   minValueSpinBox: Spinbox to set the minimum value
#   maxValueSpinBox: Spinbox to set the maximum value
#   selectedFeaturesCheckBox
#   inputLayer

import os
import csv

from math import pow, log
from PyQt4 import uic
from PyQt4.QtCore import SIGNAL, QObject, QThread, QCoreApplication
from PyQt4.QtCore import QPointF, QLineF, QRectF, QPoint, QSettings
from PyQt4.QtCore import QPyNullVariant, Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QFileDialog
from PyQt4.QtGui import QGraphicsLineItem, QGraphicsEllipseItem
from PyQt4.QtGui import QGraphicsRectItem, QGraphicsTextItem

from PyQt4.QtGui import QGraphicsScene, QBrush, QPen, QColor
from PyQt4.QtGui import QGraphicsView
from qgis.core import QgsMessageLog, QgsMapLayerRegistry, QgsMapLayer
from qgis.core import QGis
from qgis.gui import QgsMessageBar

from histogram_engine import Worker

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'histogram_dialog_base.ui'))


# Angles:
# Real world angles (and QGIS azimuth) are measured clockwise from
# the 12 o'clock position (north).
# QT angles are measured counter clockwise from the 3 o'clock
# position.
class histogramDialog(QDialog, FORM_CLASS):

    def __init__(self, iface, parent=None):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Some constants
        self.HISTOGRAM = self.tr('Histogram')
        self.BROWSE = self.tr('Browse')
        self.CANCEL = self.tr('Cancel')
        self.CLOSE = self.tr('Close')
        self.OK = self.tr('OK')
        self.NUMBEROFRINGS = 10  # Number of concentric rings in the histogram

        """Constructor."""
        super(histogramDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        okButton = self.button_box.button(QDialogButtonBox.Ok)
        okButton.setText(self.OK)
        cancelButton = self.button_box.button(QDialogButtonBox.Cancel)
        cancelButton.setText(self.CANCEL)

        browseButton = self.BrowseButton
        browseButton.setText(self.BROWSE)
        closeButton = self.button_box.button(QDialogButtonBox.Close)
        closeButton.setText(self.CLOSE)

        # Connect signals
        okButton.clicked.connect(self.startWorker)
        cancelButton.clicked.connect(self.killWorker)
        closeButton.clicked.connect(self.reject)
        browseButton.clicked.connect(self.browse)
        #minvalSBCh = self.minValueSpinBox.valueChanged[str]
        #minvalSBCh.connect(self.updateBins)
        #minvalSBCh.connect(function ....)
        #binsSBCh = self.binsSpinBox.valueChanged[str]
        #binsSBCh.connect(self.updateBins)

        #self.iface.legendInterface().itemAdded.connect(
        #    self.layerlistchanged)
        #self.iface.legendInterface().itemRemoved.connect(
        #    self.layerlistchanged)
        inpIndexCh = self.InputLayer.currentIndexChanged['QString']
        inpIndexCh.connect(self.layerchanged)
        fieldIndexCh = self.inputField.currentIndexChanged['QString']
        fieldIndexCh.connect(self.fieldchanged)

        QObject.disconnect(self.button_box, SIGNAL("rejected()"),
                           self.reject)

        # Set instance variables
        self.worker = None
        self.inputlayerid = None
        self.layerlistchanging = False
        self.bins = 8
        self.binsSpinBox.setValue(self.bins)
        self.selectedFeaturesCheckBox.setChecked(True)
        self.scene = QGraphicsScene(self)
        self.histogramGraphicsView.setScene(self.scene)
        self.result = None

    def startWorker(self):
        #self.showInfo('Ready to start worker')
        # Get the input layer
        layerindex = self.InputLayer.currentIndex()
        layerId = self.InputLayer.itemData(layerindex)
        inputlayer = QgsMapLayerRegistry.instance().mapLayer(layerId)
        if inputlayer is None:
            self.showError(self.tr('No input layer defined'))
            return
        if inputlayer.featureCount() == 0:
            self.showError(self.tr('No features in input layer'))
            self.scene.clear()
            return
        self.bins = self.binsSpinBox.value()
        self.outputfilename = self.outputFile.text()
        self.minValue = self.minValueSpinBox.value()
        self.maxValue = self.maxValueSpinBox.value()
        if self.maxValue - self.minValue < 0:
            self.showError(self.tr('Max value less than min value'))
            return
        if self.inputField.count() == 0:
            self.showError(self.tr('Missing numerical field'))
            self.scene.clear()
            return
        fieldindex = self.inputField.currentIndex()
        fieldname = self.inputField.itemData(fieldindex)
        self.result = None
        # create a new worker instance
        worker = Worker(inputlayer, self.bins, self.minValue,
                        self.maxValue,
                        self.selectedFeaturesCheckBox.isChecked(), fieldname)
        ## configure the QgsMessageBar
        #msgBar = self.iface.messageBar().createMessage(self.tr('Joining'), '')
        #self.aprogressBar = QProgressBar()
        #self.aprogressBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        #acancelButton = QPushButton()
        #acancelButton.setText(self.CANCEL)
        #acancelButton.clicked.connect(self.killWorker)
        #msgBar.layout().addWidget(self.aprogressBar)
        #msgBar.layout().addWidget(acancelButton)
        ## Has to be popped after the thread has finished (in
        ## workerFinished).
        #self.iface.messageBar().pushWidget(msgBar,
        #                                   self.iface.messageBar().INFO)
        #self.messageBar = msgBar
        # start the worker in a new thread
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)
        worker.status.connect(self.workerInfo)
        worker.progress.connect(self.progressBar.setValue)
        #worker.progress.connect(self.aprogressBar.setValue)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Close).setEnabled(False)
        self.InputLayer.setEnabled(False)
        self.inputField.setEnabled(False)

    def workerFinished(self, ok, ret):
        """Handles the output from the worker and cleans up after the
           worker has finished."""
        # clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        # remove widget from the message bar (pop)
        #self.iface.messageBar().popWidget(self.messageBar)
        if ok and ret is not None:
            #self.showInfo("Histogram: " + str(ret))
            self.result = ret
            # report the result
            # As a CSV file:
            if self.outputfilename != "":
                try:
                    with open(self.outputfilename, 'wb') as csvfile:
                        csvwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csvwriter.writerow(["StartValue", "EndValue",
                                            "Number"])
                        for i in range(len(ret)-1):
                            csvwriter.writerow([ret[i][0],ret[i+1][0],
                                                   ret[i][1]])
                        csvwriter.writerow([ret[len(ret)-1][0],self.maxValue,
                                                   ret[len(ret)-1][1]])
                    with open(self.outputfilename + 't', 'wb') as csvtfile:
                        csvtfile.write('"Real","Real","Integer"')
                except IOError, e:
                    self.showInfo("Trouble writing the CSV file: " + str(e))
            # Draw the histogram
            self.drawHistogram()
        else:
            # notify the user that something went wrong
            if not ok:
                self.showError(self.tr('Aborted') + '!')
            else:
                self.showError(self.tr('No histogram created') + '!')
        # Update the user interface
        self.progressBar.setValue(0.0)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self.button_box.button(QDialogButtonBox.Close).setEnabled(True)
        self.InputLayer.setEnabled(True)
        self.inputField.setEnabled(True)
        # end of workerFinished(self, ok, ret)

    def workerError(self, exception_string):
        """Report an error from the worker."""
        #QgsMessageLog.logMessage(self.tr('Worker failed - exception') +
        #                         ': ' + str(exception_string),
        #                         self.HISTOGRAM,
        #                         QgsMessageLog.CRITICAL)
        self.showError(exception_string)

    def workerInfo(self, message_string):
        """Report an info message from the worker."""
        QgsMessageLog.logMessage(self.tr('Worker') + ': ' +
                                 message_string,
                                 self.HISTOGRAM,
                                 QgsMessageLog.INFO)

    def killWorker(self):
        """Kill the worker thread."""
        if self.worker is not None:
            QgsMessageLog.logMessage(self.tr('Killing worker'),
                                     self.HISTOGRAM,
                                     QgsMessageLog.INFO)
            self.worker.kill()

    # Implement the reject method to have the possibility to avoid
    # exiting the dialog when cancelling
    def reject(self):
        """Reject override."""
        # exit the dialog
        QDialog.reject(self)

    def browse(self):
        outpath = saveDialog(self)
        self.outputFile.setText(outpath)


    def drawHistogram(self):
        if self.result is None:
            return
        # Label the histogram
        #self.minValueLabel.setText(str(self.minValue))
        #self.maxValueLabel.setText(str(self.maxValue))
        minvaltext = QGraphicsTextItem(str(self.minValue))
        minvaltextheight = minvaltext.boundingRect().height()
        maxvaltext = QGraphicsTextItem(str(self.maxValue))
        maxvaltextwidth = maxvaltext.boundingRect().width()

        #self.showInfo(str(self.result))
        # Check which element should be used for the histogram
        element = 1
        maxvalue = 0.0
        for i in range(len(self.result)):
            if self.result[i][element] > maxvalue:
                maxvalue = self.result[i][element]
                # Find the maximum value for scaling
        cutoffvalue = maxvalue
        if (self.frequencyRangeSpinBox.value() > 0):
            cutoffvalue = self.frequencyRangeSpinBox.value()
        #self.maxNumberLabel.setText(str(maxvalue))
        #self.maxNumberLabel.setText(str(cutoffvalue))
        self.scene.clear()
        if maxvalue == 0:
            return
        viewprect = QRectF(self.histogramGraphicsView.viewport().rect())
        self.histogramGraphicsView.setSceneRect(viewprect)
        bottom = self.histogramGraphicsView.sceneRect().bottom()
        top = self.histogramGraphicsView.sceneRect().top()
        left = self.histogramGraphicsView.sceneRect().left()
        right = self.histogramGraphicsView.sceneRect().right()
        height = bottom - top - 1
        width = right - left - 1
        padding = 3
        toppadding = 3
        bottompadding = minvaltextheight
        # Determine the width of the left margin (depends on the y range)
        clog = log(cutoffvalue,10)
        clogint = int(clog)
        #clogrem = clog % clogint
        yincr = pow(10,clogint)
        dummytext = QGraphicsTextItem(str(yincr))
        # The left padding must accomodate the y labels
        leftpadding = dummytext.boundingRect().width()
        #leftpadding = 30
        # Find the width of the maximium frequency label
        maxfreqtext = QGraphicsTextItem(str(cutoffvalue))
        maxfreqtextwidth = maxvaltext.boundingRect().width()
        rightpadding = maxfreqtextwidth
        width = width - (leftpadding + rightpadding)
        height = height - (toppadding + bottompadding)
        barwidth = width / self.bins
        #center = QPoint(left + width / 2.0, top + height / 2.0)
        #start = QPointF(self.histogramGraphicsView.mapToScene(center))

        # Create the histogram
        for i in range(self.bins):
            #barheight = height * self.result[i][element] / maxvalue
            barheight = height * self.result[i][element] / cutoffvalue
            barrect = QGraphicsRectItem(QRectF(leftpadding + barwidth * i,
                        height-barheight+toppadding, barwidth, barheight))
            barbrush = QBrush(QColor(255,153,102))
            barrect.setBrush(barbrush)
            self.scene.addItem(barrect)
        
        # Determine the increments for the horizontal lines
        if (cutoffvalue // yincr <= 5 and yincr > 1 ):
            yincr = yincr / 2
            if (cutoffvalue // yincr < 5 and yincr > 10 ):
                yincr = yincr / 2
        # Draw horizontal lines with labels
        yval = 0
        while (yval <= cutoffvalue):
            scval = height + toppadding - yval * height / cutoffvalue
            hline = QGraphicsLineItem(QLineF(leftpadding-2, scval,width+(leftpadding),scval))
            hlinepen = QPen(QColor(153,153,153))
            hline.setPen(hlinepen)
            self.scene.addItem(hline)
            ylabtext = QGraphicsTextItem(str(int(yval)))
            ylabtextheight = ylabtext.boundingRect().height()
            ylabtextwidth = ylabtext.boundingRect().width()
            ylabtext.setPos(leftpadding - ylabtextwidth, scval - ylabtextheight/2)
            if (scval - ylabtextheight/2 > 0):
                self.scene.addItem(ylabtext)
            yval = yval + yincr

            
        #yincr = (cutoffvalue / 10)
        minvaltextwidth = minvaltext.boundingRect().width()
        minvaltext.setPos(leftpadding - minvaltextwidth/2, height + toppadding + bottompadding - minvaltextheight)
        self.scene.addItem(minvaltext)
        maxvaltext.setPos(leftpadding + width - maxvaltextwidth/2, height + toppadding + bottompadding - minvaltextheight)
        self.scene.addItem(maxvaltext)
        maxfreqtext.setPos(leftpadding + width, 0)
        self.scene.addItem(maxfreqtext)
        
        #self.minvalueHorizontalSpacer.changeSize(leftpadding,0)
        
        
    # Update the visualisation of the bin structure
    def updateBins(self):
        return true
        # end of updatebins


    #def layerlistchanged(self):
    #    self.layerlistchanging = True
    #    # Repopulate the input and join layer combo boxes
    #    # Save the currently selected input layer
    #    inputlayerid = self.inputlayerid
    #    self.InputLayer.clear()
    #    # We are only interested in line and polygon layers
    #    for alayer in self.iface.legendInterface().layers():
    #        if alayer.type() == QgsMapLayer.VectorLayer:
    #            if (alayer.geometryType() == QGis.Line or
    #                alayer.geometryType() == QGis.Polygon):
    #                self.InputLayer.addItem(alayer.name(), alayer.id())
    #    # Set the previous selection
    #    for i in range(self.InputLayer.count()):
    #        if self.InputLayer.itemData(i) == inputlayerid:
    #            self.InputLayer.setCurrentIndex(i)
    #    self.layerlistchanging = False

    def layerchanged(self, number=0):
        """Do the necessary updates after a layer selection has
           been changed."""
        ## If the layer list is being updated, don't do anything
        #if self.layerlistchanging:
        #    return
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.layerselectionactive = True
        layerindex = self.InputLayer.currentIndex()
        layerId = self.InputLayer.itemData(layerindex)
        self.inputlayerid = layerId
        inputlayer = QgsMapLayerRegistry.instance().mapLayer(layerId)
        while self.inputField.count() > 0: 
            self.inputField.removeItem(0)
        self.layerselectionactive = False
        # Get the numerical fields
        if inputlayer is not None:
            provider = inputlayer.dataProvider()
            attribs = provider.fields()
            if str(type(attribs)) != "<type 'dict'>":
                atr = {}
                for i in range(attribs.count()):
                    atr[i] = attribs.at(i)
                attrdict = atr
            for id, attrib in attrdict.iteritems():                            
                # Check for numeric attribute
                if attrib.typeName().upper() in ('REAL', 'INTEGER', 'INT4', 'INT8', 'FLOAT4'):
                    self.inputField.addItem(attrib.name(), attrib.name())
            if (self.inputField.count() > 0):
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            
        #self.updateui()

    def fieldchanged(self, number=0):
        """Do the necessary updates after the field selection has
           been changed."""
        ## If the layer list is being updated, don't do anything
        #if self.layerlistchanging:
        #    return
        if self.layerselectionactive:
            return
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        inputlayer = QgsMapLayerRegistry.instance().mapLayer(self.inputlayerid)
        if inputlayer is not None:
            inpfield = inputlayer.fieldNameIndex(self.inputField.itemData(self.inputField.currentIndex()))
            if (inpfield is not None):
                minval = inputlayer.minimumValue(inpfield)
                maxval = inputlayer.maximumValue(inpfield)
                if not isinstance(minval, QPyNullVariant):
                    self.minValueSpinBox.setValue(minval)
                    self.maxValueSpinBox.setValue(maxval)
                    self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                else:
                    self.minValueSpinBox.setValue(0.0)
                    self.maxValueSpinBox.setValue(0.0)
            

    def showError(self, text):
        """Show an error."""
        self.iface.messageBar().pushMessage(self.tr('Error'), text,
                                            level=QgsMessageBar.CRITICAL,
                                            duration=3)
        QgsMessageLog.logMessage('Error: ' + text,
                                 self.HISTOGRAM,
                                 QgsMessageLog.CRITICAL)

    def showWarning(self, text):
        """Show a warning."""
        self.iface.messageBar().pushMessage(self.tr('Warning'), text,
                                            level=QgsMessageBar.WARNING,
                                            duration=2)
        QgsMessageLog.logMessage('Warning: ' + text,
                                 self.HISTOGRAM,
                                 QgsMessageLog.WARNING)

    def showInfo(self, text):
        """Show info."""
        self.iface.messageBar().pushMessage(self.tr('Info'), text,
                                            level=QgsMessageBar.INFO,
                                            duration=2)
        QgsMessageLog.logMessage('Info: ' + text,
                                 self.HISTOGRAM,
                                 QgsMessageLog.INFO)

    # Implement the accept method to avoid exiting the dialog when
    # starting the work
    def accept(self):
        """Accept override."""
        pass

    # Implement the reject method to have the possibility to avoid
    # exiting the dialog when cancelling
    def reject(self):
        """Reject override."""
        # exit the dialog
        QDialog.reject(self)

    # Translation
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('Dialog', message)

    # Overriding
    def resizeEvent(self, event):
        #self.showInfo("resizeEvent")
        if (self.result is not None):
            self.drawHistogram()

    # Overriding
    def showEvent(self, event):
        return
        #self.showInfo("showEvent")
        #self.updateBins()


def saveDialog(parent):
        """Shows a file dialog and return the selected file path."""
        settings = QSettings()
        key = '/UI/lastShapefileDir'
        outDir = settings.value(key)
        filter = 'Comma Separated Value (*.csv)'
        outFilePath = QFileDialog.getSaveFileName(parent,
                       parent.tr('Output CSV file'), outDir, filter)
        outFilePath = unicode(outFilePath)
        if outFilePath:
            root, ext = os.path.splitext(outFilePath)
            if ext.upper() != '.CSV':
                outFilePath = '%s.csv' % outFilePath
            outDir = os.path.dirname(outFilePath)
            settings.setValue(key, outDir)
        return outFilePath
