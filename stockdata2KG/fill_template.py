import json

from stockdata2KG.wikidata import wikidata_wbsearchentities


# copy template to template_with_ids.json
def fill_template(id_of_company, wikidata):

     # copies template.json to template_with_ids.json
     with open("files/initial_graph_data/template.json", 'r') as f:
         data = json.load(f)

     with open("files/initial_graph_data/template_with_ids.json", 'w') as f:
         json.dump(data, f, indent=4)


     # replace the IDs such as "P946" with the correct value
     with open('files/initial_graph_data/template_with_ids.json', 'r') as f:
         template_json = json.load(f)

     for key, value in template_json.items():
     ### iterates over key, value pairs in the template_json
         if isinstance(value, dict):
         ### if value is a dicts, iterate over "properties" key, value pairs

             #print("key: " + str(key))
            for key2, id in value["properties"].items():
                #print("key2: " + str(key2))
                ### if id has a string value, continue, else skip
                if id != "":
                    #print("value: " + str(id))
                    for id in id.split("|"):
                        ### split this by "|". This is so that different wikidata-ids for same
                        ### meaning are tried in a try-except clause. This is important when e.g. one wikidata entry has
                #       ## "manager" and the other has "ceo"
                        try:
                            #print("id: " + str(id))
                            new_value = wikidata["entities"][id_of_company]["claims"][id][0]["mainsnak"]["datavalue"]["value"]
                            ### extract the value from wikidata
                            if isinstance(new_value, str):
                            ### if it's a string, we are done an just replace the current value with the new one
                                template_json[key]["properties"][key2] = new_value
                            elif isinstance(new_value, dict):
                            ### if its a dict, then we replace the current value with wikidata_websearchentity
                            ### result of the 'id' of the dict
                                new_value = wikidata_wbsearchentities(new_value['id'], 'label'),
                                template_json[key]["properties"][key2] = new_value[0]
                        except: pass


     with open('files/initial_graph_data/template_with_ids.json', 'w') as f:
     ### we copy the json back into template_with_ids.json
         json.dump(template_json, f, indent=4)