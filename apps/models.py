import json

from django.db import models


class Store(models.Model):
    store = models.IntegerField(db_index=True)
    timestamp_utc = models.DateTimeField(db_index=True)
    is_active = models.BooleanField()

    class Meta:
        unique_together = ["store", "timestamp_utc"]


class BusinessHours(models.Model):
    store = models.IntegerField(db_index=True)
    day = models.IntegerField()
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()

    class Meta:
        unique_together = ["store", "day"]


class Timezone(models.Model):
    store = models.IntegerField(db_index=True)
    timezone_str = models.CharField(max_length=50)


class StoreReport:
    def __init__(
        self,
        store,
        uptime_last_hour,
        uptime_last_day,
        uptime_last_week,
        downtime_last_hour,
        downtime_last_day,
        downtime_last_week,
    ):
        self.store = store
        self.uptime_last_hour = uptime_last_hour
        self.uptime_last_day = uptime_last_day
        self.uptime_last_week = uptime_last_week
        self.downtime_last_hour = downtime_last_hour
        self.downtime_last_day = downtime_last_day
        self.downtime_last_week = downtime_last_week

    def serialize(self):
        return {
            "store": self.store,
            "uptime_last_hour": self.uptime_last_hour,
            "uptime_last_day": self.uptime_last_day,
            "uptime_last_week": self.uptime_last_week,
            "downtime_last_hour": self.downtime_last_hour,
            "downtime_last_day": self.downtime_last_day,
            "downtime_last_week": self.downtime_last_week,
        }


class Report(models.Model):
    # Django will automatically add an auto-incrementing primary key 'id'
    store_data = models.JSONField(default=list)
    is_completed = models.BooleanField(default=False)

    def set_store_data(self, store_reports):
        # Convert a list of StoreReport instances to a list of dictionaries
        data_list = [store_report.serialize() for store_report in store_reports]
        self.store_data = json.dumps(data_list)
        self.is_completed = True
        self.save()

    def get_store_data(self):
        # Convert the JSON-serialized store_data back to a list of dictionaries
        data_list = json.loads(self.store_data)
        return [StoreReport(**store_data) for store_data in data_list]
