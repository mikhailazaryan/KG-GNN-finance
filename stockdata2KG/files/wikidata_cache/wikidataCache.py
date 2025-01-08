import json
import os
import warnings

import requests
from typing import Dict

# this code is partly written with Claude 3.5 Sonnet because I did not want to code a custom caching function,
# party of this code are custom to adapt it to the wikidata api

class WikidataCache:
    # Class-level counters
    cache_hits = 0
    internet_retrievals = 0

    def __init__(self, cache_file='files/wikidata_cache/wikidata_cache.json'):
        self.cache_file = cache_file
        self._ensure_cache_directory()
        self.cache = self._load_cache()

    def _init_cache_structure(self) -> Dict:
        cache = {
            'wbgetentities': {},
            'wbsearchentities': {}
        }
        self._save_cache(cache)  # Save the fresh structure
        return cache

    def _ensure_cache_directory(self):
        directory = os.path.dirname(self.cache_file)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        if not os.access(directory, os.W_OK):
            print(f"Warning: No write permission in {directory}")

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Cache file content length: {len(content)}")
                    if len(content) == 0:
                        print("Cache file is empty")
                        return self._init_cache_structure()

                    # Try to parse the JSON
                    try:
                        cache_data = json.loads(content)
                        return cache_data
                    except json.JSONDecodeError as e:
                        warnings.warn(f"Cache reset due to JSON error: {e}")
                        print(f"Error position: line {e.lineno}, column {e.colno}")
                        print(f"Error message: {e.msg}")

                        # Backup corrupted file
                        backup_file = f"{self.cache_file}.corrupted"
                        os.rename(self.cache_file, backup_file)
                        print(f"Corrupted cache backed up to: {backup_file}")

                        return self._init_cache_structure()
            except Exception as e:
                print(f"Unexpected error reading cache: {e}")
                return self._init_cache_structure()
        return self._init_cache_structure()

    def _save_cache(self, cache_data=None):
        if cache_data is None:
            cache_data = self.cache
        try:
            # Write to temporary file first
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4, ensure_ascii=False)
            # Atomic replace
            os.replace(temp_file, self.cache_file)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_data(self, action: str, key: str, params: Dict) -> Dict:
        if action not in self.cache:
            self.cache[action] = {}

        cache_dict = self.cache[action]

        if key in cache_dict:
            if print_update:
                print(f"Retrieved from wikidata_cache: {action} - {key}")
            WikidataCache.cache_hits += 1
            return cache_dict[key]

        # Make actual request
        result = _make_request(params)
        if print_update:
            print(f"Retrieved data from wikidata {action} - {key}")
        WikidataCache.internet_retrievals += 1

        # Store in wikidata_cache
        cache_dict[key] = result
        self._save_cache()
        if print_update:
            print(f"Cached new result: {action} - {key}")
        return result

    @staticmethod
    def print_current_stats():
        print(f"\n--- Cache Statistics ---")
        print(f"Cache Hits: {WikidataCache.cache_hits}")
        print(f"Internet Retrievals: {WikidataCache.internet_retrievals}")
        total_requests = WikidataCache.cache_hits + WikidataCache.internet_retrievals
        print(f"Total requests: {total_requests}")
        if WikidataCache.cache_hits > 0 or WikidataCache.internet_retrievals > 0:
            cache_hit_ratio = (WikidataCache.cache_hits / (WikidataCache.cache_hits + WikidataCache.internet_retrievals) * 100).__round__(3)
            print(f"Which is a cache hit ratio of {cache_hit_ratio}%\n\n")

def _make_request(params: Dict) -> Dict:
    url = 'https://www.wikidata.org/w/api.php'
    try:
        return requests.get(url, params=params).json()
    except Exception as e:
        raise Exception(f'Error making request: {e}')

# Initialize wikidata_cache globally
wikidata_cache = WikidataCache()
print_update = False


