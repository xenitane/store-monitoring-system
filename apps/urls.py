from django.urls import path

from apps.views import trigger_report, get_report

urlpatterns = [
    path("trigger-report/", trigger_report),
    path("get-report/<int:report_id>/", get_report),
]
