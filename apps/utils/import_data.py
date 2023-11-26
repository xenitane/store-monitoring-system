import csv
import os
import threading
import time
from datetime import datetime, timezone
from multiprocessing import Process

from decouple import config
from tqdm import tqdm

from apps.models import *
from .is_importing import set_is_importing

BUSINESS_HOURS_CSV_PATH = config("BUSINESS_HOURS_CSV_PATH")
STORES_CSV_PATH = config("STORES_CSV_PATH")
TIMEZONES_CSV_PATH = config("TIMEZONES_CSV_PATH")


def clear_database():
    """
    Erases all store records from the database.

    This function deletes all Store objects from the database. This is typically used to clear out old data before importing new data.
    """
    Store.objects.all().delete()
    BusinessHours.objects.all().delete()
    Timezone.objects.all().delete()


def parse_timestamp(timestamp_str):
    """
    Converts a timestamp string into a datetime object.

    Args:
        timestamp_str (str): The timestamp string to convert.

    Returns:
        datetime: The parsed datetime object.

    Raises:
        ValueError: If the timestamp string format is not recognized.
    """
    timestamp_formats = ["%Y-%m-%d %H:%M:%S.%f %Z", "%Y-%m-%d %H:%M:%S %Z"]

    for timestamp_format in timestamp_formats:
        try:
            timestamp_utc = datetime.strptime(timestamp_str, timestamp_format)
            return timestamp_utc
        except ValueError:
            pass

    raise ValueError(f"Timestamp format not recognized: {timestamp_str}")


