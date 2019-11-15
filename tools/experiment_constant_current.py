from res.SerialCom import SerialConfig, LoadConfig, ElectronicLoad
import sys

if __name__ == "__main__":
    name = str(input('Experiment filename?'))
    conf = SerialConfig(port="COM3")
    load = LoadConfig(discharge_voltage=50.0, channels=(1,2,3))
    N3300A = ElectronicLoad(conf, load, measurement_file_name=name)
    N3300A.set_current(10.0, channels=(1, 2, 3))
    N3300A.periodic_measurement_parallel(sample_time=1.0, channels=(1, 2, 3))
    N3300A.turn_all_input_off()
    sys.exit(0)
