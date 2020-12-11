# Infodemic Claim-Matching

## Intro

This codebase matches COVID-19-related content from Google's Fact Check API to json files (e.g. Tweets) 

We have provided a claim matcher than can support matching claims from one set of data to another using semantic analysis.
More specifically, we use a SBERT to encode each claim from one set, which we call the search set. 
Then, we iterate over every encoding in another set, the candidate set, and pick the closest matches from each. 
For instructions on how to use the claim matcher, follow the instructions below, keeping in mind that the functionality 
is located in the `claimMatching` subdirectory.


## Claim Matching via Semantic Similarity
This repository leverages a pre-trained SBERT model (see Reimers & Gurevych 2019 for details) to rapidly compare two document sets at a sentence level. In the below example, we are searching a database of previously fact checked claims (the candidate set) with the tweets in our database. 

<p float="left">
  <img src="docs/assets/ClaimMatching_system.png" width="600" />
</p>

We pre-processed the search set (COVID-related Tweets, in this case), by filtering to English and to the top fact-checked claim terms via TF-IDF. We added this TF-IDF filtering step because converting tweets to embeddings is the longest step of the pipeline. This largely reduced the less relevant tweets we searched for matches to (e.g. Tweets of "This." or "That's the Tweet".) 

<p float="left">
  <img src="docs/assets/Preprocessing_pipeline.png" width="600" />
</p>



### Examples
Here's an example of a tweet and the closest matches in the fact-checked claim database: 
<p float="left">
  <img src="docs/assets/Tweet-match.png" width="600" />
</p>

Here's an example of a claim and the closest tweets: 
<p float="left">
  <img src="docs/assets/Claim-match.png" width="600" />
</p>


## Claim-Matching Setup
1. Navigate to the root directory in Terminal.
2. Create a new virtual environment.
   2. On MacOS/Linux, run `python3 -m venv claimEnv` in Terminal.
   2. On Windows, run `py -m venv claimEnv` in CMD or Powershell.
3. Activate the virtual environment. This should be done every time you run code.
   3. On MacOS/Linux, run `source claimEnv/bin/activate`.
   3. On Windows, run `.\claimEnv\Scripts\activate`.
4. From the repository root, install every package needed by running `pip install -r requirements.txt`.
5. In the repository root, run the setup script.
   5. On MacOS/Linux, run `python claimMatching/setup.py`.
   5. On Windows, run `python .\claimMatching\setup.py`.
6. When finished running commands, run `deactivate` to stop using the virtual environment. Be sure to reactivate the
virtual environment per the instructions given above when you choose to run the jupyter notebooks or claim matcher.

### Dataset Terminology
In order to run the claim matcher, data must be fetched. There are two sets of data used
in the matcher: the search set (the data that is iterated over to find matches for) and
the candidate set (the potential matches for each item in the search set). For example, to find
the top 10 most similar matches from set "B" to each item in set "A", set "A" would be made
the search set and set "B" would be made the candidate set. Both sets support tweets from Twitter, claims from the
Google FactCheck API, and user supplied JSON from any source. The search set may contain manually
specified sentences. Below are instructions for how to set up each source for use.

### Fact Check API Setup
In order to obtain the data for the Google Fact Check API, one must first set up a personal key via the following steps:
1. Follow the instructions located at https://support.google.com/googleapi/answer/6158862 to create an API key for your
account.
2. Duplicate the secret-template.json file in the claimMatching/env directory of the repository and name the duplicate
secret.json, if secret.json wasn't created for Twitter data setup above.
3. Inside secret.json, insert the new API key between the empty quotes. For example, if the API key is `MY KEY`, the
secret.json should have the contents `{"key":"MY KEY", "tweet_db_pwd":""}`.
4. Run `python claimMatching/main.py -g` from your repository root. The first attempt to fetch data will fail with a
message that includes a link. Click on the link and follow the on-screen instructions to give Fact Check API permission
to use your API key.
5. Run `main.py` again following the directions above to successfully fetch the data.

### Postgres Tweet Data Setup
1. Inside secret.json, insert your Postgres API key between the empty quotes. For example, if the API key is MY PASSWORD, the secret.json should have the contents {"key":"", "tweet_db_pwd":"MY PASSWORD"}.
2. When you run the Claim Matcher, follow the flags for PostgreSQL for search/candidate data. 

### Local Tweet Data Setup
1. Hydrate the Twitter data located at the [COVID-19 Twitter data respository](https://github.com/echen102/COVID-19-TweetIDs)
as jsonl files.
2. Move the desired hydrated jsonl files to `data_samples/tweets/`.
3. When you run the Claim Matcher, follow the flags for local tweets for search/candidate data. 

### Manual Search Set Setup
1. Open `config.yml` with a text editor in the repository root.
2. Add sentences to the `sentences` variable at the bottom of the file to add them to the search set.

### Running Claim Matcher
1. Activate the virtual environment from the setup above.
2. Navigate to your repository root.
3. Run `python claimMatching/main.py` from your repository root. The default search and candidate sets are Twitter and the
FactCheck API, respectively.
4. In order to specify the search and candidate sets, run `python claimMatching/main.py -s <search> -c <candidate>`, where
`<search>` is the name of the search set and `<candidate>` is the name of the candidate set. Both sets support `tweets`
for Twitter data from a PostgreSQL database, `factcheck` for FactCheck API, `local_tweets` for tweets pulled from json
files downloaded locally, and `misc_json` for data pulled from miscellaneous JSON files. Add the `-f` flag in order to
filter search set documents using the candidate set.

### Using Multimodal Tweets
In order to use multimodal tweet data, there are additional items that must be installed manually.
1. Install Tesseract OCR from https://github.com/tesseract-ocr/tesseract
1. Install densecap from https://github.com/jcjohnson/densecap for image captioning. TODO: following instructions are temporary for testing image captioning:
    1. Place all images you'd like to run the image captioner on into a folder anywhere.
    1. Run the captioner via `th run_model.lua -input_dir /path/to/image/folder` in the densecap root directory.
    1. Change to the `vis` directory (`cd vis`).
    1. View all output files by running `python -m http.server 8181` inside the `vis` directory and opening `localhost:8181/view_results.html` in your browser.
1. Run `python claimMatching/main.py -m` in order to use multimodal Twitter data.
