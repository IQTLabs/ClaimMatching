"""
Created on Wed Aug 31 15:36:10 2020
This file contains functions for reading in NewsGuard claim data.
@author: brocklin
"""
import json, os, sys

def get_ng_data(cfg):
    """
    Helper function that fetches the NewsGuard data from a file

    :param cfg: configuration dictionary
    :return: a list of fact-checked miscellaneous json claims
    """
    if not os.path.exists(cfg['ng_dir']):
        print("Please ensure you followed the README directions for JSON data.")
        sys.exit(1)
    json_files = [os.path.join(cfg['ng_dir'], file) for file in os.listdir(cfg['ng_dir']) if file.endswith('.json')]
    if len(json_files) == 0:
        print("Please ensure you followed the README directions for JSON data.")
        sys.exit(1)
    data = []
    for file in json_files:
        with open(file) as f:
            data.extend(json.load(f))
    return data
