from datetime import datetime, timezone
from neo4j import Driver
from colorama import Fore, Style
from typing import Optional, Dict, Union, List, Any, Tuple
from wikidata.wikidata import wikidata_wbgetentities, wikidata_wbsearchentities

max_branching_factor = 12


def build_graph_from_root(root_name: str, root_label: str, date_range: Tuple[datetime, datetime],
                          included_node_types: List[str], max_depth: int, driver: Driver) -> str:
    """
    Builds a graph network from a root node, expanding relationships to specified depth.

    Creates nodes and relationships in Neo4j graph based on Wikidata information.
    Starting from a root node, expands the graph by creating related nodes and
    relationships that fall within the specified date range and node types.

    Args:
        root_name: Name of the root node to start graph from
        root_label: Type/label of the root node
        date_range: Tuple of (start_date, end_date) to filter relationships
        included_node_types: List of node types to include in graph
        max_depth: Maximum depth of graph expansion
        driver: Neo4j driver instance

    Returns:
        str: Wikidata ID of the root node
    """

    # Create root node
    root_id = wikidata_wbsearchentities(root_name)
    properties = build_node_properties(root_id, root_label, root_name)
    queue = [create_new_node(root_id, root_label, properties, driver)]
    date_from, date_until = date_range

    # Build graph iteratively
    for level in range(max_depth):
        print(Fore.BLUE + f"\--Building {root_name} graph: depth {level}---" + Style.RESET_ALL)

        next_queue = []
        for node_id in queue:
            if not node_id:
                continue

            # Get current node info
            node = find_node_by_wikidata_id(node_id, driver)
            if not node:
                raise ValueError(f"Node {node_id} not found in graph")

            # Process relationships
            relationships = _get_relationship_dict(node_id, node.get("label")).items()
            for _, rel_info in relationships:
                if rel_info["label"] not in included_node_types:
                    continue

                # Create related nodes and relationships
                for rel in rel_info["wikidata_entries"]:
                    if not _is_date_in_range(
                            rel["start_time"],
                            rel["end_time"],
                            date_from,
                            date_until
                    ):
                        continue

                    # Create new node
                    properties = build_node_properties(
                        rel['id'],
                        rel_info["label"],
                        None
                    )
                    new_id = create_new_node(
                        rel["id"],
                        rel_info["label"],
                        properties,
                        driver
                    )

                    if new_id:
                        # Create relationship
                        create_relationship(
                            rel_info["relationship_type"],
                            node_id,
                            rel["id"],
                            rel["start_time"],
                            rel["end_time"],
                            driver
                        )
                        next_queue.append(new_id)

        queue = next_queue
        print(Fore.BLUE + f"---Completed {root_name} graph: depth {level}---" + Style.RESET_ALL)

    return root_id


def find_node_by_wikidata_id(wikidata_id: str, driver) -> Union[Dict, bool]:
    """Helper function to find node by Wikidata ID."""
    query = """
        MATCH (n {wikidata_id: $wikidata_id})
        RETURN n, labels(n) as label, n.name as name
    """

    with driver.session() as session:
        result = session.run(query, wikidata_id=wikidata_id).single()

        if result:
            return {
                "name": result.get("name"),
                "label": result.get("label")[0]
            }
        return False


