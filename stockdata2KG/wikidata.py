import requests
import json

## Code partially from https://www.jcchouinard.com/wikidata-api-python/

def wikidata_wbsearchentities(query_string, id_or_label):
    # Name of the File for the initial Websearch entities
    filename = "files/initial_graph_data/websearchentities.json"

    # What text to search for
    query = query_string

    # Which parameters to use
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query,
        'language': 'en',
        'profile' : 'language'
    }
    data = retrieve_from_wikidata(params)

    # Return only the ID of the wikidata entity
    if id_or_label == 'id':
        return data['search'][0]['id']
    if id_or_label == 'label':
        return data['search'][0]['label']
    else:
        return 'Please indicate if you would like to return id or label'

def wikidata_wbgetentities(id):
    # Name of the File for the initial Websearch entities
    filename = "files/initial_graph_data/webgetentities.json"

    # Which parameters to use
    params = {
        'action': 'wbgetentities',
        'ids': id,
        'format': 'json',
        'languages': 'en',
        'props': 'claims'
    }
    data = retrieve_from_wikidata(params)

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"JSON data written to {filename}")

    return data

def retrieve_from_wikidata(params):
    data = None,

    # Fetch API
    url = 'https://www.wikidata.org/w/api.php'
    try:
        data = requests.get(url, params=params).json()
    except:
        print('There was and error')
    return data

