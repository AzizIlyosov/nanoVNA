import logging
import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox
)
from PyQt5 import QtCore, QtGui, QtWidgets
# from Hardware.Serial import Interface
from typing import List
from Hardware.Hardware import Interface, get_interfaces, get_VNA
from RFTools import Datapoint, corr_att_data
from Controls import MarkerControl, SweepControl
from Touchstone import Touchstone
from pyqtgraph import PlotWidget
from forms.setup import Ui_Dialog as Ui_Dialog_Setup
from forms.data import Ui_Dialog as Ui_Dialog_Data
from forms.scale import Ui_Dialog as Ui_Dialog_Scale
from Hardware.VNA import VNA
from Settings import BandsModel, Sweep
from SweepWorker import SweepWorker
import threading
from time import sleep

from Calibration import Calibration
from Marker import Marker, DeltaMarker
from SweepWorker import SweepWorker
from Settings import BandsModel, Sweep
from Touchstone import Touchstone
import pyqtgraph as pg

from forms.main import Ui_MainWindow





logger = logging.getLogger(__name__) 



class Window(QMainWindow, Ui_MainWindow):
    # version = VERSION
    dataAvailable = QtCore.pyqtSignal()
    scaleFactor = 1

    def __init__(self, parent=None):
        super().__init__(parent)

        self.threadpool = QtCore.QThreadPool()

        self.sweep = Sweep()
        self.worker = SweepWorker(self)
        print('this is  worker ', self.worker)
        # worker is socket which  reads data continiously 
        self.worker.signals.updated.connect(self.dataUpdated)
        self.worker.signals.finished.connect(self.sweepFinished)
        self.worker.signals.sweepError.connect(self.showSweepError)
        self.worker.signals.fatalSweepError.connect(self.showFatalSweepError)

        # self.sweep_control = SweepControl(self)
        # self.marker_control = MarkerControl(self)

        self.bands = BandsModel()

        self.interface = Interface("serial", "None")
        print('this is  Interface ', self.interface)
        self.vna = VNA(self.interface)
        
        self.dataLock = threading.Lock()

        self.data11: List[Datapoint] = []
        self.data21: List[Datapoint] = []
        self.referenceS11data: List[Datapoint] = []
        self.referenceS21data: List[Datapoint] = []

        self.sweepSource = ""
        self.referenceSource = ""

        self.calibration = Calibration()

        logger.debug("Building user interface")

        self.baseTitle = f"NanoVNA Saver  "
        # self.updateTitle()
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)

        # scrollarea = QtWidgets.QScrollArea()
        # outer = QtWidgets.QVBoxLayout()
        # outer.addWidget(scrollarea)
        # self.setLayout(outer)
        # scrollarea.setWidgetResizable(True)
        # window_width = self.settings.value("WindowWidth", 1350, type=int)
        # window_height = self.settings.value("WindowHeight", 950, type=int)
        # self.resize(window_width, window_height)
        # scrollarea.setSizePolicy(
        #     QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
        #                    QtWidgets.QSizePolicy.MinimumExpanding)
        # widget = QtWidgets.QWidget()
        # widget.setLayout(layout)
        # scrollarea.setWidget(widget)



        self.setupUi(self) 
        self.connectSignalsSlots()
        self.plotData()
        self.rescanSerialPort()

    # this  slots  connec all buttons with  dialogs 
    def connectSignalsSlots(self):
        self.pushButton_2.clicked.connect(self.openSetup)
        self.pushButton.clicked.connect(self.openScale)
        self.pushButton_4.clicked.connect(self.openData) 
    

    def plotData(self):
        print('plot data ')
        textx = [1,2,3,4,5,6,7,8,9,10]
        testy = [30,32,34,32,33,31,29,32,35,45]
        self.widget.plot(textx, testy)
        






    

    def dataUpdated(self):
        with self.dataLock:
            s11data = self.data11[:]
            s21data = self.data21[:]

        for m in self.markers:
            m.resetLabels()
            m.updateLabels(s11data, s21data)

        for c in self.s11charts:
            print('data is  updates', c)
            c.setData(s11data)

        for c in self.s21charts:
            print('data is  updates', c)
            c.setData(s21data)

        for c in self.combinedCharts:
            c.setCombinedData(s11data, s21data)

        self.sweep_control.progress_bar.setValue(self.worker.percentage)
        self.windows["tdr"].updateTDR()

        # if s11data:
        #     min_vswr = min(s11data, key=lambda data: data.vswr)
        #     self.s11_min_swr_label.setText(
        #         f"{format_vswr(min_vswr.vswr)} @ {format_frequency(min_vswr.freq)}")
        #     self.s11_min_rl_label.setText(format_gain(min_vswr.gain))
        # else:
        #     self.s11_min_swr_label.setText("")
        #     self.s11_min_rl_label.setText("")

        # if s21data:
        #     min_gain = min(s21data, key=lambda data: data.gain)
        #     max_gain = max(s21data, key=lambda data: data.gain)
        #     self.s21_min_gain_label.setText(
        #         f"{format_gain(min_gain.gain)}"
        #         f" @ {format_frequency(min_gain.freq)}")
        #     self.s21_max_gain_label.setText(
        #         f"{format_gain(max_gain.gain)}"
        #         f" @ {format_frequency(max_gain.freq)}")
        # else:
        #     self.s21_min_gain_label.setText("")
        #     self.s21_max_gain_label.setText("")

        # self.updateTitle()
        self.dataAvailable.emit()

    def sweepFinished(self):
        self.sweep_control.progress_bar.setValue(100)
        self.sweep_control.btn_start.setDisabled(False)
        self.sweep_control.btn_stop.setDisabled(True)
        self.sweep_control.toggle_settings(False)

        for marker in self.markers:
            marker.frequencyInput.textEdited.emit(
                marker.frequencyInput.text())

    def setReference(self, s11data=None, s21data=None, source=None):
        if not s11data:
            with self.dataLock:
                s11data = self.data11[:]
                s21data = self.data21[:]

        self.referenceS11data = s11data
        for c in self.s11charts:
            c.setReference(s11data)

        self.referenceS21data = s21data
        for c in self.s21charts:
            c.setReference(s21data)

        for c in self.combinedCharts:
            c.setCombinedReference(s11data, s21data)

        self.btnResetReference.setDisabled(False)

        if source is not None:
            # Save the reference source info
            self.referenceSource = source
        else:
            self.referenceSource = self.sweepSource
        self.updateTitle()


    def showFatalSweepError(self):
        self.showError(self.worker.error_message)
        self.stopSerial()

    def showSweepError(self):
        self.showError(self.worker.error_message)
        try:
            self.vna.flushSerialBuffers()  # Remove any left-over data
            self.vna.reconnect()  # try reconnection
        except IOError:
            pass
        self.sweepFinished()

    



        

    def openSetup(self):
        Dialog = QtWidgets.QDialog()
        Dialog.setModal(False)
        ui = Ui_Dialog_Setup() 
        ui.setupUi(Dialog)
        Dialog.exec() 
 
    def openScale(self):
        Dialog = QtWidgets.QDialog()
        ui = Ui_Dialog_Scale()
        ui.setupUi(Dialog)
        Dialog.exec()

    def openData(self):
        Dialog = QtWidgets.QDialog()
        Dialog.setModal(False)
        ui = Ui_Dialog_Data()
        ui.setupUi(Dialog)
        # loading sweep file 
        ui.pushButton.clicked.connect(self.loadSweepFile)
        Dialog.exec()

    def rescanSerialPort(self):
        print('I am searhing all available ports ')
        # new item for serieal port should be added in this line 
        # self.serialPortInput.clear()
        for iface in get_interfaces():
            self.serialPortInput.insertItem(1, f"{iface}", iface)
            print('this is iface ', iface)
        # self.serialPortInput.repaint()
    
    def connect_device(self):
        if not self.interface:
            return
        with self.interface.lock:
            self.interface = '/dev/ttyACMO(S-A-A-2)' #  self.serialPortInput.currentData()
            logger.info("Connection %s", self.interface)
            try:
                self.interface.open()

            except (IOError, AttributeError) as exc:
                logger.error("Tried to open %s and failed: %s",
                             self.interface, exc)
                return
            if not self.interface.isOpen():
                logger.error("Unable to open port %s", self.interface)
                return
            self.interface.timeout = 0.05
        sleep(0.1)
        try:
            self.vna = get_VNA(self.interface)
        except IOError as exc:
            logger.error("Unable to connect to VNA: %s", exc)

        self.vna.validateInput = self.settings.value(
            "SerialInputValidation", True, bool)

        # connected
        self.btnSerialToggle.setText("Disconnect")
        self.btnSerialToggle.repaint()

        frequencies = self.vna.readFrequencies()
        print('this is frequencies ', frequencies)

        if not frequencies:
            logger.warning("No frequencies read")
            return
        logger.info("Read starting frequency %s and end frequency %s",
                    frequencies[0], frequencies[-1])
        # self.sweep_control.set_start(frequencies[0])
        # if frequencies[0] < frequencies[-1]:
        #     self.sweep_control.set_end(frequencies[-1])
        # else:
        #     self.sweep_control.set_end(
        #         frequencies[0] +
                # self.vna.datapoints * self.sweep_control.get_segments())

        # self.sweep_control.set_segments(1)  # speed up things
        # self.sweep_control.update_center_span()
        # self.sweep_control.update_step_size()

        self.windows["sweep_settings"].vna_connected()

        logger.debug("Starting initial sweep")
        self.sweep_start()
    
    def loadSweepFile(self):
        #TODO: finish this method 
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            filter="Touchstone Files (*.s1p *.s2p);;All files (*.*)")
        if filename != "":    
            t= Touchstone('test/data/attenuator-0643_MA.s2p')
            t.load()
            print(t.s11data)

    def loadReferenceFile(self):
        # TODO: finish this method 
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            filter="Touchstone Files (*.s1p *.s2p);;All files (*.*)")
        if filename != "":
            self.resetReference()
            t = Touchstone(filename)
            t.load()
            print(t.s11data)
            # uncoment following file  
            # self.setReference(t.s11data, t.s21data, filename)
    
    
    def setReference(self, s11data=None, s21data=None, source=None):
        if not s11data:
            with self.dataLock:
                s11data = self.data11[:]
                s21data = self.data21[:]

        self.referenceS11data = s11data
        for c in self.s11charts:
            c.setReference(s11data)

        self.referenceS21data = s21data
        for c in self.s21charts:
            c.setReference(s21data)

        for c in self.combinedCharts:
            c.setCombinedReference(s11data, s21data)

        self.btnResetReference.setDisabled(False)

        if source is not None:
            # Save the reference source info
            self.referenceSource = source
        else:
            self.referenceSource = self.sweepSource
        self.updateTitle()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show() 
    sys.exit(app.exec())