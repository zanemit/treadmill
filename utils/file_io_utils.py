import sys
import os
import numpy as np
import csv
import pandas as pd

def check_create_folder(folderpath): # check if a folder exists, otherwise create it
    if not os.path.isdir(folderpath):
        os.mkdir(folderpath)

def check_folder_empty(folderpath): # check if folder is empty, return true/false
    if not len(os.listdir(folderpath)):
        return True
    else:
        return False

def check_file_exists(filepath): # check if a file with the given path already exists
    return os.path.isfile(filepath)

def create_csv_file(filepath, fieldnames):
    try:
        with open(filepath, "a", newline='') as f:
            logger = csv.DictWriter(f, fieldnames=fieldnames)
            logger.writeheader()
    except Exception as e:
        raise ValueError("Could not create CSV file, probably because it is open in excel. \n\n{}",format(e))

def append_csv_file(csv_file, row, fieldnames):
    with open(csv_file, "a", newline='') as f:
        logger = csv.DictWriter(f, fieldnames=fieldnames)
        logger.writerow(row)

def load_csv_file(csv_file):
    return pd.read_csv(csv_file)
