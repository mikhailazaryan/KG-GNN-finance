from typing import Dict, Any
from colorama import init, Fore, Back, Style


import json


from stockdata2KG.files.wikidata_cache.wikidataCache import wikidata_cache

## Code partially from https://www.jcchouinard.com/wikidata-api-python/

def wikidata_wbsearchentities(query_string: str, id_or_label: str = 'id') -> str:
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query_string,
        'language': 'en',
        'profile': 'language'
    }

    # Use wikidata_cache to get data
    data = wikidata_cache.get_data('wbsearchentities', query_string, params)

    try:
        if not data['search']:
            print(Fore.LIGHTYELLOW_EX + f"No entry found from wikidata for query: {query_string}, id_or_label: {id_or_label}, returning \"No wikidata entry found\"" + Style.RESET_ALL)
            return "No wikidata entry found"
            #todo: find out which side effects this had
        if id_or_label == 'id':
            return data['search'][0]['id']
        elif id_or_label == 'name':
            return data['search'][0]['label']
        else:
            return 'Please indicate if you would like to return id or label'
    except KeyError as e:
        print(Fore.LIGHTYELLOW_EX + f"KeyError: {e} while retrieving data from wikidata for query: {query_string}, id_or_label: {id_or_label}, returning \"No id or label defined by Wikidata\"" + Style.RESET_ALL)
        return "No id or label defined by Wikidata"

def wikidata_wbgetentities(id: str, print_output: bool = False) -> Dict[str, Any]:
    params = {
        'action': 'wbgetentities',
        'ids': id,
        'format': 'json',
        'languages': 'en',
        'props': 'claims'
    }

    # Use wikidata_cache to get data
    data = wikidata_cache.get_data('wbgetentities', id, params)

    if print_output and data:
        filename = "files/initial_graph_data/webgetentities.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"JSON data written to {filename}")

    return data
