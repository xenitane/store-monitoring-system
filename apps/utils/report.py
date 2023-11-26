import multiprocessing
import time

from django.http import JsonResponse
from rest_framework import status

from apps.models import Report

from .report_data import generate_store_data


def create_report():
    """
    Create and save a new Report instance.

    Returns:
        Report: The newly created Report instance.
    """
    report = Report()
    report.save()
    return report


def generate_report_async(report):
    """
    Trigger generate_report in a separate process using multiprocessing.

    Args:
        report (Report): The Report instance to be updated asynchronously.
    """
    pool = multiprocessing.Pool()
    pool.apply_async(generate_report, (report.set_store_data,))
    pool.close()


def get_report_by_id(report_id):
    """
    Retrieve a Report instance by its ID.

    Args:
        report_id (int): The ID of the Report instance to be retrieved.

    Returns:
        Report: The retrieved Report instance if present else None.
    """
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return None

    return report


def generate_report(set_store_data_callback):
    """
    Generate a Report with store data and update the provided callback.

    Args:
        set_store_data_callback (function): The callback function to set store data.

    Prints:
        str: A message indicating the success and time taken to generate the report.
    """
    print("Generating Report...")
    start_time = time.time()  # Record the start time
    set_store_data_callback(generate_store_data())
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time
    print(f"Report generated successfully. Time taken: {elapsed_time:.2f} seconds")
