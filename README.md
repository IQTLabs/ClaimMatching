# ClaimMatching
Codebase to match COVID-19-related content from Google's Fact Check API to json files (e.g. Tweets) 

We have provided a claim matcher than can support matching claims from one set of data to another using semantic analysis. More specifically, we use an SBERT to encode each claim from one set, which we call the search set. Then, we iterate over every encoding in another set, the candidate set, and pick the closest matches from each. For instructions on how to use the claim matcher, follow the README in the claimMatching/ directory.
