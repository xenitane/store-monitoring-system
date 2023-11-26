import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from itertools import groupby
from operator import itemgetter

import pytz

from apps.apps import StoremonitoringsystemConfig
from apps.models import Store, StoreReport

from .business_hours import get_business_hours_by_store

# Number of intervals per hour for time granularity
INTERVALS_PER_HOUR = 4

# Dictionary to store date-weekday mapping
date_weekday_mapping = {}


def calculate_date_weekday_mapping():
    """
    Creates a dictionary mapping week days to corresponding dates based on the current timestamp.

    This function iterates through the days of the week, starting with the current day, and calculates
    the corresponding dates based on the current timestamp. It stores these date-weekday mappings in a dictionary.

    Returns:
        dict: A dictionary mapping week days to corresponding dates.
    """

    current_weekday = StoremonitoringsystemConfig.current_timestamp.weekday()

    # Iterate through the days of the week, starting with the current day
    for day in range(7):
        # Calculate the corresponding date for the current day and store it in the dictionary
        date = (
            StoremonitoringsystemConfig.current_timestamp - timedelta(days=day)
        ).date()
        date_weekday_mapping[(current_weekday - day) % 7] = date

    return date_weekday_mapping


def get_weekday(item):
    """
    Retrieves the weekday from an observation item.

    This function extracts the datetime object from the observation item and returns its weekday.

    Args:
        item (tuple): An observation item containing a date and a timestamp.

    Returns:
        int: The weekday of the date in the observation item.
    """

    observation_date = item[1]
    weekday = observation_date.weekday()

    return weekday


def group_observations_by_date(observations):
    """
    Groups observations by their corresponding weekdays.

    This function utilizes the `groupby` function from the `itertools` module to group observations
    based on their weekdays. It returns a dictionary where each key represents a weekday and
    the corresponding value is a list of observations for that weekday.

    Args:
        observations (list): A list of observation items.

    Returns:
        dict: A dictionary mapping weekdays to lists of observations for those weekdays.
    """

    weekday_groups = groupby(observations, key=get_weekday)
    grouped_observations = {weekday: list(group) for weekday, group in weekday_groups}

    return grouped_observations


def filter_recent_observations(observations, current_timestamp):
    """
    Filters observations to include only those that occurred within the past week.

    This function removes observations that are older than one week from the provided list of observations.
    It uses the current timestamp as a reference point and compares the observation timestamps to a date one week ago.
    Only observations with timestamps on or after the one-week-ago date are retained.

    Args:
        observations (list): A list of observation items.
        current_timestamp (datetime): The current timestamp.

    Returns:
        list: A filtered list of observation items containing only recent observations.
    """

    one_week_ago = current_timestamp - timedelta(days=7)
    recent_observations = []

    for observation in observations:
        observation_timestamp = observation[1]
        if observation_timestamp.replace(tzinfo=pytz.UTC) >= one_week_ago.replace(
            tzinfo=pytz.UTC
        ):
            recent_observations.append(observation)

    return recent_observations