def load_csv_data(csv_path, model, create_objects):
    """
    Loads CSV data into the database.

    Args:
        csv_path (str): The path to the CSV file.
        model (Model): The model class corresponding to the CSV data.
        create_objects (function): A function that takes a list of CSV data rows and returns a list of corresponding model objects.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: '{csv_path}'")

    with open(csv_path, "r") as csv_file:
        csv_data = csv.reader(csv_file)
        next(csv_data)  # Skip the header row
        objects = create_objects(csv_data)
        model.objects.bulk_create(objects, batch_size=100000)


def load_db_from_csv(store_csv_path, business_hours_csv_path, timezone_csv_path):
    """
    Loads data from CSV files into the database.

    This function reads data from three CSV files, stores, business hours, and timezones,
    and imports it into the database. It uses a separate process for each CSV file to improve performance.

    Args:
        store_csv_path (str): The path to the stores CSV file.
        business_hours_csv_path (str): The path to the business hours CSV file.
        timezone_csv_path (str): The path to the timezones CSV file.

    Raises:
        FileNotFoundError: If any of the CSV files do not exist.
    """

    # Check if the CSV files exist
    if not os.path.isfile(store_csv_path):
        raise FileNotFoundError(f"Store CSV file not found: {store_csv_path}")
    if not os.path.isfile(business_hours_csv_path):
        raise FileNotFoundError(
            f"Business hours CSV file not found: {business_hours_csv_path}"
        )
    if not os.path.isfile(timezone_csv_path):
        raise FileNotFoundError(f"Timezones CSV file not found: {timezone_csv_path}")

    # Import data from CSV files in parallel using multiple processes
    print("Importing data...")
    set_is_importing(True)
    start_time = time.time()

    clear_database()  # Remove existing data from the database before importing new data

    processes = [
        Process(
            target=load_csv_data,
            args=(store_csv_path, Store, create_store_objects),
        ),
        Process(
            target=load_csv_data,
            args=(
                business_hours_csv_path,
                BusinessHours,
                create_business_hours_objects,
            ),
        ),
        Process(
            target=load_csv_data,
            args=(timezone_csv_path, Timezone, create_timezone_objects),
        ),
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    end_time = time.time()
    elapsed_time = end_time - start_time
    set_is_importing(False)
    print(f"Data loaded successfully. Time taken: {elapsed_time:.2f} seconds")


def create_store_objects(csv_data):
    """
    Creates Store objects from a list of CSV data rows.

    This function iterates through the list of CSV data rows and creates corresponding Store objects.
    It converts the timestamp from UTC to the specified timezone and sets the is_active flag based on the store status.

    Args:
        csv_data (list): A list of CSV data rows.

    Returns:
        list: A list of Store objects.
    """

    store_objects = []
    csv_data = list(csv_data)
    total_rows = len(csv_data)

    for i, row in tqdm(
        enumerate(csv_data, 1), total=total_rows, desc="Processing stores"
    ):
        store, status, timestamp_utc = row

        # Parse the timestamp from UTC to the specified timezone
        timestamp_utc = parse_timestamp(timestamp_utc)
        timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

        # Convert status to 1 for 'active' and 0 for 'inactive'
        is_active = True if status.lower() == "active" else False

        # Create a Store object with the parsed data
        store_objects.append(
            Store(store=store, timestamp_utc=timestamp_utc, is_active=is_active)
        )

    return store_objects


def create_business_hours_objects(csv_data):
    """
    Creates BusinessHours objects from a list of CSV data rows.

    This function iterates through the list of CSV data rows and creates corresponding BusinessHours objects.
    It handles duplicate records by updating existing records instead of creating new ones.

    Args:
        csv_data (list): A list of CSV data rows.

    Returns:
        list: A list of BusinessHours objects.
    """

    business_hours_objects = []
    existing_records = {}  # Dictionary to store existing records by (store, day) tuple
    csv_data = list(csv_data)
    total_rows = len(csv_data)

    for i, row in tqdm(
        enumerate(csv_data, 1), total=total_rows, desc="Processing business hours"
    ):
        store, day, start_time_local, end_time_local = row
        day = int(day)  # Convert day to an integer

        # Check if a record with the same (store, day) already exists
        key = (store, day)
        existing_record = existing_records.get(key)

        if existing_record:
            # Update the existing record with the new start_time_local and end_time_local
            if start_time_local != "00:00:00":
                existing_record.start_time_local = datetime.strptime(
                    start_time_local, "%H:%M:%S"
                ).time()
            if end_time_local != "23:59:59":
                existing_record.end_time_local = datetime.strptime(
                    end_time_local, "%H:%M:%S"
                ).time()
        else:
            # Create a new BusinessHours object with the parsed data
            existing_record = BusinessHours(
                store=store,
                day=day,
                start_time_local=datetime.strptime(start_time_local, "%H:%M:%S").time(),
                end_time_local=datetime.strptime(end_time_local, "%H:%M:%S").time(),
            )

            # Add the new BusinessHours object to the list
            business_hours_objects.append(existing_record)

        # Update the existing_records dictionary
        existing_records[key] = existing_record

    return business_hours_objects


def create_timezone_objects(csv_data):
    """
    Creates Timezone objects from a list of CSV data rows.

    This function iterates through the list of CSV data rows and creates corresponding Timezone objects.
    It ensures that each store has only one corresponding Timezone object.

    Args:
        csv_data (list): A list of CSV data rows.

    Returns:
        list: A list of Timezone objects.
    """

    timezone_objects = []
    store_timezones = {}  # Dictionary to store timezones by store
    csv_data = list(csv_data)
    total_rows = len(csv_data)

    for i, row in tqdm(
        enumerate(csv_data, 1), total=total_rows, desc="Processing timezones"
    ):
        store, timezone_str = row

        # Check if a timezone has already been assigned to the store
        existing_timezone = store_timezones.get(store)

        if not existing_timezone:
            # Create a new Timezone object with the parsed data
            existing_timezone = Timezone(store=store, timezone_str=timezone_str)

            # Add the new Timezone object to the dictionary and list
            store_timezones[store] = existing_timezone
            timezone_objects.append(existing_timezone)

    return timezone_objects


def load_data():
    """
    Initiates the periodic loading of data from CSV files into the database.

    This function triggers a separate thread to repeatedly load data from CSV files into the database at hourly intervals.
    It ensures data integrity by setting the `is_importing_data` flag to True during the data import process.

    """

    load_db_from_csv(STORES_CSV_PATH, BUSINESS_HOURS_CSV_PATH, TIMEZONES_CSV_PATH)


def load_data_after_1_hour():
    """
    Continuously loads data into the database at hourly intervals.

    This function operates in an infinite loop, repeatedly launching a separate thread to load data from CSV files into the database.
    It introduces a one-hour delay between each data loading cycle to ensure data consistency and avoid overloading the system.

    """

    while True:
        # Create and start a process to load data
        process = Process(target=load_data)
        process.start()

        # Sleep for one hour before initiating the next data loading cycle
        time.sleep(3600)

        # Join the process to ensure it completes before proceeding
        process.join()


def import_data():
    """Starts a thread to load data into the database."""
    process = Process(target=load_data_after_1_hour)
    process.start()

    print("Data import process started. Data will be loaded every hour.")
