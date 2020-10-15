"""
Created on Wed Jul 29 16:35:07 2020
This file contains functions for reading in Google FactCheck claim data.
@author: brocklin
"""
import json, os, sys

def get_claim_data(cfg):
    """
    Helper function that fetches the fact-checked data from a file

    :param cfg: configuration dictionary
    :return: a list of fact-checked claims
    """
    claim_files = []
    for language in cfg['languages']:
        language_dir = os.path.join(cfg['google_dir'], language)
        if not os.path.exists(language_dir):
            print("Please fetch Google FactCheck API data for language", language, "before continuing per the README.")
            sys.exit(1)
        language_files = [os.path.join(language_dir, file) for file in os.listdir(language_dir)
                          if file.endswith('.json')]
        if len(language_files) == 0:
            print("Please fetch Google FactCheck API data before continuing per the README.")
            sys.exit(1)
        claim_files.extend(language_files)
    claims = []
    for file in claim_files:
        with open(file) as f:
            claims.extend(json.load(f))
    return claims
