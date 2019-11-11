# Comunicacion serial para tomar mediciones de descarga

import serial
import time
import sys, signal
import numpy as np
import pandas as pd

serial_port = 'COM1'

def signal_handler(signal, frame):
    print('\nTerminando...')
    sys.exit(0)

class SerConfig():
    def __init__(self):
        self.baudrate = 9600
        self.port = "COM1"
        self.timeout = 1  # 1 segundo de timeout


class N3000():
    def __init__(self, SerConfig, Ts=1):
        self.Ts = Ts
        self.V = []
        self.I = []
        self.t = []

        self.Ser = serial.Serial()
        self.Ser.baudrate = SerConfig.baudrate
        self.Ser.port = SerConfig.port
        self.Ser.timeout = SerConfig.timeout

        try:
            self.Ser.open()
        except Exception as e:
            print("Error abriendo puerto serial: "+str(e))
            exit()

        if self.Ser.isOpen():
            self.Ser.flushInput()
            self.Ser.flushOutput()
            print("Puerto serial inicializado con exito")
        else:
            print("No se pudo abrir el puerto serial")


    def read_v(self):
        # Leer voltaje desde el equipo
        meas = self._request("MEAS:VOLT:ACDC?")
        return meas

    def read_i(self):
        # Leer corriente desde el equipo
        meas = self._request("MEAS:CURR:ACDC?")
        return meas

    def _request(self, cmd):
        self.Ser.write(cmd+"\r\n")
        time.sleep(self.Ts/10)
        out = ''
        while self.Ser.inWaiting() > 0:
            out += self.Ser.read(1)
        if out != '':
            return out
        else:
            return "Timeout"

    def set_mode(self): # TODO Configurar entre modo de carga y descarga

    def set_load_config():
        # TODO Definir curva de carga y configurar a la maquina
        return 0

    def begin(self):
        # Realizar mediciones constantes cada Ts segundos
        dummy = 1 # TODO buscar como parar el loop por medición obtenida
        self.t_inicial = time.time()
        t0 = self.t_inicial
        idx = 0
        while dummy:
            t1 = time.time()
            if t1-t0 >= self.Ts:
                t0 = time.time()
                self.V.append(self.read_v())
                self.I.append(self.read_i())
                self.t.append(t1 - self.t_inicial)
                idx = idx + 1
            signal.signal(signal.SIGINT, signal_handler)

    def pack_data(self):
        data = {'V': self.V,
                'I': self.I,
                't': self.t}
        df = pd.DataFrame(data)
        df.to_csv(r'Measurement\export.csv', index=None, header=True)



if __name__ == "__main__":
    conf = SerConfig()
    Meas = N3000(SerConfig)
    Meas.set_load_config()
    Meas.begin()
    Meas.pack_data()
    sys.exit(0)
