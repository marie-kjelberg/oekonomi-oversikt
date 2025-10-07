"""
    Modules which house functions which gets app data
"""
import json


def get_categories():
    categories_path = "./data/categories.json"
    categories_string = ""
    with open(categories_path, "r", encoding="utf-8") as file:
        categories_string += file.read()

    categories = json.loads(categories_string)
    return categories