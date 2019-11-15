# Comunicacion serial para tomar mediciones de descarga

import serial
import time
import sys
import signal
import numpy as np
import pandas as pd

# User defined variables
serial_port = 'COM1'


# Useful funs
def signal_handler(signal, frame):
    print('\nTerminando...')


# Classes
class SerialConfig:
    def __init__(self, baud_rate=9600, port="COM1", time_out=1):
        """
        A class to store serial communication info.
        :param baud_rate:   communication baud rate. By default 9600.
        :param port:    the port where the serial device is connected to. By default 'COM1'
        :param time_out:    communiaction timeout in seconds. By default 1 second.
        """
        self.baud_rate = baud_rate
        self.port = port
        self.timeout = time_out  # 1 segundo de timeout


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
        self.V = []
        self.I = []
        self.t = []

        # The path where measurements will be stored
        self.measurement_folder_path = measurement_folder_path
        self.measurement_file_name = measurement_file_name

        self.measurement_file_path = self.measurement_folder_path + self.measurement_file_name + ".csv"
        print('Data will be saved to:\n', self.measurement_file_path)

        # Create file where measured values will be stored. The file contains a header only.
        pd.DataFrame(columns=('t', 'V', 'I')).to_csv(self.measurement_file_path)

        # Serial communication handlers
        self.serial = serial.Serial()
        self.serial.baudrate = config_serial.baud_rate
        self.serial.port = config_serial.port
        self.serial.timeout = config_serial.timeout

        # Set Load Config
        self.load = config_load

        # Initialize serial communication
        self.beginCommunication()

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
            cmd = 'hola'
            self._send(cmd)

    def _request(self, cmd):
        toSend = bytes(cmd + "\n", 'utf-8')
        self.serial.write(toSend)
        time.sleep(self.Ts / 10)
        out = ''
        while self.serial.in_waiting > 0:
            # out = self.serial.readline().decode("utf-8")
            out = self.serial.readline().decode("utf-8")[0:-2]  # TODO posiblemente mejor readline?
        if out != '':
            return out
        else:
            return "Timeout"

    def _send(self, cmd):
        toSend = bytes(cmd + "\n", 'utf-8')
        self.serial.write(toSend)
        time.sleep(self.Ts / 10)

    def read_voltage(self):
        # Leer voltaje desde el equipo
        meas = self._request("MEAS:VOLT?")
        return meas

    def read_current(self):
        # Leer corriente desde el equipo
        meas = self._request("MEAS:CURR?")
        return meas

    def read_current_parallel(self, channels=(1,)):
        meas = [0]*len(channels)
        for i, channel in enumerate(channels):
            self._send('CHAN ' + str(channel))
            meas[i] = self.read_current()
        return meas

    def read_voltage_current(self, channels=(1,)):
        meas = self._request('MEAS:ARR:CURR?')
        print()
        return

    def set_current(self, val, channels=(1,)):
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT OFF; FUNC CURR')
            self._send('CURR:RANG MAX')
            self._send('CURR ' + str(val))
            self._send('INPUT ON')
        return

    def turn_all_input_on(self, channels=(1,2,3)):
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT ON')
        return

    def turn_all_input_off(self, channels=(1,2,3)):
        for channel in channels:
            self._send('CHAN ' + str(channel))
            self._send('INPUT OFF')
        return

    def set_load_config(self, config, method='loop'):
        # TODO Definir curva de carga y configurar a la maquina
        return 0

    def periodic_measurement(self, sample_time=1):
        # Realizar mediciones constantes cada sample_time segundos

        # Set signal handler
        signal.signal(signal.SIGINT, signal_handler)

        # Initialize first values and append
        t0 = time.time()
        t0_global = t0

        # Iterate until user press ctrl+c or voltage is above discharge voltage
        V = 9999999999999.9
        while True:
            t1 = time.time()
            if t1 - t0 >= sample_time:
                t = t1 - t0_global
                V = self.read_voltage()
                I = self.read_current()
                data = {'t': [t],
                        'V': [V],
                        'I': [I]}
                df = pd.DataFrame(data)
                print(df)
                df.to_csv(self.measurement_file_path, index=None, header=False, mode='a')
                t0 = time.time()
            if float(V) <= self.load.discharge_voltage:
                break

    def periodic_measurement_parallel(self, sample_time=1, channels=(1,)):
        # Realizar mediciones constantes cada sample_time segundos

        # Set signal handler
        signal.signal(signal.SIGINT, signal_handler)

        # Initialize first values and append
        t0 = time.time()
        t0_global = t0

        # Iterate until user press ctrl+c or voltage is above discharge voltage
        V = 9999999999999.9
        while True:
            t1 = time.time()
            if t1 - t0 >= sample_time:
                t = t1 - t0_global
                V = self.read_voltage()
                data = {'t': [t],
                        'V': [V]}
                I = self.read_current_parallel(channels=channels)
                for channel, current in zip(channels, I):
                    data['I (Chan '+str(channel)+')'] = [current]
                df = pd.DataFrame(data)
                print(df)
                df.to_csv(self.measurement_file_path, index=None, header=False, mode='a')
                t0 = time.time()
            if float(V) <= self.load.discharge_voltage:
                break

    def pack_data(self):
        data = {'V': self.V,
                'I': self.I,
                't': self.t}
        df = pd.DataFrame(data)
        print('Obtained data frame:\n', df)
        df.to_csv(r'../data/labMeasurements/measurement.csv', index=None, header=True)


if __name__ == "__main__":
    conf = SerialConfig(port="COM3")
    load = LoadConfig()
    N3300A = ElectronicLoad(conf, load)
    # N3300A.set_current(2.0, channels=(1, 2, 3))
    print(N3300A.read_current_parallel(channels=(1,2,3)))
    N3300A.turn_all_input_off()
    sys.exit(0)