def create_new_node(wikidata_id: str, label: str, properties: dict, driver) -> Union[str, Any]:
    """
    creates a new node in Neo4j if one with the given Wikidata ID doesn't already exist.

    This function checks for the existence of a node with the specified `wikidata_id`. If no such node exists, it creates a new node with the given `label` and `properties`.
    If the node already exists, it simply returns the `wikidata_id` and logs a message.

    Args:
        driver: The Neo4j driver instance.
        wikidata_id: The Wikidata ID of the node.  Used as a unique identifier.
        label: The label to apply to the new node (e.g., "Company", "Manager").
        properties: A dictionary of properties to set on the new node.
        node_name: An optional human-readable name for the node, used for logging.

    Returns:
        The Wikidata ID of the node, whether it was newly created or already existed.

    Raises:
        Exception: If an error occurs during node creation.
    """

    with driver.session() as session:
        if not find_node_by_wikidata_id(wikidata_id, driver):

            create_query = f"""
                CREATE (n:`{label}`)
                SET n = $properties
                RETURN n.wikidata_id as wikidata_id
            """
            result = session.run(create_query, properties=properties).single()

            if result and result.get("wikidata_id"):
                print(
                    Fore.GREEN + f"Successfully created node with wikidataID '{wikidata_id}' and node properties '{properties}'")
                return result.get("wikidata_id")
            else:
                raise Exception(
                    f"Error creating node with wikidata_id: {wikidata_id} and node properties: {properties}")
        else:
            print(
                Fore.GREEN + f"Node with wikidata_id: {wikidata_id} and properties '{properties}' already exists and has therefore not been added" + Style.RESET_ALL)

            return wikidata_id


def create_relationship(rel_type: str, org_wikidata_id: str, rel_wikidata_id: str,
                        rel_wikidata_start_time: str, rel_wikidata_end_time: str, driver, name_org_node=None,
                        name_rel_node=None):
    """Creates a relationship between two nodes in a Neo4j graph if it doesn't already exist.

    This function creates a directed relationship between two nodes identified by their Wikidata IDs.


    Args:
        rel_type: Type of relationship to create (e.g., "SUBSIDIARY_OF")
        org_wikidata_id: Wikidata ID of the organization node
        rel_wikidata_id: Wikidata ID of the related node
        rel_wikidata_start_time: Start time of the relationship
        rel_wikidata_end_time: End time of the relationship
        driver: Neo4j driver instance
        name_org_node: Optional name for organization node (for logging)
        name_rel_node: Optional name for related node (for logging)

    Returns:
        bool: False if relationship already exists or creation fails

    """

    params = {
        "source_id": org_wikidata_id,
        "target_id": rel_wikidata_id,
        "start_time": rel_wikidata_start_time,
        "end_time": rel_wikidata_end_time
    }

    # Check if relationship exists
    check_query = f"""
        MATCH (source {{wikidata_id: $source_id}})-[r:{rel_type}]->(target {{wikidata_id: $target_id}})
        WHERE r.start_time = $start_time AND r.end_time = $end_time
        RETURN r
    """

    with driver.session() as session:
        if list(session.run(check_query, params)):
            print(
                Fore.GREEN + f"Relationship {rel_type} between {org_wikidata_id} and {rel_wikidata_id} already exists" + Style.RESET_ALL)
            return False

        # Create relationship if it doesn't exist
        create_query = f"""
            MATCH (source {{wikidata_id: $source_id}})
            MATCH (target {{wikidata_id: $target_id}})
            CREATE (source)-[r:{rel_type} {{
                start_time: $start_time,
                end_time: $end_time
            }}]->(target)
            RETURN source, target, r
        """
        result = session.run(create_query, params)
        if list(result):
            if name_org_node is not None and name_rel_node is not None:
                print(
                    Fore.GREEN + f"Successfully created relationship between node '{name_org_node}' with wikidataID '{org_wikidata_id}' and node '{name_rel_node}' with wikidataID' {rel_wikidata_id}' of type '{rel_type}'" + Style.RESET_ALL)
            else:
                print(
                    Fore.GREEN + f"Successfully created relationship between node with wikidataID '{org_wikidata_id}' and node with wikidataID' {rel_wikidata_id}' of type '{rel_type}'" + Style.RESET_ALL)

            return True
        else:
            return False


