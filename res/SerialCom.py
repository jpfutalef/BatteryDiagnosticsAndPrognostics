# Comunicacion serial para tomar mediciones de descarga

import serial
import time
import sys
import signal
import numpy as np
import pandas as pd

# User defined variables
serial_port = 'COM1'


# Useful functions
def signal_handler():
    print('\nfinishing')


# Classes
class SerialConfig:
    def __init__(self, baud_rate=9600, port="COM1", time_out=1, sleep_time=.07):
        """
        A class to store serial communication info.
        :param baud_rate:   communication baud rate. By default 9600.
        :param port:    the port where the serial device is connected to. By default 'COM1'
        :param time_out:    communiaction timeout in seconds. By default 1 second.
        """
        self.baud_rate = baud_rate
        self.port = port
        self.timeout = time_out  # 1 segundo de timeout
        self.sleep_time = sleep_time


class LoadConfig:
    def __init__(self, discharge_voltage=48.0, channels=(1,)):
        self.discharge_voltage = discharge_voltage
        self.channels = channels

    def __str__(self):
        pass


class ElectronicLoad:
    def __init__(self, config_serial: SerialConfig, config_load: LoadConfig, Ts=1, measurement_folder_path="../data/",
                 measurement_file_name="fileName"):
        # Measurement variables
        self.Ts = Ts

        # The path where measurements will be stored
        self.measurement_folder_path = measurement_folder_path
        self.measurement_file_name = measurement_file_name
        self.measurement_file_path = self.measurement_folder_path + self.measurement_file_name + ".csv"
        print('Data will be saved to:\n', self.measurement_file_path)

        # Serial communication handlers
        self.serial = serial.Serial()
        self.serial.baudrate = config_serial.baud_rate
        self.serial.port = config_serial.port
        self.serial.timeout = config_serial.timeout
        self.serial_sleep_time = config_serial.sleep_time

        # Set Load Config
        self.load = config_load

        # Create file where measured values will be stored. The file contains a header only.
        pd.DataFrame(columns=self.create_header()).to_csv(self.measurement_file_path, index=False)

        # Initialize serial communication
        self.beginCommunication()

    def create_header(self):
        header = ['t']
        for channel in self.load.channels:
            header.append('V CH' + str(channel))
            header.append('I CH' + str(channel))
        return header

    def beginCommunication(self):
        # Try opening the serial port
        try:
            self.serial.open()

        except Exception as e:
            print("Cannot open serial port: " + str(e))
            sys.exit(1)

        # Clean buffer and check if everything is alright
        if self.serial.is_open:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            print("Serial port has been initialized successfully!\n",
                  "Connected to port: " + str(self.serial.port))
        else:
            print("Cannot open serial port.")
            sys.exit(1)

    def setup(self):
        for channel in self.load.channels:
            cmd = 'hello'
            self._send(cmd)

    def _request(self, cmd):
        to_send = bytes(cmd + "\n", 'utf-8')
        self.serial.write(to_send)
        time.sleep(self.serial_sleep_time)  # FIXME this takes too much time, what's the real solution?
        out = ''
        while self.serial.in_waiting > 0:
            out = self.serial.readline().decode("utf-8")[0:-2]
        if out != '':
            return out
        else:
            return "Timeout"

    def _send(self, cmd):
        to_send = bytes(cmd + "\n", 'utf-8')
        self.serial.write(to_send)
        time.sleep(self.serial_sleep_time)  # FIXME this takes too much time, what's the real solution?

    def read_voltage(self):
        #channels = self.load.channels
        channels = [1]  # FIXME a trick
        meas = [0] * len(channels)
        for i, channel in enumerate(channels):
            self._send('CHAN ' + str(channel))
            meas[i] = self._request("MEAS:VOLT?")
        return meas

    def read_current(self):
        channels = self.load.channels
        meas = [0] * len(channels)
        for i, channel in enumerate(channels):
            self._send('CHAN ' + str(channel))
            meas[i] = self._request("MEAS:CURR?")
        return meas

    def set_current(self, val):
        channels = self.load.channels
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT OFF; FUNC CURR')
            self._send('CURR:RANG MAX')
            self._send('CURR ' + str(val))
            self._send('INPUT ON')
        return

    def turn_all_input_on(self):
        channels = (1, 2, 3)
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT ON')
        return

    def turn_all_input_off(self):
        channels = (1, 2, 3)
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT OFF')
        return

    def periodic_measurement(self, sample_time=1):
        """
        Measure every sample_time seconds the voltage and current of the channels specified by the
        load object
        :param sample_time: the sample time in seconds
        :return:
        """
        channels = self.load.channels
        # Initialize first values and append
        t0 = time.time()
        t0_global = t0

        # Iterate until user press ctrl+c or voltage is above discharge voltage
        while True:
            t1 = time.time()
            if t1 - t0 >= sample_time:
                t = t1 - t0_global
                data = {'t': [t]}
                voltage_list = self.read_voltage()*3    # FIXME a trick
                current_list = self.read_current()
                for channel, voltage, current in zip(channels, voltage_list, current_list):
                    data['V CH' + str(channel)] = [voltage]
                    data['I CH' + str(channel)] = [current]
                df = pd.DataFrame(data)
                print(df)
                df.to_csv(self.measurement_file_path, index=None, header=False, mode='a')

                if float(voltage_list[0]) <= self.load.discharge_voltage:
                    break
                t0 = time.time()
        return
