import json

def load_json(file_path):
    with open(file_path, 'rb') as inp:
        data = inp.read().decode("utf-8")
        return json.dumps(json.loads(data))