def get_relationship_triples(node_name: str, node_label: str = None, driver=None):
    """Retrieves relationship triples (source, relationship, target) for a given node.

        Queries Neo4j database to find all relationships connected to the specified node,
        optionally filtered by the connected node's label. Returns relationships as
        triples in dictionary format.

        Args:
            node_name: Name of the node to find relationships for
            driver: Neo4j driver instance
            node_label: Optional label to filter connected nodes by

        Returns:
            List[Dict[str, str]]: List of relationship triples, each containing:
                - node_from: Source node name
                - relationship: Type of relationship
                - node_to: Target node name
            None: If no relationships found or error occurs

        Example:
            [
                {"node_from": "Google", "relationship": "OWNS", "node_to": "YouTube"}
            ]
        """

    query = """
        MATCH (n) WHERE n.name = $node_name
        MATCH (n)-[r]-(connected)
        WHERE labels(connected)[0] = $node_label
        RETURN type(r) as relationship_type, connected.name as connected_node_name
        """

    query_all_node_labels = """
        MATCH (n) WHERE n.name = $node_name
        MATCH (n)-[r]-(connected)
        RETURN type(r) as relationship_type, 
               connected.name as connected_node_name,
               labels(connected) as connected_labels
    """

    with driver.session() as session:
        try:
            if node_label is not None:
                result = session.run(query,
                                     node_name=node_name,
                                     node_label=node_label)
            else:
                result = session.run(query_all_node_labels,
                                     node_name=node_name)

            relationships = []
            for record in result:
                relationships.append({"node_from": node_name.replace("'", ""),
                                      "relationship": record["relationship_type"].replace("'", ""),
                                      "node_to": record["connected_node_name"].replace("'",
                                                                                       "")})  # escaping " ' " to prevent issues with the json formatting later

            if relationships:
                return relationships
            else:
                print(f"No relationships found for node '{node_name}'")
                return None
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")


def get_node_relationships(source_wikidata_id: str = None, target_wikidata_id: str = None, driver=None) -> list:
    """Retrieves relationships between nodes in a Neo4j graph database.

    This function queries relationships in the graph based on provided Wikidata IDs. It can either:
    1. Find all relationships for a single node (when only source_wikidata_id is provided)
    2. Find relationships between two specific nodes (when both IDs are provided)

    Args:
        source_wikidata_id: Wikidata ID of the source node
        target_wikidata_id: Optional Wikidata ID of the target node
        driver: Neo4j driver instance

    Returns:
        list: List of dictionaries containing relationship information:
            - rel_type: Type of relationship
            - rel_id: Relationship ID
            - rel_end_time: End time of relationship (or 'NA' if not set)

    Raises:
        KeyError: If no source_wikidata_id is provided
        Exception: If relationship formatting fails
    """
    if driver is None:
        print(Fore.RED + "Error: No driver provided" + Style.RESET_ALL)
        return []

    with driver.session() as session:
        try:
            # Query for relationships between two specific nodes
            if source_wikidata_id and target_wikidata_id:
                relationships = _query_two_nodes(session, source_wikidata_id, target_wikidata_id).get("relationships",
                                                                                                      [])
            # Query for all relationships of a single node
            elif source_wikidata_id:
                relationships = _query_single_node(source_wikidata_id, driver).get("relationships", [])
            else:
                raise KeyError(
                    Fore.RED +
                    f"Error: No source wikidata_id provided (source: '{source_wikidata_id}', target: '{target_wikidata_id}')" +
                    Style.RESET_ALL
                )

            # Format and return relationships
            return [
                {
                    'rel_type': rel['type'],
                    'rel_id': rel['id'],
                    'rel_end_time': rel.get('end_time', 'NA')
                }
                # for rel in (result["outgoing"] + result["incoming"])
                for rel in relationships
            ]

        except Exception as e:
            raise Exception(f"Error processing relationships: {str(e)}")


