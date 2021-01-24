import json

def load_json(file):
    with open(file) as f:
        data = json.load(f)
    return data
