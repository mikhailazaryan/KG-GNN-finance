import json

from numpy.f2py.auxfuncs import throw_error

from stockdata2KG.wikidata import wikidata_wbgetentities, wikidata_wbsearchentities

earliest_date = "-inf"
latest_date = "+inf"

def create_placeholder_node_in_neo4j(wikidata_id, label, driver):
    # Check if node exists using wikidata_id
    check_query = """
         MATCH (n {wikidata_id: $wikidata_id})
         RETURN n
         """

    with driver.session() as session:
        result = session.run(check_query, wikidata_id=wikidata_id).single()

        # If node doesn't exist (result is None), create it
        if result is None:
            properties_dict = {
                "label" : label,
                "wikidata_id": wikidata_id,
                "placeholder" : True,
                "has_relationships": False # standard is false
                # other properties...
            }

            create_query = f"""
                CREATE (n:{label})
                SET n = $properties
                RETURN n
                """
            result = session.run(create_query, properties=properties_dict).single()

            if result and result.get("n"):
                print(f"Placeholder Node with wikidata_id: {wikidata_id} has been added to neo4j graph")
                return result
            else:
                print(f"Error while adding placeholder node with wikidata_id: {wikidata_id} to neo4j graph")
        else:
            print(
                f"Placeholder node with wikidata_id: {wikidata_id} already exists in neo4j graph and has therefore not been added")


def return_wikidata_id_of_all_placeholder_nodes(driver):
    match_placeholders_query = """
        MATCH (n)
        WHERE n.placeholder = true
        RETURN n.wikidata_id as wikidata_id
        """

    # Execute the query
    with driver.session() as session:
        results = session.run(match_placeholders_query)
        return [record.get("wikidata_id") for record in results if record.get("wikidata_id")]

def return_all_wikidata_ids_of_nodes_without_relationships(driver):
    match_without_rel_query = """
        MATCH (n)
        WHERE n.has_relationships = false
        RETURN n.wikidata_id as wikidata_id
        """

    # Execute the query
    with driver.session() as session:
        results = session.run(match_without_rel_query)
        return [record.get("wikidata_id") for record in results if record.get("wikidata_id")]

def populate_placeholder_node_in_neo4j(wikidata_id, driver):
    # Check if node exists using wikidata_id
    check_query = f"""
        MATCH (n {{wikidata_id: $wikidata_id}})
        RETURN n,  labels(n) as labels,
           CASE 
               WHEN n.placeholder IS NOT NULL THEN n.placeholder 
               ELSE false 
           END as isPlaceholder
        """

    with (driver.session() as session):
        result = session.run(check_query, wikidata_id=wikidata_id).single()

        if result is None:
            raise Exception(f"Could not find node with wikidata_id {wikidata_id} in graph")
        else:
            if result.get("isPlaceholder"):
                label = result.get("labels")[0] #could lead to errors if there are multiple with the same id
                properties_dict = get_properties_dict(wikidata_id, label)
                # Create node using properties from dictionary
                update_query = f"""
                                MATCH (n {{wikidata_id: $wikidata_id}})
                                SET n:{label}
                                SET n = $properties
                                RETURN n
                                """
                result = session.run(update_query, wikidata_id=wikidata_id, properties=properties_dict).single()
                if result and result.get("n"):
                    print(f"Placeholder Node with wikidata_id: {wikidata_id} has been populated with data in neo4j graph")
                else:
                    print(f"Error while populating placeholder node with wikidata_id: {wikidata_id} to neo4j graph")
            else:
                print(f"Populating placeholder node with wikidata_id: {wikidata_id} failed because isPlaceholder == False")