def build_node_properties(wikidata_id: str, label: str, name: Optional[str] = None) -> Dict:
    """Builds a dictionary of node properties based on entity type and Wikidata information.

    Constructs property dictionary either from custom ID or by fetching Wikidata properties.
    Different properties are collected based on the node label (entity type).

    Args:
        wikidata_id: Entity identifier (either Wikidata ID or CustomID)
        label: Type of entity (Company, Manager, etc.)
        name: Optional name for custom entities

    Returns:
        dict: Properties dictionary containing:
            - Basic properties: name, wikidata_id
            - Label-specific properties:
                - Company: inception, isin
                - Manager/Founder/Board_Member: date_of_birth, date_of_death
                - Others: empty additional properties

    Raises:
        KeyError: If label is not in supported entity types
    """
    # Handle custom entities
    if wikidata_id.startswith("CustomID"):
        return {
            "name": name,
            "label": label,
            "wikidata_id": wikidata_id
        }

    # Fetch Wikidata information
    if wikidata_id.startswith("FinancialID"):  # FinancialID--2013-12-31--Q3895
        financial_id = wikidata_id.split("--")[2]
        point_in_time = wikidata_id.split("--")[1]
        data = wikidata_wbgetentities(financial_id)
        # note: the following is not the most time efficient, solutions could be cached to improve runtime
        return {
            "name": wikidata_id,
            "label": "Financial_Data",
            "wikidata_id": wikidata_id,
            "total assets": _get_wikidata_financial_entry("P2403", financial_id, point_in_time, data),
            "total equity": _get_wikidata_financial_entry("P2137", financial_id, point_in_time, data),
            "total revenue": _get_wikidata_financial_entry("P2139", financial_id, point_in_time, data),
            "net profit": _get_wikidata_financial_entry("P2295", financial_id, point_in_time, data),
            "operating income": _get_wikidata_financial_entry("P3362", financial_id, point_in_time, data),
            "market capitalization": _get_wikidata_financial_entry("P2226", financial_id, point_in_time, data),
            "assets under management": _get_wikidata_financial_entry("P4103", financial_id, point_in_time, data),
            "employee_number": _get_wikidata_financial_entry("P1128", financial_id, point_in_time, data),
        }

    data = wikidata_wbgetentities(wikidata_id)
    properties = _get_label_specific_properties(label, wikidata_id, data)

    # Add common properties
    try:
        properties["name"] = data["entities"][wikidata_id]["labels"]["en"]["value"]
    except KeyError:
        print(
            Fore.RED +
            f"No label/name defined in Wikidata for ID {wikidata_id}. Using ID as name." +
            Style.RESET_ALL
        )
        properties["name"] = wikidata_id

    properties["wikidata_id"] = wikidata_id
    return properties


def update_relationship_property(elementID: str, rel_property: str, new_property_value: str, driver) -> tuple:
    """Updates a specific property of a relationship in Neo4j.

    This function updates a single property of a relationship identified by its element ID.
    It verifies that the update was successful by returning the new value.

    Args:
        elementID: The unique identifier of the relationship
        rel_property: Name of the property to update
        new_property_value: New value to set for the property
        driver: Neo4j driver instance

    Returns:
        tuple: (elementID, new_property_value) if update successful

    Raises:
        ValueError: If the relationship update fails
    """
    update_query = f"""
        MATCH ()-[r]-() 
        WHERE elementId(r) = $element_id
        SET r.{rel_property} = $new_value
        RETURN r.{rel_property} as new_property_value
    """

    params = {
        "element_id": elementID,
        "new_value": new_property_value
    }

    with driver.session() as session:
        result = session.run(update_query, params)
        if result:
            return elementID, new_property_value

        raise ValueError(
            f"Failed to update property '{rel_property}' for relationship '{elementID}'"
        )


def reset_graph(driver):
    with driver.session() as session:
        session.run("MATCH(n) DETACH DELETE n")


