import os
import json
import requests
import numpy as np


def make_directory(path):
    try:
        os.makedirs(path)
    except:
        if not os.path.isdir(path):
            raise


def pull_data():
    categories = ["apple", "banana", "grapes"]

    this_directory = os.path.dirname(os.path.realpath(__file__))
    quickdraw_directory = this_directory + "/quickdraw"
    bitmap_directory = quickdraw_directory + "/bitmap"

    make_directory(quickdraw_directory)
    make_directory(bitmap_directory)

    bitmap_url = "https://storgae.googleapis.com/quickdraw_dataset/full/numpy_bitmap"

    total_categories = len(categories)

    for index, category in enumerate(categories):
        bitmap_filename = f"/{category}.npy"

        with open(bitmap_directory + bitmap_filename, "wb+") as bitmap_file:
            bitmap_response = requests.get(bitmap_url + bitmap_filename)
            bitmap_file.write(bitmap_response.content)

        print(f"Downloaded {category} drawings (category {index+1}/{total_categories})")


if __name__ == "__main__":
    pull_data()
