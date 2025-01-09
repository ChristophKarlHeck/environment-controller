from pyHS100 import SmartPlug
from datetime import datetime, timedelta
import time
import os
import pandas as pd
import argparse

# SmartPlug IPs
WP03 = "134.34.225.167"  # Light
WP04 = "134.34.225.135"  # Heater

growLight = SmartPlug(WP03)
heater = SmartPlug(WP04)

def read_last_temperature(directory):
    """
    Reads the last temperature from the latest P6*.csv file in the given directory.

    Args:
        directory (str): Path to the directory containing P6*.csv files.

    Returns:
        float: The average of the last two temperature values from the file, or None if an error occurs.
    """
    try:
        # Find the latest P6*.csv file
        files = [f for f in os.listdir(directory) if f.startswith("P6") and f.endswith(".csv")]
        if not files:
            print("No P6*.csv files found.")
            return None

        # Identify the latest file based on creation time
        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(directory, f)))

        # Read the file and get the last row
        df = pd.read_csv(os.path.join(directory, latest_file))
        last_row = df.iloc[-1]

        # Access temperature values by position using .iloc
        last_temperature = float(last_row.iloc[3])
        last_temperature_2 = float(last_row.iloc[4])

        # Return the average of the two temperature values
        return (last_temperature + last_temperature_2) / 2

    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None


def wait_for_temperature_or_time(directory, start_temperature, target_increase, max_duration_minutes, check_temp_time):
    """
    Waits until either the temperature has increased by the target amount
    or the maximum time has elapsed.
    """

    target_temperature = start_temperature + target_increase 
    print(f"Starting 30-minute cycle. Target temperature: {target_temperature}°C.")
    start_time = datetime.now()

    while True:
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds() / 60  # Convert to minutes

        # Check if 30 minutes have passed
        if elapsed_time >= max_duration_minutes:
            print(f"30 minutes elapsed. Turning off the heater.")
            break

        # Read the current temperature
        current_temperature = read_last_temperature(directory)
        if current_temperature is None:
            time.sleep(check_temp_time)
            continue

        # Heat to the target temperature if not reached
        if current_temperature < target_temperature:
            print(f"Heating: Current temperature {current_temperature}°C. Target: {target_temperature}°C.")
            heater.turn_on()
        else:
            print(f"Holding temperature: {current_temperature}°C. Heater off.")
            heater.turn_off()

        print(f"Current temperature: {current_temperature}°C. Elapsed time: {elapsed_time:.2f} minutes. Waiting...")
        time.sleep(check_temp_time)

def experiment_cycle(directory):
    """
    Performs one cycle of the experiment.
    """
    print("Starting experiment cycle...")

    wait_time_seconds = 3600 # 3600 wait 1h
    check_temp_time = 60 # 60 check temp every minute
    heater_time = 30 # minutes to heat up and hold target temp
    temp_increase = 6 # 6 C°

    # Turn on the grow light
    growLight.turn_on()
    #heater.turn_off()
    print("Grow light turned on.")

    # Wait for 1 hour
    time.sleep(wait_time_seconds)

    # Turn on the heater
    heater.turn_on()
    print("Heater turned on.")

    # Get the starting temperature
    start_temperature = read_last_temperature(directory)
    if start_temperature is None:
        print("Could not read the starting temperature. Turning off heater.")
        heater.turn_off()
        return

    # Wait for either 30 minutes or a temperature increase of 6°C
    wait_for_temperature_or_time(directory, start_temperature, temp_increase, heater_time, check_temp_time)

    # Turn off the heater
    heater.turn_off()

    print("Heater turned off.")

    # Wait for 1 hour
    time.sleep(wait_time_seconds)

    
def main():
    """
    Main function to run the experiment daily from 8:00 to 20:30.
    """
    parser = argparse.ArgumentParser(description="Run the experiment with temperature monitoring.")
    parser.add_argument("--directory", type=str, required=True, help="Directory containing P6*.csv files.")
    args = parser.parse_args()

    heater.turn_off()
    growLight.turn_off()

    directory = os.path.abspath(args.directory)
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    while True:
        current_time = datetime.now()

        # Check if the current time is within the active period (8:00 to 20:30)
        start_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
        end_time = current_time.replace(hour=20, minute=30, second=0, microsecond=0)

        if start_time <= current_time <= end_time:
            experiment_cycle(directory)
        else:
            # Turn off devices outside active period
            growLight.turn_off()
            heater.turn_off()
            print("Outside active period. Devices turned off.")

            # Wait until the next start time
            if current_time > end_time:
                next_start = start_time + timedelta(days=1)
            else:
                next_start = start_time

            sleep_duration = (next_start - current_time).total_seconds()
            print(f"Sleeping for {sleep_duration / 3600:.2f} hours until 8:00...")
            time.sleep(sleep_duration)

if __name__ == "__main__":
    main()
