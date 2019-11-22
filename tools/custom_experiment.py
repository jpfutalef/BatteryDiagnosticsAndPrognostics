from res.SerialCom import SerialConfig, LoadConfig, ElectronicLoad
import sys
import time
import pandas as pd


def experiment_current_profile(electronic_load: ElectronicLoad, current_profile, file_path, ts):
    # initial time
    t0 = time.time()

    # Iterate through each point
    for t1, c in current_profile:
        # Set current
        electronic_load.set_current(c)

        # Do stuff until reach next point
        while time.time() - t0 < t1:
            # Time the measurement is made
            t = time.time()

            # Measure voltage
            volt = electronic_load.read_voltage_raw()

            # Check if continue
            if volt <= electronic_load.load.discharge_voltage:
                return False

            # Read current from each channel
            electronic_load.set_channel(1)
            curr_1 = electronic_load.read_current_raw()

            electronic_load.set_channel(2)
            curr_2 = electronic_load.read_current_raw()

            electronic_load.set_channel(3)
            curr_3 = electronic_load.read_current_raw()

            # Put into data frame and save
            with open(file_path, 'a') as file_handle:
                data_dict = {'t': t,
                             'V': volt,
                             'I1': curr_1,
                             'I2': curr_2,
                             'I3': curr_3}
                df = pd.DataFrame(data_dict)
                print(df)
                df.to_csv(file_handle, index=None, header=False)
                file_handle.close()

            # Wait until ts seconds have been accomplished since starting measurement
            while time.time() - t <= ts:
                pass

    return True


point_list = [(10, 30), (20, 20), (30, 10), (40, 30)]

if __name__ == "__main__":
    # Name of the experiment
    name = str(input('Experiment filename?'))

    # Setup serial port, load profiles, etc
    conf = SerialConfig(port="COM3")
    load = LoadConfig(discharge_voltage=50.0, channels=(1, 2, 3))

    # Instantiate Electronic load and set
    file_header = ('t', 'V', 'I1', 'I2', 'I3')
    N3300A = ElectronicLoad(conf, load, measurement_file_name=name, header=file_header)

    # Do experiment
    ts = 1.0
    loop = True

    if loop:
        while experiment_current_profile(N3300A, point_list, N3300A.measurement_file_path, ts):
            pass
    else:
        experiment_current_profile(N3300A, point_list, N3300A.measurement_file_path, ts)

    # Finish
    N3300A.turn_all_input_off()
    sys.exit(0)
