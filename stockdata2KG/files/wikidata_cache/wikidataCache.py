import json
import os
import requests
from typing import Dict

# this code is partly written with Claude 3.5 Sonnet because I did not want to code a custom caching function,
# party of this code are custom to adapt it to the wikidata api

class WikidataCache:
    def __init__(self, cache_file='files/wikidata_cache/wikidata_cache.json'):
        self.cache_file = cache_file
        self._ensure_cache_directory()
        self.cache = self._load_cache()
        # Initialize wikidata_cache structure if empty
        self._init_cache_structure()

    def _init_cache_structure(self):
        """Ensure wikidata_cache has the required structure"""
        if not isinstance(self.cache, dict):
            self.cache = {}
        if 'wbgetentities' not in self.cache:
            self.cache['wbgetentities'] = {}
        if 'wbsearchentities' not in self.cache:
            self.cache['wbsearchentities'] = {}
        self._save_cache()

    def _ensure_cache_directory(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=4)

    def get_data(self, action: str, key: str, params: Dict) -> Dict:
        if action not in self.cache:
            self.cache[action] = {}

        cache_dict = self.cache[action]

        if key in cache_dict:
            if print_update: print(f"Retrieved from wikidata_cache: {action} - {key}")
            return cache_dict[key]

        # Make actual request
        result = _make_request(params)
        if print_update: print(f"Retrieved data from wikidata {action} - {key}")

        # Store in wikidata_cache
        cache_dict[key] = result
        self._save_cache()
        if print_update: print(f"Cached new result: {action} - {key}")
        return result

def _make_request(params: Dict) -> Dict:
    url = 'https://www.wikidata.org/w/api.php'
    try:
        return requests.get(url, params=params).json()
    except Exception as e:
        raise Exception(f'Error making request: {e}')

# Initialize wikidata_cache globally
wikidata_cache = WikidataCache()
print_update = False


