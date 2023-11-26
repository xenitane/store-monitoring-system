import json


def get_is_importing():
    with open("is_importing.json", "r") as file:
        data = json.load(file)
        return data.get("is_importing")


def set_is_importing(value):
    data = {"is_importing": value}
    with open("is_importing.json", "w") as file:
        json.dump(data, file)
