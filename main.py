from pyHS100 import SmartPlug
from datetime import datetime, timedelta
import time
import os
import pandas as pd
import argparse
import sys

sys.stdout.reconfigure(line_buffering=True)

# SmartPlug IPs
WP03 = "134.34.225.167"  # Light
WP04 = "134.34.225.135"  # Heater

growLight = SmartPlug(WP03)
heater = SmartPlug(WP04)

temp_increase = 2 # 6°C temp increase

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
        if df.empty:
            print("The latest CSV file is empty.")
            return None

        last_row = df.iloc[-1]

        # Access temperature values by position using .iloc
        last_temperature = float(last_row.iloc[3])
        last_temperature_2 = float(last_row.iloc[4])

        # Return the average of the two temperature values
        return (last_temperature + last_temperature_2) / 2

    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None


def save_target_temperature(temp):
    """Saves the target temperature to a file."""
    try:
        with open("/docker_temp/target_temp.txt", "w") as f:
            f.write(str(temp))
    except Exception as e:
        print(f"Error saving target temperature: {e}")


def load_target_temperature():
    """Loads the target temperature from a file."""
    try:
        with open("/docker_temp/target_temp.txt", "r") as f:
            return float(f.read())
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading target temperature: {e}")
        return None


def delete_target_temperature():
    """Deletes the target temperature file."""
    try:
        if os.path.exists("/docker_temp/target_temp.txt"):
            os.remove("/docker_temp/target_temp.txt")
    except Exception as e:
        print(f"Error deleting target temperature file: {e}")


def control_heater(directory):
    """
    Controls the heater based on the target temperature and current temperature.
    """
    current_temperature = read_last_temperature(directory)

    if current_temperature is None:
        print("Could not read current temperature. Heater off.")
        heater.turn_off()
        return

    target_temperature = load_target_temperature()

    print(f"Status: Current temperature: {current_temperature}, Target temperature: {target_temperature}")

    if target_temperature is None:
        target_temperature = current_temperature + temp_increase
        save_target_temperature(target_temperature)
        print(f"Target temperature set: {target_temperature}°C.")

    if current_temperature < target_temperature:
        print(f"Heating: Current temperature {current_temperature}°C. Target: {target_temperature}°C.")
        heater.turn_on()
    else:
        print(f"Holding temperature: {current_temperature}°C. Heater off.")
        heater.turn_off()


def execute_time_block(directory, start_time, end_time, block_type):
    """
    Executes the scheduled task for the given time block type.
    """
    match block_type:
        case "sleep":
            print("Sleeping during this block. Devices off.")
            growLight.turn_off()
            heater.turn_off()
            delete_target_temperature()
        case "wait":
            print("Waiting during this block. Light on, heater off.")
            growLight.turn_on()
            heater.turn_off()
            delete_target_temperature()
        case "heat":
            growLight.turn_on()
            control_heater(directory)
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
    #     "07:00-08:00": "wait",
    #     "08:00-08:30": "heat",
    #     "08:30-09:30": "wait",
    #     "09:30-10:30": "wait",
    #     "10:30-11:00": "heat",
    #     "11:00-12:00": "wait",
    #     "12:00-13:00": "wait",
    #     "13:00-13:30": "heat",
    #     "13:30-14:30": "wait",
    #     "14:30-15:30": "wait",
    #     "15:30-16:00": "heat",
    #     "16:00-17:00": "wait",
    #     "17:00-18:00": "wait",
    #     "18:00-18:30": "heat",
    #     "18:30-19:30": "wait",
    #     "19:30-07:00": "sleep"  # Overnight sleep
    # }

    schedule = {
        "10:20-10:35": "heat",  # 15 minutes of heating
        "10:35-10:50": "wait",  # 15 minutes of waiting
        "10:50-11:05": "heat",  # 15 minutes of heating
        "11:05-11:20": "wait",  # 15 minutes of waiting
        "11:20-11:35": "heat",  # 15 minutes of heating
        "11:35-11:50": "wait",  # 15 minutes of waiting
        "11:50-12:05": "heat",  # 15 minutes of heating
        "12:05-12:20": "wait",  # 15 minutes of waiting
        "12:20-12:35": "heat",  # 15 minutes of heating
        "12:35-12:50": "wait",  # 15 minutes of waiting
        "12:50-13:05": "heat",  # 15 minutes of heating
        "13:05-13:20": "wait",  # 15 minutes of waiting
        "13:20-13:30": "heat",  # Final heat phase
    }

    heater.turn_off()
    growLight.turn_off()

    last_block = None

    while True:
        current_time = datetime.now()

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
                print(f"Executing block: {block_type} ({start_str}-{end_str})")
                execute_time_block(directory, start_time, end_time, block_type)
                break

        time.sleep(20)  # Sleep to avoid tight looping

if __name__ == "__main__":
    main()