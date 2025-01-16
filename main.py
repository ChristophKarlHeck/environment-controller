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

def execute_time_block(directory, block_type):
    """
    Executes the scheduled task for the given time block type.
    """
    match block_type:
        case "sleep":
            print("Sleeping during this block. Devices off.")
            growLight.turn_off()
            heater.turn_off()
        case "wait":
            print("Waiting during this block. Light on, heater off.")
            growLight.turn_on()
            heater.turn_off()
        case "heat":
            print("Heating block started.")
            start_temperature = read_last_temperature(directory)
            if start_temperature is not None:
                wait_for_temperature_or_time(directory, start_temperature, 6, 30, 20)
            heater.turn_off()
            print("Heating block ended.")
        case _:
            print("Invalid block type.")

def main():
    parser = argparse.ArgumentParser(description="Run the experiment with fixed time blocks.")
    parser.add_argument("--directory", type=str, required=True, help="Directory containing P6*.csv files.")
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    # Define the schedule with block types
    # schedule = {
    #     "08:00-09:00": "wait",
    #     "09:00-09:30": "heat",
    #     "09:30-10:30": "wait",
    #     "10:30-11:30": "wait",
    #     "11:30-12:00": "heat",
    #     "12:00-13:00": "wait",
    #     "13:00-14:00": "wait",
    #     "14:00-14:30": "heat",
    #     "14:30-15:30": "wait",
    #     "15:30-16:30": "wait",
    #     "16:30-17:00": "heat",
    #     "17:00-18:00": "wait",
    #     "18:00-19:00": "wait",
    #     "19:00-19:30": "heat",
    #     "19:30-20:30": "wait"
    #     "20:30-08:00": "sleep"  # Overnight sleep
    # }

    schedule = {
        "14:50-14:55": "wait",
        "14:55-15:20": "heat",
        "15:20-15:25": "wait",
        "15:25-15:30": "wait",
        "15:30-15:55": "heat",
        "15:55-16:00": "wait",
        "16:00-14:50": "sleep"  # Overnight sleep
    }

    heater.turn_off()
    growLight.turn_off()

    while True:
        current_time = datetime.now()
        current_hour_minute = current_time.strftime("%H:%M")

        for time_range, block_type in schedule.items():
            start_str, end_str = time_range.split("-")
            start_time = datetime.strptime(start_str, "%H:%M").replace(
                year=current_time.year, month=current_time.month, day=current_time.day
            )
            end_time = datetime.strptime(end_str, "%H:%M").replace(
                year=current_time.year, month=current_time.month, day=current_time.day
            )

            if end_time < start_time:
                end_time += timedelta(days=1)  # Handle overnight case

            if start_time <= current_time < end_time:
                execute_time_block(directory, block_type)
                break

        # Sleep for a minute to avoid tight looping
        time.sleep(20)

if __name__ == "__main__":
    main()