def get_latest_custom_id(starts_with: str, driver: Driver) -> int:
    """Retrieves the highest numeric value from existing CustomID nodes in Neo4j.

    Queries the Neo4j database for nodes with wikidata_ids starting with 'CustomID'
    and returns the highest numeric suffix found. This is useful for generating
    the next CustomID in sequence.

    Args:
        starts_with: what kind of custom id to search for ("customID", "financialID")
        driver: Neo4j driver instance for database connection

    Returns:
        int: Highest CustomID number found, or 0 if no CustomID nodes exist
    """
    query = f"""
        MATCH (n)
        WHERE n.wikidata_id STARTS WITH '{starts_with}'
        RETURN toInteger(substring(n.wikidata_id, {len(starts_with)})) as custom_id
        ORDER BY custom_id DESC
        LIMIT 1
    """

    with driver.session() as session:
        result = session.run(query).single()
        return result["custom_id"] if result else 0


"""functions below are helper functions"""


def _get_wikidata_entry(key, wikidata_id, wikidata, name=False, time=False):
    if time:
        try:
            return str(_parse_datetime_to_iso(
                wikidata.get("entities").get(wikidata_id).get("claims").get(key)[0].get("mainsnak").get(
                    "datavalue").get("value").get("time")))
        except:
            return "NA"
    else:
        try:
            return wikidata.get("entities").get(wikidata_id).get("claims").get(key)[0].get("mainsnak").get(
                "datavalue").get("value")
        except:
            if name:
                try:
                    return wikidata_wbsearchentities(wikidata_id, id_or_name="name")
                except:
                    print(
                        Fore.RED + f"Error: for wikidata_id {wikidata_id}, because Wikidata entry exists but no label/name defined by Wikidata. Returning NA" + Style.RESET_ALL)
                    return "NA"
            return "NA"


def _get_wikidata_financial_entry(key, wikidata_id, date, wikidata):
    result = {}
    try:
        for entry in wikidata.get("entities").get(wikidata_id).get("claims").get(key):
            try:
                amount = entry.get("mainsnak").get("datavalue").get("value").get("amount")
            except KeyError:
                amount = "NA"
            try:
                point_in_time = entry.get("qualifiers").get("P585")[0].get("datavalue").get("value").get("time")
                point_in_time = _parse_datetime_to_iso(point_in_time)
                point_in_time = point_in_time.strftime('%Y-%m-%d')
            except KeyError:
                point_in_time = "NA"
            result[point_in_time] = amount
        result = result.get(date)
        return result
    except:
        return "NA"


def _get_label_specific_properties(label: str, wikidata_id: str, data: Dict) -> Dict:
    """Helper function to get properties specific to each entity type."""
    if label == "Company":
        return {
            "inception": _get_wikidata_entry("P571", wikidata_id, data, time=True),
            "isin": _get_wikidata_entry("P946", wikidata_id, data)
        }
    elif label in ["Manager", "Founder", "Board_Member"]:
        return {
            "date_of_birth": _get_wikidata_entry("P569", wikidata_id, data, time=True),
            "date_of_death": _get_wikidata_entry("P570", wikidata_id, data, time=True)
        }
    elif label in ["StockMarketIndex", "Industry_Field", "City", "Country", "Product_or_Service"]:
        return {}
    else:
        raise KeyError(f"Unsupported entity type: {label}")


def _query_single_node(node_id: str, driver):
    """Queries all relationships for a given node in Neo4j.

    Args:
        driver: Neo4j driver object
        node_id: Wikidata ID of the node to query

    Returns:
        Record containing list of relationships with their types and end times

    """

    query = """
        MATCH (n {wikidata_id: $node_id})
        OPTIONAL MATCH (n)-[r]-(connected)
        RETURN collect({
            type: type(r),
            id: elementId(r),
            end_time: r.end_time
        }) as relationships
    """
    with driver.session() as session:
        return session.run(query, node_id=node_id).single()


def _query_two_nodes(session, source_id: str, target_id: str):
    """
    Queries any relationships between two nodes in Neo4j.

    Args:
        session: Neo4j session object
        source_id: Wikidata ID of first node
        target_id: Wikidata ID of second node

    Returns:
        Record containing list of relationships between nodes
    """

    query = """
        MATCH (source {wikidata_id: $source_id})
        MATCH (target {wikidata_id: $target_id})
        OPTIONAL MATCH (source)-[r]-(target)
        RETURN collect({type: type(r), id: elementId(r)}) as relationships
    """
    return session.run(query, source_id=source_id, target_id=target_id).single()