def get_properties_dict(wikidata_id, label):
    data = wikidata_wbgetentities(wikidata_id)
    #intital properties_dict is the same for all

    #todo bring name to property dict here
    try:
        if label =="Company":
             properties_dict ={
                    "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                    "inception": data["entities"][wikidata_id]["claims"]["P571"][0]["mainsnak"]["datavalue"]["value"]["time"],
                    "legal_form": "",
                    "total_assets": "",
                    "total_equity": "",
                    "total_revenue": "",
                    "net_profit": "",
                    "operating_income": "",
                    "market_cap": "",
                    "assets_under_management": "",
                    "employee_number": "",
                    "isin": data["entities"][wikidata_id]["claims"]["P946"][0]["mainsnak"]["datavalue"]["value"],
                    "wikidata_id": wikidata_id,
                    "placeholder": False,
                    "has_relationships": False,
             }
        elif label == "StockMarketIndex":
            properties_dict = {
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        elif label == "Industry":
            properties_dict ={
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        elif label =="Person":
            properties_dict ={
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "gender": "",
                "date_of_birth": "",
                "date_of_death": "",
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        elif label == "City":
            properties_dict = {
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        elif label == "Country":
            properties_dict = {
                "name": data["entities"][wikidata_id]["claims"]["P17"][0]["mainsnak"]["datavalue"]["id"],
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        elif label == "Product_or_Service":
            properties_dict = {
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            }
        else:
            raise Exception(f"Could not find label {label} in get_properties_dict")
        return properties_dict
    except KeyError as e:
        # defaulting to just searching for the name without additional information if there was a key error
        # needs to send a request to wikidata, therefore this can slow the programm down
        properties_dict = {
            "name": wikidata_wbsearchentities(wikidata_id, "name"),
            "label": label,
            "wikidata_id": wikidata_id,
            "placeholder": False,
            "has_relationships": False,
        }
        name = properties_dict["name"]
        print(f"KeyError: {e} for wikidata_id {wikidata_id}, so defaulting to only name = {name} and wikidata_id property_dict")

        return properties_dict


def create_relationships_and_placeholder_nodes_for_node_in_neo4j(org_wikidata_id, driver):
    check_query = f"""
        MATCH (n {{wikidata_id: $wikidata_id}})
        RETURN n, labels(n) as org_labels,
           CASE 
               WHEN n.placeholder IS NOT NULL THEN n.placeholder 
               ELSE false 
           END as isPlaceholder
        """

    with (driver.session() as session):
        result = session.run(check_query, wikidata_id=org_wikidata_id).single()

        if result is None:
            raise Exception(f"Could not find node with wikidata_id {org_wikidata_id} in graph")
        else:
            if not result.get("isPlaceholder"): #todo maybe I dont need to check this if its checked before in main
                org_label = result.get("org_labels")[0] #could lead to errors if there are multiple with the same id
                relationship_dict = get_relationship_dict(org_wikidata_id, org_label)

                # Process each relationship type
                for rel_type, rel_info in relationship_dict.items():
                    rel_wikidata_entries = rel_info["wikidata_entries"]
                    rel_type = rel_info["relationship_type"]
                    rel_label = rel_info["label"]
                    rel_direction = rel_info["relationship_direction"]

                    # Create placeholder nodes and relationships for each property_id
                    for rel_wikidata_entry in rel_wikidata_entries:
                        rel_wikidata_id = rel_wikidata_entry["id"] #extract only id here
                        rel_wikidata_start_time = rel_wikidata_entry["start_time"]
                        rel_wikidata_end_time = rel_wikidata_entry["end_time"]
                        create_placeholder_node_in_neo4j(rel_wikidata_id, rel_label, driver)

                        if rel_direction == "OUTBOUND":
                            source_label = org_label
                            target_label = rel_label

                            source_id = org_wikidata_id
                            target_id = rel_wikidata_id
                        elif rel_direction == "INBOUND":
                            source_label = rel_label
                            target_label = org_label

                            source_id = rel_wikidata_id
                            target_id = org_wikidata_id
                        else:
                            raise Exception(f"Relation direction {rel_direction} is not supported")

                        # Create relationship
                        create_relationship_query = f"""
                                        MATCH (source:{source_label} {{wikidata_id: $source_id}})
                                        MATCH (target:{target_label} {{wikidata_id: $target_id}})
                                            CREATE (source)-[r:{rel_type} {{
                                                start_time: $start_time,
                                                end_time: $end_time
                                                }}]->(target)
                                        RETURN source, target, r
                                        """
                        # Then update your parameters dictionary to include the new properties
                        params = {
                            "source_id": source_id,
                            "target_id": target_id,
                            "start_time": rel_wikidata_start_time,
                            "end_time": rel_wikidata_end_time
                        }

                        # Execute the query with parameters
                        session.run(create_relationship_query, params)

                # After creating relationships, update the original node's has_relationships property
                #after relationships are added, also change the has_relationship property
                update_query = """
                                MATCH (n {wikidata_id: $org_wikidata_id})
                                SET n.has_relationships = true
                              """
                session.run(update_query, org_wikidata_id=org_wikidata_id)

                        # creates double relationships when entry is duplicated (e.g. happens when company is added
                        # and removed to indices multiple times

            else:
                print(f"Creating Relationships and placeholder node for wikidata_id: {org_wikidata_id} failed because isPlaceholder == True")

def get_relationship_dict(org_wikidata_id, label):
    data = wikidata_wbgetentities(org_wikidata_id)
    try:
        if label == "Company":
            #wikidata_wbgetentities(org_wikidata_id, True)
            relationship_dict = {
                        "StockMarketIndex": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P361"),
                            "label": "StockMarketIndex",
                            "relationship_type": "LISTED_IN",
                            "relationship_direction": "OUTBOUND",
                        },
                        "Industry": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P452"),
                            "label": "Industry",
                            "relationship_type": "ACTIVE_IN",
                            "relationship_direction": "OUTBOUND"
                        },
                        "Subsidiary": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P355"),
                            "label": "Company",
                            "relationship_type": "OWNS",
                            "relationship_direction": "OUTBOUND"
                        },
                        "City": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P159"),
                            "label": "City",
                            "relationship_type": "HAS_HEADQUARTER_IN",
                            "relationship_direction": "OUTBOUND"
                        },
                        "Product_or_Service": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P1056"),
                            "label": "Product_or_Service",
                            "relationship_type": "OFFERS",
                            "relationship_direction": "OUTBOUND"
                        },
                        "Founder": { #todo make person
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P112"),
                            "label": "Person",
                            "relationship_type": "FOUNDED",
                            "relationship_direction": "INBOUND"
                        },
                        "Manager": { #todo make person
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P169|P1037"),
                            "label": "Person",
                            "relationship_type": "MANAGES",
                            "relationship_direction": "INBOUND"
                        },
                        "Board_Member": { #todo make person
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P3320"),
                            "label": "Person",
                            "relationship_type": "IS_PART_OF_BOARD",
                            "relationship_direction": "INBOUND"
                        },
            }
            return relationship_dict
        elif label == "StockMarketIndex":
            relationship_dict = {} #todo
        elif label == "Industry":
            relationship_dict = {} #todo
        elif label == "City":
            relationship_dict = {
                        "Country" : {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P17"),
                            "label": "Country",
                            "relationship_type": "LOCATED_IN",
                            "relationship_direction": "OUTBOUND"
                        }
            } #todo
        elif label == "Country":
            relationship_dict = {} #todo
        elif label == "Product_or_Service":
            relationship_dict = {} #todo
        elif label == "Person":
            relationship_dict = {} #todo
        else:
            raise Exception(f"Label {label} is not supported")
        return relationship_dict
    except KeyError as e:
        raise KeyError(f"KeyError Could not access key {e}")



