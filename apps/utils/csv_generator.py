import csv
import os


def generate_csv_and_return_path(report):
    """
    Generates a CSV file containing the report data and returns the file path.

    Args:
        report (object): The report object containing the data to be exported.

    Returns:
        str: The path to the generated CSV file.
    """
    csv_generator = CSVGenerator(report.id, report.get_store_data())
    csv_path = csv_generator.generate_csv()
    return csv_path


class CSVGenerator:
    """
    Class responsible for generating CSV files from report data.
    """

    def __init__(self, report_id, store_reports):
        """
        Initializes the CSVGenerator object with the report ID and store reports data.

        Args:
            report_id (int): The unique identifier of the report.
            store_reports (list): A list of store report objects containing the data to be exported.
        """
        self.report_id = report_id
        self.store_reports = store_reports

    def generate_csv(self):
        """
        Generates a CSV file containing the report data and returns the file path.

        Returns:
            str: The path to the generated CSV file.
        """
        csv_filename = f"{self.report_id}.csv"
        csv_path = os.path.join("csv_data", csv_filename)

        with open(csv_path, "w", newline="") as csv_file:
            self._write_csv_header(csv_file)
            self._write_csv_data(csv_file)

        return csv_path

    def _write_csv_header(self, csv_file):
        """
        Writes the CSV header row to the file.

        Args:
            csv_file (file): The open CSV file object.
        """
        field_names = [
            "store",
            "uptime_last_hour",
            "uptime_last_day",
            "uptime_last_week",
            "downtime_last_hour",
            "downtime_last_day",
            "downtime_last_week",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

    def _write_csv_data(self, csv_file):
        """
        Writes each store report data as a row to the CSV file.

        Args:
            csv_file (file): The open CSV file object.
        """
        for store_report in self.store_reports:
            writer = csv.DictWriter(
                csv_file, fieldnames=store_report.serialize().keys()
            )
            writer.writerow(store_report.serialize())
