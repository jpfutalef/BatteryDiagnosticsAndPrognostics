from res.SerialCom import SerialConfig, LoadConfig, ElectronicLoad
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt


def experiment_current_profile(electronic_load: ElectronicLoad, current_profile, file_path, ts, t_offset=0.0):
    # initial time
    t0 = time.time() - t_offset
    t = t0

    # Iterate through each point
    for t1, c in current_profile:
        # Set current
        electronic_load.set_current(c)

        # Do stuff until reach next point
        while time.time() - t0 < t1 + t_offset:
            # Wait until ts seconds have been accomplished since last measurement
            while time.time() - t <= ts:
                pass

            # Time the measurement is made
            t = time.time()

            # Measure voltage
            volt = float(electronic_load.read_voltage_raw())

            # Read current from each channel
            electronic_load.set_channel(1)
            curr_1 = float(electronic_load.read_current_raw())

            electronic_load.set_channel(2)
            curr_2 = float(electronic_load.read_current_raw())

            electronic_load.set_channel(3)
            curr_3 = float(electronic_load.read_current_raw())

            # Put into data frame and save
            with open(file_path, 'a') as file_handle:
                data_dict = {'t': [t - t0],
                             'V': [volt],
                             'I1': [curr_1],
                             'I2': [curr_2],
                             'I3': [curr_3]}
                df = pd.DataFrame(data_dict)
                print(df)
                df.to_csv(file_handle, index=None, header=False)
                file_handle.close()

            # Check if continue
            if volt <= electronic_load.load.discharge_voltage:
                return False, t0 + time.time(), data_dict

    return True, t - t0, data_dict


# Profiles
point_list_1 = [(900, 27), (900+120, 18), (900+120*2, 27), (900+120*3, 18)]     # Pola profile
point_list_2 = [(2, 30), (4, 10)]       # experiment profile

# Setup experiment variables
ts = 1.0
loop = True
points = point_list_2
discharge_voltage = 42.5

# Name of the experiment
name = "discharge_with_current_profile_27-11-19"

if __name__ == "__main__":
    # Setup serial port, load profiles, etc
    conf = SerialConfig(port="COM5")
    load = LoadConfig(discharge_voltage=discharge_voltage, channels=(1, 2, 3))

    # Instantiate Electronic load and set
    file_header = ('t', 'V', 'I1', 'I2', 'I3')
    N3300A = ElectronicLoad(conf, load, measurement_file_name=name)

    # Create file where measured values will be stored. The file contains a header only.
    pd.DataFrame(columns=file_header).to_csv(N3300A.measurement_file_path, index=False)

    # Turn off to ensure clean starting
    N3300A.turn_all_input_off()
    input("Press enter to start...")

    # Do experiment
    cum_current = 0.0

    # Zone 1
    print("########### ZONE 1 #############")
    N3300A.set_current(27)
    t0 = time.time()
    t = t0

    while cum_current < 35*3600:
        # Wait until ts seconds have been accomplished since last measurement
        while time.time() - t <= ts:
            pass

        # Time
        t = time.time()

        # Measure voltage
        volt = float(N3300A.read_voltage_raw())

        # Check if continue
        if volt <= N3300A.load.discharge_voltage:
            N3300A.turn_all_input_off()
            break

        # Read current from each channel
        N3300A.set_channel(1)
        curr_1 = float(N3300A.read_current_raw())

        N3300A.set_channel(2)
        curr_2 = float(N3300A.read_current_raw())

        N3300A.set_channel(3)
        curr_3 = float(N3300A.read_current_raw())

        cum_current += curr_1 + curr_2 + curr_3

        # Put into data frame and save
        with open(N3300A.measurement_file_path, 'a') as file_handle:
            data_dict = {'t': [t - t0],
                         'V': [volt],
                         'I1': [curr_1],
                         'I2': [curr_2],
                         'I3': [curr_3]}
            df = pd.DataFrame(data_dict)
            print(df)
            df.to_csv(file_handle, index=None, header=False)
            file_handle.close()

    # Zone 2
    print("########### ZONE 2 #############")
    t_off = t - t0
    if loop:
        continue_experiment = True
        while continue_experiment:
            continue_experiment, t_off, data_dict = experiment_current_profile(N3300A, points,
                                                                               N3300A.measurement_file_path,
                                                                               ts, t_offset=t_off)
            cum_current += data_dict["I1"][0] + data_dict["I2"][0] + data_dict["I3"][0]
            if cum_current >= 80*3600:
                break
    else:
        experiment_current_profile(N3300A, points, N3300A.measurement_file_path, ts)

    # Zone 3
    print("########### ZONE 3 #############")
    N3300A.set_current(27)
    t0 = time.time() - t_off
    t = t0

    while True:
        # Wait until ts seconds have been accomplished since starting measurement
        while time.time() - t <= ts:
            pass

        # Time
        t = time.time()

        # Measure voltage
        volt = float(N3300A.read_voltage_raw())

        # Check if continue
        if volt <= N3300A.load.discharge_voltage:
            N3300A.turn_all_input_off()
            break

        # Read current from each channel
        N3300A.set_channel(1)
        curr_1 = float(N3300A.read_current_raw())

        N3300A.set_channel(2)
        curr_2 = float(N3300A.read_current_raw())

        N3300A.set_channel(3)
        curr_3 = float(N3300A.read_current_raw())

        cum_current += curr_1 + curr_2 + curr_3

        # Put into data frame and save
        with open(N3300A.measurement_file_path, 'a') as file_handle:
            data_dict = {'t': [t - t0],
                         'V': [volt],
                         'I1': [curr_1],
                         'I2': [curr_2],
                         'I3': [curr_3]}
            df = pd.DataFrame(data_dict)
            print(df)
            df.to_csv(file_handle, index=None, header=False)
            file_handle.close()

    # Turn all inputs off
    N3300A.turn_all_input_off()

    # Plot results
    with open(N3300A.measurement_file_path, 'r') as csv_file:
        df = pd.read_csv(csv_file)

        t = df.t.values
        v = df.V.values
        i1 = df.I1.values
        i2 = df.I2.values
        i3 = df.I3.values

        # current
        plt.subplot(131)
        plt.plot(t, i1)
        plt.xlabel('Time [s]')
        plt.ylabel('Current [A]')
        plt.title('Current channel 1')

        plt.subplot(132)
        plt.plot(t, i2)
        plt.xlabel('Time [s]')
        plt.ylabel('Current [A]')
        plt.title('Current channel 2')

        plt.subplot(133)
        plt.plot(t, i3)
        plt.xlabel('Time [s]')
        plt.ylabel('Current [A]')
        plt.title('Current channel 3')

        plt.show()

        # voltage
        plt.plot(t, v)
        plt.xlabel('Time [s]')
        plt.ylabel('Current [A]')
        plt.title('Battery pack voltage')

        plt.show()

    # sys.exit(0)
