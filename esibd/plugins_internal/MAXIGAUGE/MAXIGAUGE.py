# pylint: disable=[missing-module-docstring] # only single class in module
import time
import serial
import numpy as np
from esibd.plugins import Device
from esibd.core import Parameter, PluginManager, Channel, parameterDict, DeviceController, PRINT, getTestMode

def providePlugins():
    return [MAXIGAUGE]

class MAXIGAUGE(Device):
    """Device that reads pressure values form a Pfeiffer MaxiGauge."""
    documentation = None # use __doc__

    name = 'MAXIGAUGE'
    version = '1.0'
    supportedVersion = '0.6'
    pluginType = PluginManager.TYPE.OUTPUTDEVICE
    unit = 'mbar'

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.channelType = PressureChannel
        self.controller = PressureController(_parent=self)
        self.logY = True

    def getIcon(self, **kwargs):
        return self.makeIcon('pfeiffer_maxi.png', **kwargs)

    def getDefaultSettings(self):
        ds = super().getDefaultSettings()
        ds[f'{self.name}/Interval'][Parameter.VALUE] = 500 # overwrite default value
        ds[f'{self.name}/COM'] = parameterDict(value='COM1', toolTip='COM port.', items=','.join([f'COM{x}' for x in range(1, 25)]),
                                          widgetType=Parameter.TYPE.COMBO, attr='COM')
        ds[f'{self.name}/{self.MAXDATAPOINTS}'][Parameter.VALUE] = 1E6 # overwrite default value
        return ds

    def getInitializedChannels(self):
        return [channel for channel in self.channels if (channel.enabled and (self.controller.port is not None
                                              or self.getTestMode())) or not channel.active]

class PressureChannel(Channel):
    """UI for pressure with integrated functionality"""

    ID = 'ID'

    def getDefaultChannel(self):
        channel = super().getDefaultChannel()
        channel[self.VALUE][Parameter.HEADER] = 'P (mbar)' # overwrite existing parameter to change header
        channel[self.VALUE][Parameter.WIDGETTYPE] = Parameter.TYPE.EXP # overwrite existing parameter to change to use exponent notation
        channel[self.ID] = parameterDict(value=1, widgetType=Parameter.TYPE.INTCOMBO, advanced=True,
                                        items='0, 1, 2, 3, 4, 5, 6', attr='id')
        return channel

    def setDisplayedParameters(self):
        super().setDisplayedParameters()
        self.displayedParameters.append(self.ID)

class PressureController(DeviceController):

    def closeCommunication(self):
        if self.port is not None:
            with self.lock.acquire_timeout(1, timeoutMessage='Could not acquire lock before closing port.'):
                self.port.close()
                self.port = None
        super().closeCommunication()

    def runInitialization(self):
        try:
            self.port=serial.Serial(f'{self.device.COM}', baudrate=9600, bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, timeout=2)
            TPGStatus = self.TPGWriteRead(message='TID')
            self.print(f"MaxiGauge Status: {TPGStatus}") # gauge identification
            if TPGStatus == '':
                raise ValueError('TPG did not return status.')
            self.signalComm.initCompleteSignal.emit()
        except Exception as e: # pylint: disable=[broad-except]
            self.print(f'TPG Error while initializing: {e}', PRINT.ERROR)
        finally:
            self.initializing = False

    def initComplete(self):
        self.pressures = [np.nan]*len(self.device.channels)
        super().initComplete()

    def runAcquisition(self, acquiring):
        while acquiring():
            with self.lock.acquire_timeout(1) as lock_acquired:
                if lock_acquired:
                    self.fakeNumbers() if getTestMode() else self.readNumbers()
                    self.signalComm.updateValueSignal.emit()
            time.sleep(self.device.interval/1000)

    PRESSURE_READING_STATUS = {
      0: 'Measurement data okay',
      1: 'Underrange',
      2: 'Overrange',
      3: 'Sensor error',
      4: 'Sensor off',
      5: 'No sensor',
      6: 'Identification error'
    }

    def readNumbers(self):
        for i, channel in enumerate(self.device.getChannels()):
            if channel.enabled and channel.active:
                if self.initialized:
                    msg = self.TPGWriteRead(message=f'PR{channel.id}', lock_acquired=True)
                    try:
                        status, pressure = msg.split(',')
                        if status == '0':
                            self.pressures[i] = float(pressure) # set unit to mbar on device
                            # self.print(f'Read pressure for channel {channel.name}', flag=PRINT.DEBUG)
                        else:
                            self.print(f'Could not read pressure for {channel.name}: {self.PRESSURE_READING_STATUS[int(status)]}.', PRINT.WARNING)
                            self.pressures[i] = np.nan
                    except Exception as e:
                        self.print(f'Failed to parse pressure from {msg}: {e}', PRINT.ERROR)
                        self.pressures[i] = np.nan
                else:
                    self.pressures[i] = np.nan

    def fakeNumbers(self):
        for i, pressure in enumerate(self.pressures):
            self.pressures[i] = self.rndPressure() if np.isnan(pressure) else pressure*np.random.uniform(.99, 1.01) # allow for small fluctuation

    def rndPressure(self):
        exp = np.random.randint(-11, 3)
        significand = 0.9 * np.random.random() + 0.1
        return significand * 10**exp

    def updateValue(self):
        for channel, pressure in zip(self.device.getChannels(), self.pressures):
            channel.value = pressure

    def TPGWrite(self, message):
        self.serialWrite(self.port, f'{message}\r', encoding='ascii')
        self.serialRead(self.port, encoding='ascii') # read acknowledgment

    def TPGRead(self):
        self.serialWrite(self.port, '\x05\r', encoding='ascii') # Enquiry prompts sending return from previously send mnemonic
        enq =  self.serialRead(self.port, encoding='ascii') # response
        self.serialRead(self.port, encoding='ascii') # followed by NAK
        return enq

    def TPGWriteRead(self, message, lock_acquired=False):
        response = ''
        with self.tpgLock.acquire_timeout(2, timeoutMessage=f'Cannot acquire lock for message: {message}', lock_acquired=lock_acquired) as lock_acquired:
            if lock_acquired:
                self.TPGWrite(message)
                response = self.TPGRead() # reads return value
        return response
