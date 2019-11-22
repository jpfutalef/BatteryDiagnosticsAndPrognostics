from res.SerialCom import SerialConfig, LoadConfig, ElectronicLoad
import sys

if __name__ == "__main__":
    # Name of the experiment
    name = str(input('Experiment filename?'))

    # Setup serial port, load profiles, etc
    conf = SerialConfig(port="COM3")
    load = LoadConfig(discharge_voltage=50.0, channels=(1, 2, 3))

    # Instantiate Electronic load and set
    N3300A = ElectronicLoad(conf, load, measurement_file_name=name)

    # Do experiment
    N3300A.set_current(5.0)
    N3300A.periodic_measurement(sample_time=1.0)

    # Finish
    N3300A.turn_all_input_off()
    sys.exit(0)
