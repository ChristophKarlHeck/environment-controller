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

wait_time_seconds = 3600
check_temp_time = 60
heater_time = 30 

def read_last_temperature(directory):
    """
    Reads the last temperature from the latest P6*.csv file in the given directory.
    """
    try:
        # Find the latest P6*.csv file
        files = [f for f in os.listdir(directory) if f.startswith("P6") and f.endswith(".csv")]
        if not files:
            print("No P6*.csv files found.")
            return None

        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(directory, f)))

        # Read the last row of the CSV file
        df = pd.read_csv(os.path.join(directory, latest_file))
        last_row = df.iloc[-1]

        # Assuming the temperature is in the second column (index 1)
        last_temperature = float(last_row[1])
        last_temperature_2 = float(last_row[3])
        return (last_temperature + last_temperature_2)/2

    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None

def wait_for_temperature_or_time(directory, start_temperature, target_increase, max_time_minutes):
    """
    Waits until either the temperature has increased by the target amount
    or the maximum time has elapsed.
    """
    start_time = datetime.now()

    while True:
        current_temperature = read_last_temperature(directory)
        if current_temperature is None:
            time.sleep(check_temp_time)  # Retry after 1 minute
            continue

        if current_temperature >= start_temperature + target_increase:
            print(f"Temperature increased by {target_increase}°C.")
            break

        elapsed_time = (datetime.now() - start_time).total_seconds() / check_temp_time  # Minutes
        if elapsed_time >= max_time_minutes:
            print(f"Maximum time of {max_time_minutes} minutes reached. Proceeding to the next step.")
            break

        print(f"Current temperature: {current_temperature}°C. Elapsed time: {elapsed_time:.2f} minutes. Waiting...")
        time.sleep(check_temp_time)  # Check every minute

def experiment_cycle(directory):
    """
    Performs one cycle of the experiment.
    """
    print("Starting experiment cycle...")

    # Turn on the grow light
    growLight.turn_on()
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
    wait_for_temperature_or_time(directory, start_temperature, 6, heater_time)

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