def generate_time_intervals(start, end):
    """
    Generates a sequence of time intervals with specified granularity.

    This function creates a series of time intervals with equal lengths, starting from the provided start time
    and ending at the specified end time. It utilizes the `timedelta` class to represent the interval length
    and iterates until the end time is reached.

    Args:
        start (datetime): The start time of the time interval sequence.
        end (datetime): The end time of the time interval sequence.

    Returns:
        generator: A generator yielding tuples of start and end times for each interval.
    """

    interval_length = timedelta(minutes=60 // INTERVALS_PER_HOUR)
    current_time = start

    while current_time < end:
        yield (current_time, current_time + interval_length)
        current_time += interval_length


def linear_interpolation(start_time, end_time, start_state, end_state, timestamp):
    """
    Performs linear interpolation to estimate the state at a given timestamp.

    This function calculates the state value at a specified timestamp between two known state values based on the linear relationship
    between the timestamp and the known state values. It assumes a uniform rate of change between the start and end states.

    Args:
        start_time (datetime): The timestamp for the start state.
        end_time (datetime): The timestamp for the end state.
        start_state (float): The state value at the start time.
        end_state (float): The state value at the end time.
        timestamp (datetime): The timestamp for which to estimate the state.

    Returns:
        float: The estimated state value at the specified timestamp.
    """

    if start_time == end_time:
        return start_state

    # Calculate the alpha value based on the relative position of the timestamp
    alpha = (timestamp - start_time) / (end_time - start_time)

    # Estimate the state value using linear interpolation
    interpolated_state = start_state + alpha * (end_state - start_state)

    return interpolated_state


def get_state_at_timestamp(timestamp, observations):
    """
    Determines the state value at a given timestamp based on available observations.

    This function searches through a list of observations to find the two observations that bracket the provided timestamp.
    If such observations are found, it applies linear interpolation to estimate the state value at the timestamp.
    However, if no observations are found within the specified timestamp range, it returns False.

    Args:
        timestamp (datetime): The timestamp for which to determine the state.
        observations (list): A list of observation items containing timestamps and state values.

    Returns:
        float or bool: The estimated state value at the timestamp, or False if no observation found.
    """

    for i in range(len(observations) - 1):
        current_observation_timestamp = observations[i][1].replace(tzinfo=pytz.UTC)
        next_observation_timestamp = observations[i + 1][1].replace(tzinfo=pytz.UTC)

        if current_observation_timestamp <= timestamp <= next_observation_timestamp:
            start_observation = observations[i]
            end_observation = observations[i + 1]

            return linear_interpolation(
                start_observation[1],
                end_observation[1],
                start_observation[2],
                end_observation[2],
                timestamp,
            )

    return False  # Default to False if no observation found


def classify_time_intervals(observations, start_utc, end_utc):
    """
    Classifies time intervals based on observations within a given period.

    This function generates time intervals between start and end times and classifies each interval
    based on the state value estimated at the midpoint of the interval.

    Args:
        observations (list): A list of observation items containing timestamps and state values.
        start_utc (datetime): The start time of the interval.
        end_utc (datetime): The end time of the interval.

    Returns:
        list: A list of tuples containing start time, end time, and the estimated state for each interval.
    """

    intervals = list(generate_time_intervals(start_utc, end_utc))

    result = []

    for interval in intervals:
        start_time, end_time = interval
        state = get_state_at_timestamp(
            start_time.replace(tzinfo=pytz.UTC), observations
        )
        result.append((start_time, end_time, state))

    return result


def calculate_uptime_downtime(classified_intervals):
    """
    Calculates uptime and downtime for different time periods based on classified intervals.

    This function takes a dictionary of classified intervals for each weekday and calculates
    uptime and downtime for the last hour, last day, and last week.

    Args:
        classified_intervals (dict): A dictionary mapping weekdays to classified intervals.

    Returns:
        dict: A dictionary containing uptime and downtime values for different time periods.
    """

    now = StoremonitoringsystemConfig.current_timestamp
    current_weekday = now.weekday()  # 0=Monday, 6=Sunday
    last_hour_start = now - timedelta(hours=1)
    last_day_start = now - timedelta(days=1)
    last_week_start = now - timedelta(weeks=1)

    uptime_last_hour = downtime_last_hour = 0
    uptime_last_day = downtime_last_day = 0
    uptime_last_week = downtime_last_week = 0

    for weekday, result in classified_intervals.items():
        for interval in result:
            start_time, end_time, state = interval
            if start_time >= last_week_start:
                if state:
                    uptime_last_week += (end_time - start_time).total_seconds() / 3600
                else:
                    downtime_last_week += (end_time - start_time).total_seconds() / 3600

            if weekday == current_weekday:
                if start_time >= last_hour_start:
                    if state:
                        uptime_last_hour += (end_time - start_time).total_seconds() / 60
                    else:
                        downtime_last_hour += (
                            end_time - start_time
                        ).total_seconds() / 60

                if start_time >= last_day_start:
                    if state:
                        uptime_last_day += (
                            end_time - start_time
                        ).total_seconds() / 3600
                    else:
                        downtime_last_day += (
                            end_time - start_time
                        ).total_seconds() / 3600

    return {
        "uptime_last_hour": uptime_last_hour,
        "downtime_last_hour": downtime_last_hour,
        "uptime_last_day": uptime_last_day,
        "downtime_last_day": downtime_last_day,
        "uptime_last_week": uptime_last_week,
        "downtime_last_week": downtime_last_week,
    }


def generate_store_report(store_id, observations):
    """
    Generates a store report based on observations for a specific store.

    This function calculates classified intervals for each weekday and then calculates uptime and downtime
    for different time periods based on those intervals. The results are used to create a StoreReport object.

    Args:
        store_id (int): The identifier of the store.
        observations (list): A list of observation items containing timestamps and state values.

    Returns:
        StoreReport: An object containing uptime and downtime information for the store.
    """

    business_hours_data = get_business_hours_by_store(store_id)
    recent_observations = filter_recent_observations(
        observations, StoremonitoringsystemConfig.current_timestamp
    )
    grouped_observations = group_observations_by_date(recent_observations)

    classified_intervals = {
        day: classify_time_intervals(
            grouped_observations.get(day, []),
            datetime.combine(
                date_weekday_mapping[day], business_hours_data[day]["start_utc"]
            ),
            datetime.combine(
                date_weekday_mapping[day], business_hours_data[day]["end_utc"]
            ),
        )
        for day in range(7)
    }

    uptime_downtime_summary = calculate_uptime_downtime(classified_intervals)

    store_report = StoreReport(store=store_id, **uptime_downtime_summary)

    return store_report


def process_store_group(args):
    """
    Processes a group of observations for a specific store asynchronously.

    This function generates a store report for a specific store based on the provided observations.
    It handles any exceptions that may occur during the processing and prints an error message.

    Args:
        args (tuple): A tuple containing store_id and observations.

    Returns:
        StoreReport or None: An object containing uptime and downtime information for the store,
        or None if an error occurs during processing.
    """

    try:
        store_id, observations = args
        store_report = generate_store_report(store_id, observations)
        return store_report
    except Exception as e:
        # Capture and handle the error
        print(f"Error processing store group: {e}, {store_id}")
        # You can also log the error or raise it further


def generate_store_data():
    """
    Generates store data by processing observations for multiple stores in parallel.

    This function fetches all store data including timestamp and activity status,
    groups the stores by store_id, calculates the date-weekday mapping, and then processes each
    store group asynchronously using ThreadPoolExecutor.

    Returns:
        list: A list of StoreReport objects containing uptime and downtime information for each store.
    """

    # Fetch all store data including timestamp and activity status
    all_stores_data = Store.objects.values_list(
        "store", "timestamp_utc", "is_active"
    ).order_by("store", "timestamp_utc")

    # Group the stores by store_id
    grouped_stores = [
        (key, list(group)) for key, group in groupby(all_stores_data, key=itemgetter(0))
    ]

    # Calculate the date-weekday mapping
    calculate_date_weekday_mapping()

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        # Process each store group asynchronously
        store_data_by_id = list(executor.map(process_store_group, grouped_stores))

    return store_data_by_id
