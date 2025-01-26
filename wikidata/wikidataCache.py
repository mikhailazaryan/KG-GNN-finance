import json
import os
import warnings
import time
import requests
from typing import Dict

os.environ['GRPC_VERBOSITY'] = 'ERROR'


class WikidataCache:
    # Class-level counters
    cache_hits = 0
    internet_retrievals = 0
    request_times = []

    def __init__(self, cache_file='files/wikidata_cache/wikidata.json'):
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
                print(f"Retrieved from wikidata: {action} - {key}")
            WikidataCache.cache_hits += 1
            return cache_dict[key]

        # Time the request
        start_time = time.time()

        # Make actual request
        time.sleep(
            0.0)  # no sleep time as this seems to be the fastest, no obvious punishment for making a lot of requests
        result = _make_request(params)

        # result = _strip_results(result)

        # Calculate request time and store it
        request_time = time.time() - start_time
        # print(f"Request time: {request_time}")
        WikidataCache.request_times.append(request_time)

        if print_update:
            print(f"Retrieved data from wikidata {action} - {key}")
        WikidataCache.internet_retrievals += 1

        # Store in wikidata
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
            cache_hit_ratio = (WikidataCache.cache_hits / (
                        WikidataCache.cache_hits + WikidataCache.internet_retrievals) * 100).__round__(3)
            print(f"Which is a cache hit ratio of {cache_hit_ratio}%\n\n")

        if WikidataCache.internet_retrievals > 0:
            avg_request_time = sum(WikidataCache.request_times) / len(WikidataCache.request_times)
            max_request_time = max(WikidataCache.request_times)
            min_request_time = min(WikidataCache.request_times)
            print(f"Average request time: {avg_request_time:.2f} seconds")
            print(f"Max request time: {max_request_time:.2f} seconds")
            print(f"Min request time: {min_request_time:.2f} seconds")

    @classmethod
    def strip_cache(cls, cache_instance=None):
        """
        Public method to strip unnecessary keys from the cache.
        Can be called either on an instance or as a class method.
        """
        if cache_instance is None:
            cache_instance = cls(cache_file='files/wikidata_cache/wikidata.json')

        allowed_keys = {'P17', 'P452', 'P1056', 'P108', 'P361', 'P169', 'P946',
                        'P3320', 'P570', 'P1830', 'P373', '127', 'P569', 'P112',
                        'P159', 'P1037', 'P571', 'P355', 'P2403', 'P2137', 'P2139', 'P2295', 'P3362', 'P2226', 'P749',
                        'P749', 'P4103', 'P1128'}

        try:
            if 'wbgetentities' in cache_instance.cache:
                for entry_id, entry_data in cache_instance.cache['wbgetentities'].items():
                    if ('entities' in entry_data and
                            entry_id in entry_data['entities'] and
                            'claims' in entry_data['entities'][entry_id]):

                        claims = entry_data['entities'][entry_id]['claims']
                        keys_to_strip = [key for key in claims.keys() if key not in allowed_keys]

                        for key in keys_to_strip:
                            # claims.pop(key)
                            cache_instance.cache['wbgetentities'][entry_id]["entities"][entry_id]["claims"].pop(key)

            cache_instance._save_cache(cache_instance.cache)
            print("Cache successfully stripped")

        except Exception as e:
            print(f"Error while stripping cache: {e}")


def _make_request(params: Dict) -> Dict:
    url = 'https://www.wikidata.org/w/api.php'
    try:
        result = requests.get(url, params=params).json()
        return result
    except Exception as e:
        raise Exception(f'Error making request: {e}')


# Initialize wikidata globally
wikidata_cache = WikidataCache()
print_update = False
