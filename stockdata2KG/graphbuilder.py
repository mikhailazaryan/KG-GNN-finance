import json
import warnings
from datetime import datetime, timezone
from colorama import init, Fore, Back, Style
from neo4j import GraphDatabase
from stockdata2KG.wikidata import wikidata_wbgetentities, wikidata_wbsearchentities

def _create_new_node(wikidata_id, name, label, placeholder, has_relationships, driver,):
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
                "name" : name,
                "label": label,
                "wikidata_id": wikidata_id,
                "placeholder": placeholder,
                "has_relationships": has_relationships  # standard is false
                # other properties...
            }

            create_query = f"""
                    CREATE (n:{label})
                    SET n = $properties
                    RETURN n
                    """
            result = session.run(create_query, properties=properties_dict).single()

            if result and result.get("n"):
                print(
                    Fore.GREEN + f"Node with placeholder = {placeholder} and wikidata_id: '{wikidata_id}' has been added to neo4j graph" + Style.RESET_ALL)
                return result
            else:
                raise Exception(f"Error while adding node with wikidata_id: {wikidata_id} to neo4j graph")
        else:
            print(
                Fore.GREEN + f"Node with wikidata_id: {wikidata_id} already exists in neo4j graph and has therefore not been added" + Style.RESET_ALL)

def create_relationship_in_neo4j(rel_direction: str, rel_type: str, org_label: str, rel_label: str, org_wikidata_id: str, rel_wikidata_id: str, rel_wikidata_start_time: str,  rel_wikidata_end_time: str, driver):
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

    with driver.session() as session:
        result = session.run(create_relationship_query, params)
        records = list(result)
        if records:
            print(f"Successfully created relationship of type {rel_type}")
            return True
        else:
            print("No relationship created for params: '{params}'. Source or target node might not exist.")

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
            raise Exception(f"Could not find placeholder node with wikidata_id {wikidata_id} in graph")
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
                    print(Fore.GREEN + f"Placeholder Node with wikidata_id: {wikidata_id} has been populated with data in neo4j graph" + Style.RESET_ALL)
                else:
                    raise Exception(f"Error while populating placeholder node with wikidata_id: {wikidata_id} to neo4j graph")
            else:
                print(Fore.RED + f"Populating placeholder node with wikidata_id: {wikidata_id} failed because isPlaceholder == False" + Style.RESET_ALL)

def get_properties_dict(wikidata_id, label,):
    data = wikidata_wbgetentities(wikidata_id)

    #todo bring name to property dict here
    try:
        if label =="Company" or label == "InitialCompany":
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
        elif label == "Industry_Field":
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
        print(Fore.LIGHTYELLOW_EX + f"KeyError: {e} for wikidata_id {wikidata_id}, so defaulting to only name = {name} and wikidata_id property_dict" + Style.RESET_ALL)
        return properties_dict

def check_if_node_exists_in_graph(wikidata_id = None, name = None, driver=None):
    if wikidata_id is not None:
        check_query = f"""
                MATCH (n {{wikidata_id: $wikidata_id}})
                RETURN n, labels(n) as label, n.name as name,
                   CASE 
                       WHEN n.placeholder IS NOT NULL THEN n.placeholder 
                       ELSE false 
                   END as isPlaceholder
                """
        with (driver.session() as session):
            result = session.run(check_query, wikidata_id=wikidata_id).single()
            if result is not None:
                return {"name": result.get("name"), "label": result.get("label")[0], "isPlaceholder": result.get("isPlaceholder")}
    elif name is not None:
        check_query = f"""
                        MATCH (n {{name: $name}})
                        RETURN n, labels(n) as label, n.wikidata_id as wikidata_id,
                           CASE 
                               WHEN n.placeholder IS NOT NULL THEN n.placeholder 
                               ELSE false 
                           END as isPlaceholder
                        """
        with (driver.session() as session):
            result = session.run(check_query, name=name).single()
            if result is not None:
                return {"wikidata_id": result.get("wikidata_id"), "label": result.get("label")[0], "isPlaceholder": result.get("isPlaceholder")}
    elif name is None and wikidata_id is not None:
        raise Exception("Please specify at least one of name or wikidata_id")
    return False