def _clean_string(text: str) -> str:
    """Helper function to remove single quotes from strings."""
    return text.replace("'", "")


def _get_relationship_dict(wikidata_id, label):
    data = wikidata_wbgetentities(wikidata_id)
    try:
        if label == "Company":
            relationship_dict = {
                "StockMarketIndex": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P361"]),
                    "label": "StockMarketIndex",
                    "relationship_type": "IS_LISTED_IN",
                },
                "Industry_Field": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P452"]),
                    "label": "Industry_Field",
                    "relationship_type": "IS_ACTIVE_IN",
                },
                "Subsidiary": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P355"]),
                    # removed P1830 because also included buildings, football clubs etx
                    "label": "Company",
                    "relationship_type": "OWNS",
                },
                "Owner": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["127"]),
                    "label": "Company",
                    "relationship_type": "IS_OWNED_BY",
                },
                "City": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P159"]),
                    "label": "City",
                    "relationship_type": "HAS_HEADQUARTER_IN",
                },
                "Product_or_Service": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P1056"]),
                    "label": "Product_or_Service",
                    "relationship_type": "OFFERS",
                },
                "Founder": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P112"]),
                    "label": "Founder",
                    "relationship_type": "WAS_FOUNDED_BY",
                },
                "Manager": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P169", "P1037"]),
                    "label": "Manager",
                    "relationship_type": "IS_MANAGED_BY",
                },
                "Board_Member": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P3320"]),
                    "label": "Board_Member",
                    "relationship_type": "HAS_BOARD_MEMBER",
                },
                "Financial_Data": {
                    "wikidata_entries": _get_wikidata_financial_rels(data, wikidata_id, ["P2139"]),
                    "label": "Financial_Data",
                    "relationship_type": "HAS_FINANCIAL_DATA",
                }
            }
            return relationship_dict
        elif label == "StockMarketIndex":
            relationship_dict = {}
        elif label == "Industry_Field":
            relationship_dict = {}
        elif label == "City":
            relationship_dict = {
                "Country": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P17"]),
                    "label": "Country",
                    "relationship_type": "LOCATED_IN",
                }
            }
        elif label == "Country":
            relationship_dict = {}
        elif label == "Product_or_Service":
            relationship_dict = {}
        elif label in ["Manager", "Founder", "Board_Member"]:
            relationship_dict = {
                "Employer": {
                    "wikidata_entries": _get_wikidata_rels(data, wikidata_id, ["P108"]),
                    "label": "Company",
                    "relationship_type": "EMPLOYED_BY",
                }
            }
        elif label == "Financial_Data":
            relationship_dict = {}
        else:
            raise Exception(f"Label {label} is not supported")
        return relationship_dict
    except KeyError as e:
        raise KeyError(f"KeyError for label: '{label}': {e}")


def _get_wikidata_rels(data: dict, wikidata_id: str, property_ids: list) -> list[
    dict[str, Union[Union[datetime, str], Any]]]:
    result = []

    for property_id in property_ids:
        try:
            entries = data["entities"][wikidata_id]["claims"][property_id]
        except KeyError:
            # print(Fore.YELLOW + f"Key Error {property_id} for wikidata_id {wikidata_id}, skipping this key" + Style.RESET_ALL)
            continue
        for entry in entries:
            try:
                start_time = entry["qualifiers"]["P580"][0]["datavalue"]["value"]["time"]  # start time
                start_time = _parse_datetime_to_iso(start_time)
            except KeyError:
                start_time = "NA"
            try:
                end_time = entry["qualifiers"]["P582"][0]["datavalue"]["value"]["time"]
                end_time = _parse_datetime_to_iso(end_time)
            except KeyError:
                end_time = "NA"
            try:
                id = entry["mainsnak"]["datavalue"]["value"]["id"]
            except KeyError as e:
                print(
                    Fore.YELLOW + f"Key Error for single relationship for wikidata_id {wikidata_id}, skipping this relationship. Error {e}" + Style.RESET_ALL)
                continue
            result.append({"id": id, "start_time": start_time, "end_time": end_time})

    if max_branching_factor is not None:
        result = result[:max_branching_factor]

    return result


