"""
Created on Tue Jul 14 12:34:50 2020
This file creates a SBERT model that matches user-submitted
tweets about COVID to the nearest fact-checked claims.
@author: brocklin
"""
from datetime import datetime
import os, sys

import numpy as np
import scipy
from sentence_transformers import SentenceTransformer

import func.google_fc_loader as GoogleLoader
import func.ng_loader as NewsGuardLoader
import func.tweet_loader as TweetLoader
import func.misc_json_loader as MiscLoader
from func.util import get_filtering_words, make_list_unique, filter_documents


def encode_sets(search_docs, candidate_docs, model_weights, search_set, candidate_set):
    """
    Encodes all the items in the search and candidate sets using an
    SBERT sentence encoder with the given weights.

    :param search_docs: list of all documents from the search set
    :param candidate_docs: list of all documents from the candidate set
    :param model_weights: name of the pre-trained weights to use to encode the documents
    :param search_set: name of the search set
    :param candidate_set: name of the candidate set
    :return: a list of embeddings for the search set and a list of embeddings for the candidate set
    """
    embedder = SentenceTransformer(model_weights)

    if search_set == candidate_set:
        print("Encoding search and candidate set data...")
        search_embeddings = embedder.encode(search_docs)
        return search_embeddings, search_embeddings
    else:
        print("Encoding search set...")
        search_embeddings = embedder.encode(search_docs)

        print("Encoding candidate set...")
        candidate_embeddings = embedder.encode(candidate_docs)
        return search_embeddings, candidate_embeddings


def get_top_matches(search_embedding, candidate_embeddings, search_set, candidate_set, cfg):
    """
    Helper function to find the top matching items in the candidate set for a search set item.

    :param search_embedding: SBERT-generated embedding for search set document
    :param candidate_embeddings: SBERT-generated embeddings for all documents in the target set
    :param search_set: name of the search set
    :param candidate_set: name of the target set
    :param cfg: configuration dictionary
    :return: distances and indices of the closest candidate documents to the search document
    """
    distances = scipy.spatial.distance.cdist([search_embedding], candidate_embeddings, "cosine")[0]
    sorted_dists = np.argsort(distances)
    # if the search set is the same as the candidate set, keep the same element from showing up in the matches
    low_indices = None
    if search_set == candidate_set:
        low_indices = sorted_dists[1:cfg['num_matches'] + 1]
    else:
        low_indices = sorted_dists[:cfg['num_matches']]
    return distances, low_indices


def write_search_doc_output(file, search_doc, candidate_docs, match, distances, low_indices):
    """
    Helper function to write output for matches to each document in the search set.

    :param file: file to output to
    :param search_doc: document from the search set
    :param candidate_docs: all candidate documents
    :param match: matching keywords
    :param distances: distances to each nearby candidate
    :param low_indices: indices of each nearby candidate
    :return: none
    """
    file.write("Search set item:\n")
    file.write(search_doc.replace('\n', ' ') + '\n')
    file.write("----------------------------\n")
    if match:
        file.write("Matching keywords: " + str(match) + '\n')
    file.write("Distances to candidate: " + str(distances) + '\n')
    file.write("Top candidate set matches (high to low): \n")
    for dist in low_indices:
        file.write("- " + str(candidate_docs[dist]).replace('\n', ' ') + '\n')
    file.write("\n")


