import json
import os


def load_config(base_dir=None, filename="config.json"):
    folder = base_dir if base_dir is not None else os.getcwd()
    with open(os.path.join(folder, filename)) as f:
        return json.load(f)