def create_relationships_and_placeholder_nodes_for_node_in_neo4j(org_wikidata_id: str, from_date_of_interest: datetime, until_date_of_interest: datetime, nodes_to_include: list ,driver):
    result = check_if_node_exists_in_graph(wikidata_id=org_wikidata_id, driver=driver)

    if result is False:
        raise Exception(f"Could not find node with wikidata_id {org_wikidata_id} in graph")
    else:
        if not result.get("isPlaceholder"): #todo maybe I dont need to check this if its checked before in main
            org_label = result.get("label")
            relationship_dict = get_relationship_dict(org_wikidata_id, org_label)

            # Process each relationship type
            for rel_type, rel_info in relationship_dict.items():
                rel_wikidata_entries = rel_info["wikidata_entries"]
                rel_type = rel_info["relationship_type"]
                rel_label = rel_info["label"]
                rel_direction = rel_info["relationship_direction"]

                if rel_label in nodes_to_include:

                    # Create placeholder nodes and relationships for each property_id
                    for rel_wikidata_entry in rel_wikidata_entries:
                        rel_wikidata_id = rel_wikidata_entry["id"]
                        rel_wikidata_start_time = rel_wikidata_entry["start_time"]
                        rel_wikidata_end_time = rel_wikidata_entry["end_time"]
                        try:
                            if is_date_in_range(rel_wikidata_start_time, rel_wikidata_end_time, from_date_of_interest, until_date_of_interest):
                                _create_new_node(rel_wikidata_id, "", label=rel_label, placeholder=True, has_relationships=False, driver=driver)
                                create_relationship_in_neo4j(rel_direction, rel_type, org_label, rel_label, org_wikidata_id, rel_wikidata_id, rel_wikidata_start_time, rel_wikidata_end_time, driver)
                        except ValueError as e:
                            raise ValueError(f"{e}")

            # After creating relationships, update the original node's has_relationships property
            update_query = """
                            MATCH (n {wikidata_id: $org_wikidata_id})
                            SET n.has_relationships = true
                          """
            with (driver.session() as session):
                session.run(update_query, org_wikidata_id=org_wikidata_id)
        else:
            print(Fore.RED + f"Creating Relationships and placeholder node for wikidata_id: {org_wikidata_id} failed because isPlaceholder == True" + Style.RESET_ALL)

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
                        "Industry_Field": {
                            "wikidata_entries": get_all_wikidata_entries_as_list_of_dict(data, org_wikidata_id, "P452"),
                            "label": "Industry_Field",
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
        elif label == "Industry_Field":
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

def get_all_wikidata_entries_as_list_of_dict(data: dict, wikidata_id: str, property_ids: str) -> list[dict[str, datetime, datetime]]:
    result = []
    for property_id in property_ids.split("|"):
        try:
            for i, entry in enumerate(data["entities"][wikidata_id]["claims"][property_id]):
                try:
                    start_time = entry["qualifiers"]["P580"][0]["datavalue"]["value"]["time"] #start time
                    try:
                        start_time = parse_datetime_to_iso(start_time)
                    except:
                        warnings.warn(f"start_time unable to parse start_time: ({start_time}), so defaulting to datetime.min. Exception: {e}")
                except Exception as e:
                    print(Fore.LIGHTYELLOW_EX + f"Wikidata has no start_time for wikidata_id: {wikidata_id}, property_id: {property_id} and at list[{i}], so defaulting to datetime.min" + Style.RESET_ALL)
                    start_time = datetime.min.replace(tzinfo=timezone.utc)
                try:
                    end_time = entry["qualifiers"]["P582"][0]["datavalue"]["value"]["time"]
                    try:
                        end_time = parse_datetime_to_iso(end_time)
                    except Exception as e:
                        warnings.warn(f"start_time unable to parse end_time: ({end_time}), so defaulting to datetime.min. Exception: {e}")
                except:
                    print(Fore.LIGHTYELLOW_EX + f"Wikidata has no end_time for wikidata_id: {wikidata_id}, property_id: {property_id} and at list[{i}], so defaulting to datetime.max" + Style.RESET_ALL)
                    end_time = datetime.max.replace(tzinfo=timezone.utc)
                if start_time == None or end_time == None:
                    raise Exception(f"Wikidata has no start_time {start_time} or end_time {end_time} for wikidata_id: {wikidata_id}, property_id: {property_id}, list[{i}]")
                result.append({"id" :entry["mainsnak"]["datavalue"]["value"]["id"], "start_time" : start_time, "end_time": end_time})
        except KeyError as e:
            print(Fore.LIGHTYELLOW_EX + f"Key Error {e} for wikidata_id {wikidata_id}, skipping this key" + Style.RESET_ALL)
    return result

def parse_datetime_to_iso(date_string: str) -> datetime:
    try:
        if date_string.startswith('+'):
            dt = datetime.strptime(date_string.lstrip('+').rstrip('Z'),"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        elif date_string.startswith('-'):
            dt = datetime.min.replace(tzinfo=timezone.utc) # in case there are datetimes from before Christ
        else:
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S%z").replace(tzinfo=timezone.utc)
        return dt
    except ValueError as e:
        try:
            if "-00" in date_string:
                fixed_date = date_string.replace("-00", "-01")
                print(Fore.LIGHTYELLOW_EX + f"date_string: {date_string} contained invalid month or day information, changed to: {fixed_date}" + Style.RESET_ALL)
                return parse_datetime_to_iso(fixed_date)
        except:
            raise ValueError(f"Could not parse date string {date_string} to datetime format. ValueError: {e}")

def is_date_in_range(rel_wikidata_start_time: datetime, rel_wikidata_end_time: datetime, from_date_of_interest: datetime, until_date_of_interest: datetime) -> bool:
        if rel_wikidata_end_time < from_date_of_interest or rel_wikidata_start_time > until_date_of_interest:
            return False
        else:
            return True

def build_graph_from_initial_node(node_name, label, date_from, date_until, nodes_to_include, search_depth, driver):
    # initialize first placeholder node of company name
    wikidata_id_of_company = wikidata_wbsearchentities(node_name)
    _create_new_node(wikidata_id_of_company, node_name, label, placeholder=True, has_relationships=False,driver=driver)
    populate_placeholder_node_in_neo4j(wikidata_id_of_company, driver)

    # iteratively adding nodes and relationships
    for i in range(search_depth):
        print(Fore.BLUE + f"\n---Started building graph for {node_name} on depth {i}---\n" + Style.RESET_ALL)
        for wikidata_id in return_all_wikidata_ids_of_nodes_without_relationships(driver):
            create_relationships_and_placeholder_nodes_for_node_in_neo4j(org_wikidata_id=wikidata_id,
                                                                         from_date_of_interest=date_from,
                                                                         until_date_of_interest=date_until,
                                                                         nodes_to_include=nodes_to_include,
                                                                         driver=driver)

        for wikidata_id in return_wikidata_id_of_all_placeholder_nodes(driver):
            populate_placeholder_node_in_neo4j(wikidata_id, driver)
        print(Fore.BLUE + f"\n---Finished building graph for {node_name} on depth {i}---\n" + Style.RESET_ALL)

def reset_graph(driver):
    ## Setup connection to Neo4j
    neo4j_uri = "neo4j://localhost:7687"
    username = "neo4j"
    password = "neo4jtest"

    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

    with driver.session() as session:
        session.run("MATCH(n) DETACH DELETE n")

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

def build_demo_graph(driver):
    company_query = """
       CREATE (c:Company {
           name: $company_name,
           wikidata_id: $wikidata_id,
           inception: datetime($inception),
           isin: $isin,
           total_assets: $total_assets,
           operating_income: $operating_income,
           assets_under_management: $assets_under_management,
           legal_form: $legal_form,
           market_cap: $market_cap,
           total_equity: $total_equity,
           total_revenue: $total_revenue,
           employee_number: $employee_number,
           net_profit: $net_profit,
           has_relationships: $has_relationships,
           placeholder: $placeholder
       })
       """

    company_params = {
        "company_name": "Allianz SE",
        "wikidata_id": "Q487292",
        "inception": "1890-02-05T00:00:00Z",
        "isin": "DE0008404005",
        "total_assets": "",
        "operating_income": "",
        "assets_under_management": "",
        "legal_form": "",
        "market_cap": "",
        "total_equity": "",
        "total_revenue": "",
        "employee_number": "",
        "net_profit": "",
        "has_relationships": True,
        "placeholder": False
    }

    # Create city node
    city_query = """
       CREATE (city:City {
           name: $city_name,
           wikidata_id: $wikidata_id,
           has_relationships: $has_relationships,
           placeholder: $placeholder
       })
       """

    city_params = {
        "city_name": "Munich",
        "wikidata_id": "Q1726",
        "has_relationships": False,
        "placeholder": False
    }

    # Create relationship
    relationship_query = """
       MATCH (n:Company {name: $company_name})
       MATCH (c:City {name: $city_name})
       CREATE (n)-[r:HAS_HEADQUARTER_IN {
           start_time: datetime($start_time),
           end_time: datetime($end_time)
       }]->(c)
       """

    relationship_params = {
        "company_name": "Allianz SE",
        "city_name": "Munich",
        "start_time": "0001-01-01T00:00:00Z",
        "end_time": "9999-12-31T23:59:59.999999000Z"
    }

    # Execute queries
    with driver.session() as session:
        session.run(company_query, **company_params)
        session.run(city_query, **city_params)
        session.run(relationship_query, **relationship_params)