def _get_wikidata_financial_rels(data: dict, wikidata_id: str, property_ids: list) -> list[
    dict[str, Union[Union[datetime, str], Any]]]:
    # note: maybe there is a more elegant way to get the notes, as we now rely on P2129/total_revenue,
    # which might not be available although other financial data might be available

    result = []

    for property_id in property_ids:
        try:
            entries = data["entities"][wikidata_id]["claims"][property_id]
        except KeyError:
            # print(Fore.YELLOW + f"Key Error {property_id} for wikidata_id {wikidata_id}, skipping this key" + Style.RESET_ALL)
            continue
        for entry in entries:
            try:
                start_time = entry["qualifiers"]["P585"][0]["datavalue"]["value"]["time"]  # start time
                start_time = _parse_datetime_to_iso(start_time)
            except KeyError:
                start_time = "NA"
            try:
                end_time = start_time.replace(year=start_time.year + 1)
            except KeyError or ValueError:
                # Handle Feb 29 edge case
                end_time = start_time.replace(year=start_time.year + 1, day=28)
            try:
                id = "FinancialID" + "--" + (start_time.strftime('%Y-%m-%d') + "--" + str(wikidata_id))
            except KeyError as e:
                print(
                    Fore.YELLOW + f"Key Error for financial relationship for wikidata_id {wikidata_id}, skipping this relationship. Error {e}" + Style.RESET_ALL)
                continue
            result.append({"id": id, "start_time": start_time, "end_time": end_time})

    if max_branching_factor is not None:
        result = result[:max_branching_factor]

    return result


