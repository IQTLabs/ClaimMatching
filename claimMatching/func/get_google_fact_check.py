"""
Created on Wed Jul 08 16:42:31 2020
This file is responsible for retrieving data on coronavirus
from the Google Fact Check ClaimReview API. After retrieving all
data, the data is written to a new file in the directory
specified by DATA_DIR_NAME.
@author: brocklin
"""
import json, os, sys, time

import requests

def get_api_key(cfg):
    """
    Helper function that fetches the user's API key from the secret.json file. The secret.json
    is set up according to the README.md file.

    :return: the Google Fact Check API key stored in secret.json
    """
    if os.path.isfile(cfg['secret_loc']):
        with open(cfg['secret_loc']) as f:
            secret_json = json.load(f)
            if not secret_json or not secret_json.get('key'):
                print("Key required, please consult the README for proper instruction.")
                sys.exit(1)
            return secret_json.get('key')
    else:
        print("Failed to find secret.json, please consult the README for proper instruction.")
        sys.exit(1)

def fetch_api_data(key, cfg):
    """
    Helper function that, given the Fact Check API key, retrieves several fact-checked documents
    about coronavirus. These claims are then written to a new file on disk.

    :param key: the Google Fact Check API key
    :return: none
    """
    for keyword in cfg['keywords']:
        for language in cfg['languages']:
            print("Beginning", keyword, "search in", language)
            status_code = 503
            data = []
            next_page = None
            params = {'key': key, 'query': keyword, 'languageCode': language}
            while status_code == 503:
                x = requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search",
                                 params=params)
                response_json = x.json()
                status_code = x.status_code
                if response_json:
                    data = response_json.get('claims')
                    next_page = response_json.get('nextPageToken')
            while next_page:
                print("Fetching page with code", next_page)
                params['pageToken'] = next_page
                x = requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search",
                                 params=params)
                response_json = x.json()
                # sleep for one minute on error to execute more queries and avoid rate-limiting
                if x.status_code == 503:
                    print("Rate limit hit, waiting for one minute")
                    time.sleep(60)
                    continue
                data.extend(response_json.get('claims', []))
                next_page = response_json.get('nextPageToken')
            print("Done fetching data for keyword", keyword, "with language code", language)

            file_name = language + "_" + keyword + ".json"
            with open(os.path.join(cfg['google_dir'], language, file_name), 'w') as out:
                json.dump(data, out, indent=2)

def write_fact_check_data(cfg):
    """
    Fetches the API key and uses this key to write fact-checked coronavirus claims
    to disk.

    :return: none
    """
    if not os.path.exists((cfg['google_dir'])):
        cwd = os.getcwd()
        if not os.path.exists(cfg['data_dir']):
            os.mkdir(os.path.join(cwd,cfg['data_dir']))
        os.mkdir((os.path.join(cwd,cfg['google_dir'])))

    for language in cfg['languages']:
        if not os.path.exists(os.path.join(cfg['google_dir'], language)):
            os.mkdir(os.path.join(cfg['google_dir'], language))
    api_key = get_api_key(cfg)
    fetch_api_data(api_key, cfg)
