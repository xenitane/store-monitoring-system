from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .apps import StoremonitoringsystemConfig
from .utils.csv_generator import generate_csv_and_return_path
from .utils.report import create_report, generate_report_async, get_report_by_id
from .utils.is_importing import get_is_importing


@api_view(["POST"])
def trigger_report(request):
    """
    Trigger the generation of a new report asynchronously.

    Returns:
        JsonResponse: A JsonResponse indicating the success or failure of triggering the report.
    """
    if get_is_importing():
        return JsonResponse(
            {"error": "Data is still being loaded, please wait for some time."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Create a new Report instance
    report = create_report()

    # Trigger generate_report in a separate process using multiprocessing
    generate_report_async(report)

    return JsonResponse({"report_id": report.id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_report(request, report_id):
    """
    Retrieve the status of a report and its associated CSV path.

    Args:
        report_id (int): The ID of the report to retrieve.

    Returns:
        JsonResponse or Response: A JsonResponse indicating the status of the report or a Response containing the CSV path.
    """

    if get_is_importing():
        return JsonResponse(
            {"error": "Data is still being loaded, please wait for some time."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    report = get_report_by_id(report_id)

    if not report:
        return JsonResponse(
            {"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if not report.is_completed:
        return JsonResponse({"status": "Running"}, status=status.HTTP_202_ACCEPTED)

    csv_path = generate_csv_and_return_path(report)
    return Response({"status": "Complete", "csv_path": csv_path})
