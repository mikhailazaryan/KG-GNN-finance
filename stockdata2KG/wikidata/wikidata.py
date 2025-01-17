from typing import Dict, Any
from colorama import Fore, Style
import json
from stockdata2KG.wikidata.wikidataCache import wikidata_cache


## Code partially from https://www.jcchouinard.com/wikidata-api-python/

def wikidata_wbsearchentities(query_string: str, id_or_name: str = 'id') -> str:
    """ return id if no name found, even if id_or_name is 'name'"""

    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query_string,
        'language': 'en',
        'profile': 'default',
        'limit': 1,
    }

    # Use wikidata to get data
    data = wikidata_cache.get_data('wbsearchentities', query_string, params)


    if not data['search']:
        print(Fore.YELLOW + f"No entry found from wikidata for query: {query_string}, id_or_name: {id_or_name}, returning \"No wikidata entry found\"" + Style.RESET_ALL)
        return "No wikidata entry found"
    try:
        if id_or_name == 'name':
            return data['search'][0]['label']
    except KeyError:
        print(Fore.RED + f"No name specified for wikidata entry: {data['search'][0]['id']}, returning wikidata_id as name instead" + Style.RESET_ALL)
    return data['search'][0]['id']


def wikidata_wbgetentities(id: str, print_output: bool = False) -> Dict[str, Any]:
    params = {
        'action': 'wbgetentities',
        'ids': id,
        'format': 'json',
        'languages': 'en',
        'props': 'labels|claims'
    }

    # Use wikidata to get data
    data = wikidata_cache.get_data('wbgetentities', id, params)

    if print_output and data:
        filename = "files/initial_graph_data/webgetentities.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"JSON data written to {filename}")

    return data
