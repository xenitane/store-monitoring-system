from datetime import date, datetime
from pytz import timezone, utc

from apps.models import BusinessHours, Timezone


def get_default_business_hours_data():
    """
    Returns a list of dictionaries representing default business hours for all days of the week.
    Each dictionary has two keys: "day" and "start_utc".
    The "day" key is an integer representing the day of the week (6 for Sunday, 0 for Monday, etc.).
    The "start_utc" key is a time object representing the start time of the business day in UTC.
    """
    return [
        {
            "day": day,
            "start_utc": datetime.strptime("00:00:00", "%H:%M:%S").time(),
            "end_utc": datetime.strptime("23:59:59", "%H:%M:%S").time(),
        }
        for day in range(7)
    ]


def convert_local_time_to_utc(local_time, timezone_info):
    """
    Converts a local time to UTC.

    Args:
        local_time (datetime): The local time to convert.
        timezone_info (str): The timezone information.

    Returns:
        datetime: The UTC time.
    """
    local_timezone = timezone(timezone_info)
    local_datetime = datetime.combine(date.today(), local_time)
    localized_datetime = local_timezone.localize(local_datetime, is_dst=None)

    # Convert to UTC
    return localized_datetime.astimezone(utc).time()


def convert_business_hours_to_utc(store_id, start_time_local, end_time_local):
    """
    Converts local business hours to UTC.

    Args:
        store_id (int): The ID of the store.
        start_time_local (datetime): The start time of the business day in local time.
        end_time_local (datetime): The end time of the business day in local time.

    Returns:
        tuple: A tuple of two time objects representing the start and end times of the business day in UTC.
    """
    timezone_info = get_timezone_info_for_store(store_id)
    start_utc = convert_local_time_to_utc(start_time_local, timezone_info)
    end_utc = convert_local_time_to_utc(end_time_local, timezone_info)
    return start_utc, end_utc


def get_timezone_info_for_store(store_id):
    """
    Retrieves the timezone information for a store.

    Args:
        store_id (int): The ID of the store.

    Returns:
        str: The timezone information.
    """
    try:
        # Get the timezone information from the Timezone model
        timezone_obj = Timezone.objects.get(store=store_id)
        return timezone_obj.timezone_str
    except Timezone.DoesNotExist:
        # If timezone information is missing, assume America/Chicago
        return "America/Chicago"


def get_business_hours_by_store(store_id):
    """
    Retrieves the business hours for a store.

    Args:
        store_id (int): The ID of the store.

    Returns:
        list: A list of dictionaries representing the business hours for the store.
    """
    business_hours_data = get_default_business_hours_data()

    # Try to retrieve the business hours from the BusinessHours model
    try:
        business_hours = BusinessHours.objects.filter(store=store_id)
    except BusinessHours.DoesNotExist:
        # If no business hours data is found, assume it is open 24*7
        return business_hours_data

    # Update the default business hours data with the retrieved business hours
    for business_hour in business_hours:
        # Convert the local business hours to UTC
        start_utc, end_utc = convert_business_hours_to_utc(
            store_id,
            business_hour.start_time_local,
            business_hour.end_time_local,
        )

        # Update the corresponding entry in the business_hours_data list
        entry_index = business_hour.day
        business_hours_data[entry_index]["start_utc"] = start_utc
        business_hours_data[entry_index]["end_utc"] = end_utc

    return business_hours_data