def get_all_wikidata_entries_as_list_of_dict(data, wikidata_id, property_ids):
    result = []
    for property_id in property_ids.split("|"):
        print("property_ids: " + property_ids + ", property_id: " + property_id)
        try:
            for entry in data["entities"][wikidata_id]["claims"][property_id]:
                try:
                    start_time = entry["qualifiers"]["P580"][0]["datavalue"]["value"]["time"] #start time
                except:
                    start_time = earliest_date
                try:
                    end_time = entry["qualifiers"]["P582"][0]["datavalue"]["value"]["time"]
                except:
                    end_time = latest_date
                result.append({"id" :entry["mainsnak"]["datavalue"]["value"]["id"], "start_time" : start_time, "end_time": end_time})
        except KeyError as e:
            print(f"Key Error {e} for wikidata_id {wikidata_id}, skipping this key")
    return result







def initialize_graph(json_path, driver):
    with open(json_path, 'r') as f:
        data = json.load(f)

    print(f"Initializing graph from {json_path}")
    print(data.get("name"))


    with driver.session() as session:
        session.run("MATCH(n) DETACH DELETE n")
        create_nodes_and_relationships(session, data)

def create_nodes_and_relationships(session, data):
    # Create the nodes
    for key, value in data.items():
        label = value["label"]
        for properties in value["nodes"]:
        #properties = value["nodes"][0]

            # Use MERGE to create or match the node
            node_query = f"""
                MERGE (n:{label} {{name: $name}})
                SET n += $properties
                RETURN n
            """
            session.run(node_query, {"name": properties["name"], "properties": properties})

    # Create relationships
    for key, value in data.items():
        source_label = value["label"]
        for source_name in value["nodes"]:
            source_name = source_name["name"]

            for relationship in value.get("relationships", []):
                rel_type = relationship["type"]
                target_key = relationship["target"]
                target_label = data[target_key]["label"]
                #target_name = data[target_key]["nodes"][0]["name"]
                for target_node in data[target_key]["nodes"]:
                    target_name = target_node["name"]  # Extract the target node's name

                    rel_query = f"""
                        MATCH (source:{source_label} {{name: $source_name}})
                        MATCH (target:{target_label} {{name: $target_name}})
                        MERGE (source)-[:{rel_type}]->(target)
                    """
                    session.run(rel_query, {"source_name": source_name, "target_name": target_name})



