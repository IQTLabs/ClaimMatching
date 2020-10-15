"""
Created on Fri Jul 10 16:17:18 2020
This codebase creates a SBERT model that matches user-submitted
tweets about COVID to fact-checked claims in order to classify
tweets as true or false.
The main functions are:
    1) Fetch fact-checked data from the Google API.
    2) Fine-tune a SBERT model on COVID-related data.
    3) Match each tweet to its nearest fact-checked claim.
@author: brocklin
"""
import func.get_google_fact_check as FactCheck
import func.match_claims as ClaimMatcher

import argparse, os, sys, yaml

if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', '--config', dest='config', type=str,
                        default='claimMatching/config/config.yml',
                        help='configuration file\'s location')
    parser.add_argument('-s', '--search_set', dest='search_set', type=str,
                        default='google', choices=['tweets', 'local_tweets', 'google', 'ng', 'misc_json', 'manual'],
                        help='which items to find matching claims for')
    parser.add_argument('-c', '--candidate_set', dest='candidate_set', type=str,
                        default='tweets', choices=['tweets', 'local_tweets', 'google', 'ng', 'misc_json'],
                        help='which items to use as potential matches for the search set items')
    parser.add_argument('-g', '--fetch_google_data', dest='fetch_data', action='store_true',
                        help='specifies that FactCheck API data should be fetched')
    parser.add_argument('-d', '--keep_duplicates', dest='keep_duplicates', action='store_true',
                        help='specifies that duplicate datapoints should be retained rather than pruned')
    parser.add_argument('-m', '--multimodal', dest='multimodal', action='store_true',
                        help='specifies that multimodal Twitter data should be fetched')
    parser.add_argument('-f', '--filter', dest='filter', action='store_true',
                        help='specifies that the search set should be filtered with words from the target set')
    arguments = parser.parse_args()

    # configuration setup
    CWD = os.getcwd()
    config_loc = os.path.join(CWD, arguments.config)
    with open(config_loc, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    if not cfg:
        print('Config file not found, please supply a valid, non-empty config or use the default.')
        sys.exit(1)
    cfg['CWD'] = CWD
    if arguments.fetch_data:
        FactCheck.write_fact_check_data(cfg)
    ClaimMatcher.find_nearest_claims(arguments.search_set, arguments.candidate_set, not arguments.keep_duplicates,
                                     arguments.multimodal, arguments.filter, cfg)
