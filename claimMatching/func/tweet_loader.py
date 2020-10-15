"""
Created on Wed Jul 29 16:35:20 2020
This file contains several functions used for reading and
filtering data.
@author: brocklin
"""
from io import BytesIO
import json, os, re, sys
from PIL import Image

import jsonlines
from langdetect import detect
import psycopg2
import pytesseract
import requests

def get_db_pwd(cfg):
    """
    Helper function that fetches the user's PostgreSQL database password from the secret.json file. The secret.json
    is set up according to the README.md file.

    :return: the database password stored in secret.json
    """
    if os.path.isfile(cfg['secret_loc']):
        with open(cfg['secret_loc']) as f:
            print(f)
            secret_json = json.load(f)
            if not secret_json or not secret_json.get('tweet_db_pwd'):
                print("Key required, please consult the README for proper instruction.")
                sys.exit(1)
            return secret_json.get('tweet_db_pwd')
    else:
        print("Failed to find secret.json, please consult the README for proper instruction.")
        sys.exit(1)

def get_db_tweet_caption(cursor, media_ids):
    """
    Returns an OCR and image-captioning caption for a given tweet.

    :param cursor: cursor to execute SQL queries for connected to Mona's DB
    :param media_ids: list of all ids of media associated with a tweet
    :return: the caption given for the supplied media image
    """
    media_ids = json.loads(media_ids)
    if len(media_ids) == 0:
        return ""
    query = "select media_url_https from media where id IN %s"
    cursor.execute(query, (tuple(media_ids),))
    media_data = cursor.fetchall()
    return caption_image(image_fetch(media_data[0][0]))

def get_tweet_data(multimodal, cfg):
    """
    Helper function that fetches twitter data from the database.

    :param multimodal: boolean denoting whether or not multimodal data should be used
    :param cfg: configuration dictionary
    :return: a list of tweets
    """
    conn = psycopg2.connect(
        host="coviz-infodemic.cntqhtt2u1xx.us-east-1.rds.amazonaws.com",
        port="5432",
        user="postgres",
        password=get_db_pwd(cfg))
    cursor = conn.cursor()
    num_tweets = cfg['num_tweets']
    query_fields = ""
    if multimodal:
        query_fields = ", id_media"
    cursor_command = f'select full_text{query_fields} from tweets where lang=\'en\''
    if num_tweets != 0:
        cursor_command = f'{cursor_command} limit {num_tweets};'
    else:
        cursor_command += ';'
    cursor.execute(cursor_command)
    server_data = cursor.fetchall()
    tweets = []
    for datapoint in server_data:
        if multimodal:
            tweets.append(datapoint[0] + get_db_tweet_caption(cursor, datapoint[1]))
        else:
            tweets.append(datapoint[0])
    return tweets


def image_fetch(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return image


def caption_image(image):
    # ocr captioning
    ocr_caption = pytesseract.image_to_string(image)

    # image captioning
    # print(os.popen("th").read())
    image_caption = ""

    return ocr_caption + image_caption


def get_local_tweet_caption(tweet):
    tweet_obj = json.loads(tweet)
    entities = tweet_obj.get('entities')
    caption = None
    if entities:
        media = entities.get("media")
        if media:
            image_url = media[0].get("media_url_https")
            image_type = media[0].get('type')
            if image_type == 'photo':
                caption = caption_image(image_fetch(image_url))
    if not caption:
        caption = ''
    tweet_obj["full_text"] = tweet_obj.get("full_text") + caption
    return tweet_obj


def get_local_tweet_data(multimodal, cfg):
    """
    Helper function that fetches the twitter data from a file

    :param multimodal: boolean denoting whether or not multimodal data should be used
    :param cfg: configuration dictionary
    :return: a list of tweets
    """
    combined_regex = "(" + ")|(".join(cfg['tweet_files']) + ")"
    if not os.path.exists(cfg['tweet_dir']):
        print("Please fetch and set up Twitter data before continuing per the README.")
        sys.exit(1)
    tweet_files = [os.path.join(cfg['tweet_dir'], file) for file in os.listdir(cfg['tweet_dir'])
                   if re.match(combined_regex, file)]
    tweets = []
    print("Tweet files matched:")
    print(tweet_files)
    num_entries = 0
    for file in tweet_files:
        with jsonlines.open(file) as f:
            for tweet in f:
                tweet_text = tweet.get('full_text')
                try:
                    tweet_lang = detect(tweet_text)
                except:
                    tweet_lang = None
                if tweet_lang == 'en' and tweet.get('lang') == 'en':
                    if multimodal:
                        captioned_tweet = get_local_tweet_caption(tweet)
                        if cfg['remove_text_only'] and captioned_tweet.get("full_text") == tweet.get("full_text"):
                            # if we are removing text only tweets, the tweet will be unchanged, continue without it
                            # Note to Nina: until image captioning is added, this will also remove tweets w/o OCR-detected text
                            continue
                tweets.append(tweet)
                num_entries += 1
                if num_entries == cfg['num_entries']:
                    return tweets
    return tweets
