import json
import os

def load_challenges():
    if os.path.exists('challenges.json'):
        with open('challenges.json', 'r') as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open('scores.json', 'w') as f:
        json.dump(scores, f, indent=4)
