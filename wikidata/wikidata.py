from typing import Dict, Any
from colorama import Fore, Style
import json
from wikidata.wikidataCache import wikidata_cache


def wikidata_wbsearchentities(query_string: str, id_or_name: str = 'id') -> str:
    """Searches Wikidata entities by query string and returns ID or label.

    Makes a search request to Wikidata API to find matching entities.
    Returns either the entity ID or label name based on id_or_name parameter.
    Falls back to ID if name lookup fails.

    Args:
        query_string: Search term to find matching Wikidata entities
        id_or_name: Whether to return 'id' (default) or 'name' (label) of entity

    Returns:
        str: Either:
            - Wikidata entity ID (e.g. "Q12345")
            - Entity label name if id_or_name='name'
            - "No wikidata entry found" if no matches

    Example:
        >>> wikidata_wbsearchentities("Google")
        'Q95'
        >>> wikidata_wbsearchentities("Google", id_or_name='name')
        'Google'
    """
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query_string,
        'language': 'en',
        'profile': 'default',
        'limit': 1,
    }

    data = wikidata_cache.get_data('wbsearchentities', query_string, params)

    if not data['search']:
        # print(Fore.YELLOW +f"No Wikidata entry found for: {query_string}" + Style.RESET_ALL)
        return "No wikidata entry found"

    try:
        if id_or_name == 'name':
            return data['search'][0]['label']
    except KeyError:
        print(Fore.RED +
              f"No label for ID: {data['search'][0]['id']}" +
              Style.RESET_ALL)
    return data['search'][0]['id']


def wikidata_wbgetentities(entity_id: str, print_output: bool = False) -> Dict[str, Any]:
    """Retrieves detailed entity data from Wikidata by ID.

    Fetches labels and claims data for a Wikidata entity.
    Can optionally save the raw JSON response to file.

    Args:
        entity_id: Wikidata entity ID (e.g. "Q12345")
        print_output: Whether to save JSON response to file

    Returns:
        Dict containing entity data with structure:
        {
            'entities': {
                'Q12345': {
                    'labels': {...},
                    'claims': {...}
                }
            }
        }

    Example:
        >>> data = wikidata_wbgetentities("Q95")  # Google
        >>> print(data['entities']['Q95']['labels']['en']['value'])
        'Google'
    """
    params = {
        'action': 'wbgetentities',
        'ids': entity_id,
        'format': 'json',
        'languages': 'en',
        'props': 'labels|claims'
    }

    data = wikidata_cache.get_data('wbgetentities', entity_id, params)

    if print_output and data:
        filename = "files/wikidata/webgetentities.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"JSON data written to {filename}")

    return data
