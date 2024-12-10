import json

from numpy.f2py.auxfuncs import throw_error

from stockdata2KG.wikidata import wikidata_wbgetentities, wikidata_wbsearchentities


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
            # create placeholder node with only the wikidata_id
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
            else:
                print(f"Error while adding placeholder node with wikidata_id: {wikidata_id} to neo4j graph")
        else:
            print(
                f"Placeholder node with wikidata_id: {wikidata_id} already exists in neo4j graph and has therefore not been added")

    return result

def return_all_placeholder_node_wikidata_ids(driver):
    match_placeholders_query = """
        MATCH (n)
        WHERE n.placeholder = true
        RETURN n.wikidata_id as wikidata_id
        """

    # Execute the query
    with driver.session() as session:
        results = session.run(match_placeholders_query)
        return [record.get("wikidata_id") for record in results if record.get("wikidata_id")]

def return_all_nodes_without_relationships(driver):
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
    properties_dict = {
                    }
    #todo bring name to property dict here
    try:
        if label in ("Company", "Subsidiary"):
             properties_dict.update({
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
             })
        elif label == "StockMarketIndex":
            properties_dict.update({
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            })
        elif label == "Industry":
            properties_dict.update({
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            })
        elif label in ("Founder", "Manager", "Board_Member"):
            properties_dict.update({
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                "gender": "",
                "date_of_birth": "",
                "date_of_death": "",
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            })
        elif label == "City":
            properties_dict.update({
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            })
        elif label == "Product_or_Service":
            properties_dict.update({
                "name": data["entities"][wikidata_id]["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"],
                #todo more information
                "wikidata_id": wikidata_id,
                "placeholder": False,
                "has_relationships": False,
            })
        else:
            raise Exception(f"Could not find label {label} in get_properties_dict")
        return properties_dict
    except KeyError as e:
        # defaulting to just searching for the name without additional information if there was a key error
        # needs to send a request to wikidata, therefore this can slow the programm down
        print(f"KeyError: {e} for wikidata_id {wikidata_id}, so defaulting to only name and wikidata_id property_dict")
        properties_dict = {
            "name": wikidata_wbsearchentities(wikidata_id, "name"),
            "label": label,
            "wikidata_id": wikidata_id,
            "placeholder": False,
            "has_relationships": False,
        }
        return properties_dict



def create_relationships_and_placeholder_nodes_for_node(org_wikidata_id, driver):
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
                #todo: create new nodes with all property_ids as placeholder nodes (function for that exists) and add the relationship to each node

                # Process each relationship type
                for rel_label, rel_info in relationship_dict.items():
                    rel_wikidata_ids = rel_info["wikidata_ids"]
                    rel_type = rel_info["relationship_type"]
                    rel_direction = rel_info["relationship_direction"]

                    # Create placeholder nodes and relationships for each property_id
                    for rel_wikidata_id in rel_wikidata_ids:
                        # Create placeholder node
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
                                        CREATE (source)-[r:{rel_type}]->(target)
                                        RETURN source, target, r
                                        """
                        session.run(create_relationship_query,source_id=source_id, target_id=target_id).single()
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


def get_all_wikidata_ids_as_list(data, wikidata_id, property_id):
    result = []
    try:
        for entry in data["entities"][wikidata_id]["claims"][property_id]:
            result.append(entry["mainsnak"]["datavalue"]["value"]["id"])  # "P361",
    except KeyError as e:
        print(f"Key Error {e} for wikidata_id {wikidata_id}, skipping this key")
    return result


def get_relationship_dict(org_wikidata_id, label):
    data = wikidata_wbgetentities(org_wikidata_id)
    try:
        if label in ("Company", "Subsidiary"):
            wikidata_wbgetentities(org_wikidata_id, True)
            relationship_dict = {
                        "StockMarketIndex": {
                            "wikidata_ids": get_all_wikidata_ids_as_list(data, org_wikidata_id, "P361"),
                            "relationship_type": "LISTED_IN",
                            "relationship_direction": "OUTBOUND",
                        },
                        "Industry": {
                            "wikidata_ids": get_all_wikidata_ids_as_list(data, org_wikidata_id, "P452"),
                            "relationship_type": "ACTIVE_IN",
                            "relationship_direction": "OUTBOUND"
                        },
                        "Subsidiary": {
                            "wikidata_ids": get_all_wikidata_ids_as_list(data, org_wikidata_id, "P355"),
                            "relationship_type": "OWNS",
                            "relationship_direction": "OUTBOUND"
                        },
                        "City": {
                            "wikidata_ids": get_all_wikidata_ids_as_list(data, org_wikidata_id, "P159"),
                            "relationship_type": "HAS_HEADQUARTER_IN",
                            "relationship_direction": "OUTBOUND"
                        },
                        "Product_or_Service": {
                            "wikidata_ids": get_all_wikidata_ids_as_list(data, org_wikidata_id, "P1056"),
                            "relationship_type": "OFFERS",
                            "relationship_direction": "OUTBOUND"
                        }

            }
            return relationship_dict
        elif label == "StockMarketIndex":
            relationship_dict = {} #todo
        elif label == "Industry":
            relationship_dict = {} #todo
        elif label == "City":
            relationship_dict = {} #todo
        elif label == "Product_or_Service":
            relationship_dict = {} #todo
        else:
            raise Exception(f"Label {label} is not supported")
        return relationship_dict
    except KeyError as e:
        raise KeyError(f"KeyError Could not access key {e}")












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



