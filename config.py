import json
import os

class Config:
    def __init__(self, filename="config.json"):
        self.filename = filename
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {
            "ctf_role": None,
            "announcement_channel": None
        }

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
