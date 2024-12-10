from typing import Dict, Any

import requests
import json
import warnings

from stockdata2KG.files.wikidataCache import wikidata_cache

## Code partially from https://www.jcchouinard.com/wikidata-api-python/

def wikidata_wbsearchentities(query_string: str, id_or_label: str = 'id') -> str:
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query_string,
        'language': 'en',
        'profile': 'language'
    }

    # Use cache to get data
    data = wikidata_cache.get_data('wbsearchentities', query_string, params)

    try:
        if id_or_label == 'id':
            return data['search'][0]['id']
        if id_or_label == 'name':
            return data['search'][0]['label']
        else:
            return 'Please indicate if you would like to return id or label'
    except KeyError as e:
        warnings.warn(
            f"KeyError: {e} while retrieving data from wikidata for query: {query_string}, id_or_label: {id_or_label}, returning \"No label defined by Wikidata\"")
        return "No label defined by Wikidata"

def wikidata_wbgetentities(id: str, print_output: bool = False) -> Dict[str, Any]:
    params = {
        'action': 'wbgetentities',
        'ids': id,
        'format': 'json',
        'languages': 'en',
        'props': 'claims'
    }

    # Use cache to get data
    data = wikidata_cache.get_data('wbgetentities', id, params)

    if print_output and data:
        filename = "files/initial_graph_data/webgetentities.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"JSON data written to {filename}")

    return data