def _parse_datetime_to_iso(date_string: str) -> datetime:
    """Converts various datetime string formats to UTC datetime objects.

    Handles multiple datetime string formats including:
    - ISO 8601 format with '+' prefix (e.g., '+2023-01-01T00:00:00Z')
    - Standard datetime with timezone (e.g., '2023-01-01 00:00:00+00:00')
    - Dates with negative years (treated as datetime.min)

    Args:
        date_string: String representation of date/time to parse

    Returns:
        datetime: Parsed datetime object with UTC timezone

    Raises:
        ValueError: If the date string cannot be parsed into a valid datetime

    Examples:
        >>> parse_datetime_to_iso('+2023-01-01T00:00:00Z')
        datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
        >>> parse_datetime_to_iso('2023-01-01 00:00:00+00:00')
        datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    """
    # Handle dates before Christ (negative years)
    if date_string.startswith('-'):
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        # Handle ISO format with '+' prefix
        if date_string.startswith('+'):
            return datetime.strptime(
                date_string.lstrip('+').rstrip('Z'),
                "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)

        # Handle standard datetime format with timezone
        return datetime.strptime(
            date_string,
            "%Y-%m-%d %H:%M:%S%z"
        ).replace(tzinfo=timezone.utc)

    except ValueError as e:
        # Handle invalid month/day values (e.g., "-00")
        if "-00" in date_string:
            fixed_date = date_string.replace("-00", "-01")
            return _parse_datetime_to_iso(fixed_date)

        raise ValueError(
            f"Failed to parse date string '{date_string}': {str(e)}"
        )


def _is_date_in_range(
        rel_wikidata_start_time: Union[datetime, str],
        rel_wikidata_end_time: Union[datetime, str],
        from_date_of_interest: datetime,
        until_date_of_interest: datetime
) -> bool:
    """Checks if a time period overlaps with a date range of interest.

    Determines if there is any overlap between a relationship's time period
    (defined by start and end times) and a date range of interest. Handles
    "NA" values by treating them as minimum/maximum possible dates.

    Args:
        rel_wikidata_start_time: Start time of relationship (datetime or "NA")
        rel_wikidata_end_time: End time of relationship (datetime or "NA")
        from_date_of_interest: Start of date range to check
        until_date_of_interest: End of date range to check

    Returns:
        bool: True if there is overlap between the periods, False otherwise


    """
    # Convert "NA" to min/max dates
    start_time = (datetime.min.replace(tzinfo=timezone.utc)
                  if rel_wikidata_start_time == "NA"
                  else rel_wikidata_start_time)

    end_time = (datetime.max.replace(tzinfo=timezone.utc)
                if rel_wikidata_end_time == "NA"
                else rel_wikidata_end_time)

    # Check for non-overlap conditions
    return not (end_time < from_date_of_interest or
                start_time > until_date_of_interest)


"""functions below are not currently in use, but might be used for future functionality"""


def find_by_name(session, name: str) -> Union[Dict, bool]:
    """Helper function to find node by name."""
    query = """
        MATCH (n {name: $name})
        RETURN n, labels(n) as label, n.wikidata_id as wikidata_id
    """
    result = session.run(query, name=name).single()

    if result:
        return {
            "wikidata_id": result.get("wikidata_id"),
            "label": result.get("label")[0]
        }
    return False


def delete_relationship_by_id(relationship_id: str, driver) -> bool:
    """
    Deletes a relationship using its Neo4j elementId
    Returns: bool indicating success or failure
    """
    if not relationship_id:
        raise KeyError(Fore.RED + "Error: relationship_id must be provided" + Style.RESET_ALL)

    delete_query = """
        MATCH ()-[r]-()
        WHERE elementId(r) = $relationship_id
        DELETE r
        RETURN count(r) as deleted_count
    """

    try:
        with driver.session() as session:
            result = session.run(delete_query,
                                 relationship_id=relationship_id).single()

            if result and result["deleted_count"] > 0:
                print(Fore.GREEN + f"Relationship with ID '{relationship_id}' has been deleted" + Style.RESET_ALL)
                return True
            raise Exception(Fore.YELLOW + f"No relationship found with ID '{relationship_id}'" + Style.RESET_ALL)
    except Exception as e:
        raise Exception(Fore.RED + f"Error deleting relationship: {str(e)} + Error: {e}" + Style.RESET_ALL)


def delete_node(wikidata_id: str, driver) -> Union[str, bool]:
    """Deletes a node from Neo4j database based on its Wikidata ID.

    This function attempts to delete a node and all its relationships (DETACH DELETE)
    from the Neo4j database using the provided Wikidata ID as identifier.

    Args:
        driver: The Neo4j driver instance.
        wikidata_id: The Wikidata ID of the node to delete.

    Returns:
        str: The wikidata_id if deletion was successful
        bool: False if the node wasn't found or if wikidata_id is None

    Raises:
        Exception: If an error occurs during the deletion process.
    """
    if wikidata_id is None:
        print(Fore.RED + "Error: Wikidata ID is None. No deletion performed." + Style.RESET_ALL)
        return False

    delete_query = """
        MATCH (n {wikidata_id: $wikidata_id})
        DETACH DELETE n
        RETURN count(n) as deleted_count
    """

    try:
        with driver.session() as session:
            result = session.run(delete_query, wikidata_id=wikidata_id).single()

            if result and result["deleted_count"] > 0:
                return wikidata_id

            print(
                Fore.YELLOW +
                f"No node found with wikidata_id: '{wikidata_id}'" +
                Style.RESET_ALL
            )
            return False

    except Exception as e:
        raise Exception(
            Fore.RED +
            f"Error deleting node: {str(e)}" +
            Style.RESET_ALL
        )