def retrieve_nearest(search_docs, candidate_docs, matches, search_set, candidate_set, cfg):
    """
    Retrieves the nearest claims for each tweet passed in.

    :param search_docs: list of all documents in the search set
    :param candidate_docs: list of all documents in the candidate set
    :param matches: list of filtered tweets' matching keywords
    :param search_set: string denoting what data to use for the search set
    :param candidate_set: string denoting what data to use for the candidate set
    :param cfg: configuration dictionary
    :return: none
    """
    search_embeddings, candidate_embeddings = encode_sets(search_docs, candidate_docs, cfg['model'], search_set,
                                                          candidate_set)

    if len(matches) == 0:
        matches = [None] * len(search_embeddings)

    print("Writing output...")
    if not os.path.exists((cfg['output_dir'])):
        cwd = os.getcwd()    
        os.mkdir(os.path.join(cwd,cfg['output_dir']))

    with open(os.path.join(cfg['output_dir'], search_set + '-' + candidate_set + '-' +
                                              datetime.now().strftime("%m%d%y-%H%M%S") + '.txt'), "w") as f:
        f.write("Model: " + cfg['model'] + "\n")
        f.write("Search Set: " + search_set + "\n")
        f.write("Candidate Set: " + candidate_set + "\n")
        f.write("Languages: " + str(cfg['languages']) + "\n\n")
        for search_doc, search_embedding, match in zip(search_docs, search_embeddings, matches):
            distances, low_indices = get_top_matches(search_embedding, candidate_embeddings, search_set,
                                                     candidate_set, cfg)
            write_search_doc_output(f, search_doc, candidate_docs, match, distances[low_indices], low_indices)


def find_nearest_claims(search_set, candidate_set, prune_duplicates, multimodal, filter, cfg):
    """
    Finds and prints the nearest claims for each tweet. Serves as a
    controller function that dispatches work to various other helper
    functions.

    :param search_set: string denoting what data to use for the search set
    :param candidate_set: string denoting what data to use for the candidate set
    :param prune_duplicates: boolean denoting whether or not to remove duplicates from the search and candidate sets
    :param multimodal: boolean denoting whether or not multimodal data should be used
    :param cfg: configuration dictionary
    :return: none
    """
    tweets, local_tweets, google_claims, misc_data = None, None, None, None
    if candidate_set == 'google' or search_set == 'google':
        google_claims = [claim.get('text') for claim in GoogleLoader.get_claim_data(cfg)]
    if candidate_set == 'local_tweets' or search_set == 'local_tweets':
        local_tweets = [tweet.get('full_text') for tweet in TweetLoader.get_local_tweet_data(multimodal, cfg)]
    if candidate_set == 'tweets' or search_set == 'tweets':
        tweets = TweetLoader.get_tweet_data(multimodal, cfg)
    if candidate_set == 'ng' or search_set == 'ng':
        ng_data = [ng.get('description') for ng in NewsGuardLoader.get_ng_data(cfg)]
    if candidate_set == 'misc_json' or search_set == 'misc_json':
        misc_data = [misc_point.get('content') for misc_point in MiscLoader.get_json_data(cfg)]

    candidate_docs = None
    if candidate_set == 'google':
        candidate_docs = google_claims
    elif candidate_set == 'tweets':
        candidate_docs = tweets
    elif candidate_set == 'local_tweets':
        candidate_docs = local_tweets
    elif candidate_set == 'ng':
        candidate_docs = ng_data
    elif candidate_set == 'misc_json':
        candidate_docs = misc_data
    if prune_duplicates:
        print("Pruning duplicate from", len(candidate_docs), "candidate documents...")
        candidate_docs = make_list_unique(candidate_docs)

    search_docs = None
    if search_set == 'google':
        search_docs = google_claims
    elif search_set == 'tweets':
        search_docs = tweets
    elif search_set == 'local_tweets':
        search_docs = local_tweets
    elif search_set == 'ng':
        search_docs = ng_data
    elif search_set == 'manual':
        search_docs = cfg['sentences']
    elif search_set == 'misc_json':
        search_docs = misc_data
    if prune_duplicates:
        print("Pruning duplicates from", len(search_docs), "search documents...")
        search_docs = make_list_unique(search_docs)

    keyword_matches = []
    if filter:
        print("Filtering", len(search_docs), "search documents...")
        filter_words = get_filtering_words(candidate_docs, cfg)
        search_docs, keyword_matches = filter_documents(search_docs, filter_words)

    print("Retrieving nearest with", len(search_docs), "search documents and", len(candidate_docs),
          "candidate documents.")
    retrieve_nearest(search_docs, candidate_docs, keyword_matches, search_set, candidate_set, cfg)
