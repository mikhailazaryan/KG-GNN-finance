import configparser
import json
from json import JSONDecodeError

import google.generativeai as genai
from datetime import datetime, timezone
from colorama import Fore, Style
import typing_extensions as typing
from typing import Dict

from sympy import false

from stockdata2KG.graphbuilder import \
    create_new_node, build_graph_from_initial_node, create_relationship_in_graph, \
    check_if_node_exists_in_graph, delete_node, get_node_relationships, get_wikidata_id_from_name, \
    delete_relationship_by_id, get_node_properties, set_node_properties, get_properties, get_graph_information, \
    update_relationship_property
from stockdata2KG.wikidata import wikidata_wbsearchentities

model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Choose the desired model

config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

global custom_id
custom_id = 0



def find_change_triples(article, name_company_at_center, node_type_requiring_change, attempt, max_attempt, driver):
    if attempt >= max_attempt:
        return False, False, False

    old_triples = get_graph_information(name_company_at_center, node_type_requiring_change, driver=driver)
    if old_triples is None:
        old_triples = "" #["no triples found"]

    node_type_rel_dict = {
        "Company": "OWNS | IS_OWNED_BY | PARTNERS_WITH",
        "Industry_Field": "IS_ACTIVE_IN",
        "Manager": "MANAGED_BY",
        "Founder": "FOUNDED_BY",
        "Board_Member" : "HAS_BOARD_MEMBER",
        "City": "HAS_HEADQUARTER_IN | IS_ACTIVE_IN",
        "Country" : "LOCATED_IN",
        "Product_or_Service": "OFFERS | HAS_ANNOUNCED | INVESTS_IN | RESEARCHES",
        "StockMarketIndex" : "IS_LISTED_IN"
    }

    favorable_rel = node_type_rel_dict.get(node_type_requiring_change)

    prompt = f"""
    You are a classification assistant. You provide data to keep a Knowledge Graph about a company up to date. 
    Your task is to analyze a news article and analyze existing graph-triples consisting of 'node_from', 'relationship' and 'node_to'.
    You should then update the existing graph-triples according to the article and return them.
    If no change seems to be required, return the triples unchanged.

    Instructions:
    1. Read the provided news article carefully.
    2. Review the existing graph-triples consisting of "node_from", "relationship" and "node_to".
    3. Update the existing graph-triples according to the article. 

    Example input:
    
    Article: "Allianz SE bought Ergo Group'
    Input: {{triples: [{{'node_from': 'Allianz SE', 'relationship': 'OWNS', 'node_to': 'Dresdner Bank'}}, {{'node_from': 'Allianz SE', 'relationship': 'OWNS', 'node_to': 'Euler Hermes'}}]}}
    Output triples: {{triples: [{{'node_from': 'Allianz SE', 'relationship': 'OWNS', 'node_to': 'Dresdner Bank'}}, {{'node_from': 'Allianz SE', 'relationship': 'OWNS', 'node_to': 'Euler Hermes'}}, {{'node_from': 'Allianz SE', 'relationship': 'OWNS', 'node_to': 'Ergo Group'}}]}}
    
    Article: "Allianz SE fired it's old CEO Oliver Bäte, the new CEO is Boris Hilgat"
    Input triples: {{triples: [{{'node_from': 'Allianz SE', 'relationship': 'IS_MANAGED_BY', 'node_to': 'Oliver Bäte'}}]}}
    Output triples: {{triples: [{{'node_from': 'Allianz SE', 'relationship': 'IS_MANAGED_BY', 'node_to': 'Boris Hilgat'}}]}}
    
    
    Please analyze the following:
    Article: "{article}"
    Input triples: {old_triples} 
    
    If possible, please stick to the following relationships: OWNS, PARTNERS_WITH, IS_ACTIVE_IN, IS:MANAGED_BY, WAS_FOUNDED_BY, HAS_BOARD_MEMBER, HAS_HEADQUARTER_IN, IS_LOCATED_IN, OFFERS, HAS_ANNOUNCED, INVESTS_IN, RESEARCHES IN, IS_LISTED_IN.
    Remember to only output a valid json with the format {{triples:[{{'node_from': '', 'relationship': '', 'node_to': ''}}]}}
    """


    result = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.2)).text
    result = result.replace("```json", "").replace("```", "").replace("'", "\"")

    try:
        new_triples = json.loads(result)

        new_triples_set = {json.dumps(t, sort_keys=True) for t in new_triples.get("triples")}
        old_triples_set = {json.dumps(t, sort_keys=True) for t in old_triples}

        intersection = set(new_triples_set).intersection(set(old_triples_set))
        intersection = [json.loads(s) for s in intersection]
        print("intersection: " + str(intersection))


        added = set(new_triples_set).difference(set(old_triples_set))
        added = [json.loads(s) for s in added]
        print("added: " + str(added))

        deleted = set(old_triples_set).difference(set(new_triples_set))
        if "no triples found" in deleted:
            deleted = deleted.remove("no triples found")
        deleted = [json.loads(s) for s in deleted]
        print("deleted: " + str(deleted))

        return added, deleted, intersection
    except JSONDecodeError as e:
        print(Fore.RED + f"JSONDecodeError: '{e}' with result: '{result}', try again" + Style.RESET_ALL)
        find_change_triples(article, name_company_at_center, node_type_requiring_change, attempt+1, max_attempt, driver)
    return False, False, False

def _add_node(name_node_from, name_node_to, label_node_to, relationship_type, date_from, date_until, nodes_to_include, search_depth, driver):
    id_node_from = get_wikidata_id_from_name(name_node_from, driver)
    id_node_to = wikidata_wbsearchentities(name_node_to, id_or_name='id')
    rel_props = {
        "rel_direction": "OUTBOUND",
        "rel_type": relationship_type,
        "rel_start_time": str(datetime.now().replace(tzinfo=timezone.utc)),
        "rel_end_time": "NA",
    } #todo: see if we can make this more precise by extractime time data from the article

    if id_node_to == "No wikidata entry found":
        id_node_to = _get_and_increment_customID()
        print(Fore.YELLOW + f"Created custom ID '{id_node_to}' for node '{name_node_to}' because no wikidata ID was found" + Style.RESET_ALL)
        property_dict = get_properties(id_node_to, label_node_to, name_node_to)
        id_new_node = create_new_node(id_node_to, label_node_to, properties_dict=property_dict, driver=driver)
        print(Fore.GREEN + f"Node with name '{name_node_to}' and wikidata_id: '{id_new_node}' has been added to neo4j graph" + Style.RESET_ALL)
    else:
        id_new_node = build_graph_from_initial_node(name_node_from, label_node_to, date_from, date_until, nodes_to_include, search_depth, driver=driver)
    create_relationship_in_graph(rel_props.get('rel_direction'), rel_props.get('rel_type'), id_node_from, id_node_to, rel_props.get('rel_start_time'), rel_props.get('rel_end_time'), driver)
    return id_new_node

def update_neo4j_graph(article, companies, node_types, date_from, date_until, nodes_to_include, search_depth_new_nodes, search_depth_for_changes, driver):
    print("\n")

    name_company_at_center = find_company_at_center(article, companies, 1, 3)
    if name_company_at_center != "None":
        print(Fore.GREEN + f"'{name_company_at_center}' is the company at center for the article '{article}' and companies '{companies}'." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Could not find company at center for the article '{article}'." + Style.RESET_ALL)
        return False

    label_node_requiring_change = find_node_type(article, node_types)
    if label_node_requiring_change != "None":
        print(Fore.GREEN + f"'{label_node_requiring_change}' is the node type which requires a change." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Could not find node type which requires change for article '{article}'." + Style.RESET_ALL)
        return False

    added, deleted, intersection = find_change_triples(article, name_company_at_center, label_node_requiring_change, 1, 3, driver)

    if added:
        for add in added:
            try:
                node_from = add.get("node_from")
                relationship_type = add.get("relationship")
                node_to = add.get("node_to")

                id_node_from = get_wikidata_id_from_name(node_from, driver)
                if id_node_from is None:
                    id_node_from = wikidata_wbsearchentities(node_from, id_or_name='id')
                if id_node_from == "No wikidata entry found":
                    id_node_from = _get_and_increment_customID()
                id_node_from = create_new_node(id_node_from, "Company" , properties_dict=get_properties(id_node_from, "Company", node_from), driver=driver)

                id_node_to = get_wikidata_id_from_name(node_to, driver)
                if id_node_to is None:
                    id_node_to = wikidata_wbsearchentities(node_to, id_or_name='id')
                if id_node_to == "No wikidata entry found":
                    id_node_to = _get_and_increment_customID()
                id_node_to = create_new_node(id_node_to, label_node_requiring_change , properties_dict=get_properties(id_node_to, label_node_requiring_change, node_to), driver=driver)
                create_relationship_in_graph("OUTBOUND", relationship_type, id_node_from, id_node_to, str(datetime.now().replace(tzinfo=timezone.utc)), "NA", driver)
            except KeyError as e:
                print(Fore.RED + f"Key Error for {add}. Error: {e}." + Style.RESET_ALL)
    if deleted:
        for delete in deleted:
            try:
                node_from = delete.get("node_from")
                relationship_type = delete.get("relationship")
                node_to = delete.get("node_to")

                id_node_from = get_wikidata_id_from_name(node_from, driver)
                if id_node_from is None:
                    id_node_from = wikidata_wbsearchentities(node_from, id_or_name='id')

                id_node_to = get_wikidata_id_from_name(node_to, driver)
                if id_node_to is None:
                    id_node_to = wikidata_wbsearchentities(node_to, id_or_name='id')

                print("id node from: "+ id_node_from, "id node to: "+ id_node_to)

                node_relationships = get_node_relationships(id_node_from, id_node_to, driver)
                print("test node relationships: " + str(node_relationships))
                for rel_id in node_relationships:
                    print(rel_id['rel_id'])
                    updated_rel_elementID = update_relationship_property(rel_id['rel_id'], "end_time", str(datetime.now().replace(tzinfo=timezone.utc)), driver)
                print("test" + str(updated_rel_elementID))

            except KeyError as e:
                print(Fore.RED + f"Key Error for {delete}. Error: {e}." + Style.RESET_ALL)

    return "test"

def _sanity_check(article, name_org_node, node_type, type_of_change, name_selected_node):
    #todo currently not working, maybe not needed

    prompt = f"""
        Please analyze if the following change in our knowledge graph is in accordance with the article:

        Context:
        - Based on Article: {article}
        - Original Node: {name_org_node} with Node Type: {node_type}
        - Type of Change: {type_of_change}
        - Node which is changed: {name_selected_node}


        Return a JSON response in this format:
        {{
            "is_valid": boolean
        }}

        """

    class ResponseSchema(typing.TypedDict):
        is_valid: bool

    result = _generate_result_from_llm(prompt, ResponseSchema=ResponseSchema, max_output_tokens=1000)
    result = json.loads(result)
    return result

def find_company_at_center(article, companies, attempt, max_attempt):
    if "None" not in companies:
        companies.append("None")

    if attempt >= max_attempt:
        return False

    prompt = f"""
    You are a classification assistant. You provide data to keep a Knowledge Graph about a company up to date. 
    Your task is to analyze a news article and select a single which is acting in the article. Please always choose the company which is the acting part.
    If no company seems to be relevant in the article, please return "None"

    Instructions:
    1. Read the provided news article carefully.
    2. Review the list of possible companies.
    3. Return ONE company which is acting in the article.

    Example input:

    Article: "Mercedes-Benz announces new electric vehicle model with 500-mile range"
    Possible companies: ["Fresenius SE & Co. KGaA", "Hannover Rück SE", "Heidelbergcement AG", "Henkel AG & Co. KGaA", "Allianz SE", "Infineon Technologies AG", "Mercedes-Benz", "Merck KGaA", "MTU Aero Engines AG", "Münchener Rückversicherungs-Gesellschaft AG", "None"]
    Output: Mercedes-Benz
    Reasoning: Mercedes-Benz is the company which is acting, as they are announcing something.

    Article: "Sports Gear AG has been bough by Allianz SE"
    Possible companies: ["Fresenius SE & Co. KGaA", "Hannover Rück SE", "Heidelbergcement AG", "Henkel AG & Co. KGaA", "Allianz SE", "Infineon Technologies AG", "Mercedes-Benz", "Merck KGaA", "MTU Aero Engines AG", "Münchener Rückversicherungs-Gesellschaft AG", "None"]
    Output: Allianz SE
    Reasoning: Allianz SE is the company which is buying a Sports Gear AG, therefore Allianz SE is the acting company.

    Please analyze the following:
    Article: "{article}"
    Possible companies: {str(companies)}        
    """

    name = _generate_result_from_llm(prompt, enum = companies, max_output_tokens=30, temperature=0.4) #todo: as an idea, the enum could not just be the initial company, but all companies

    if name not in companies:
        find_company_at_center(article, companies, attempt+1, max_attempt)

    result = wikidata_wbsearchentities(name, id_or_name="name")
    return result

def find_node_type(article, node_types):
    if "None" not in node_types:
        node_types.append("None")

    prompt = f"""
    You are a classification assistant. You provide data to keep a Knowledge Graph about a company up to date. 
    Your task is to analyze a news article and select a SINGLE node from a provided list which is most likely to require a change or update in the knowledge graph.                
    If no node_type seems to be relevant in the article, please return "None"


    Instructions:
    1. Read the provided news article carefully
    2. Review the list of available node_types: {node_types}. These node_types make up all information in the knowledge graph. 
    3. Select ONE node_type which has to be modified, added or deleted according to the article.

    Example input:
    
    Article: "Mercedes-Benz announces new electric vehicle model 'S-Class' with 500-mile range"
    Available node_types = ["Company", "Industry_Field", "Person", "City", "Country", "Product_or_Service", "Employer", "StockMarketIndex", "None"]
    Output: Product_or_Service
    Reasoning: Mercedes-Benz is offereing their new product 'S-Class' which means the knowledge graph needs a new node 'S-Class'. 

    Article: "Volkswagen AG moved their headquarter from Munich to Berlin",
    Available node_types = ["Company", "Industry_Field", "Person", "City", "Country", "Product_or_Service", "Employer", "StockMarketIndex", "None"]
    Output: City
    Reasoning: As their headquarter is changing it's location, Citiy is the correct node_type which requires change 
            
    Article: "Allianz SE is no longer active in the insurance industry",
    Available node_types = ["Company", "Industry_Field", "Person", "City", "Country", "Product_or_Service", "Employer", "StockMarketIndex", "None"]
    Output: Industry_Field
    Reasoning: The node 'Insurance Industry' of type Industry_Field is most likely to require a change. 
            

    Please analyze the following:
    Article: "{article}"
    Available node_types: {str(node_types)}        
            """

    result = _generate_result_from_llm(prompt, enum = node_types)
    return result

def find_node_requiring_change(article, company, node_type, search_depth, driver):
    relevant_nodes = ["None"]

    if node_type == "Company":
        relevant_nodes.extend([company])  # If e.g. a company is buying another company, it makes sense to include it in the list of relevant nodes, mostly used if new nodes need to be created

    for path_length in range(0, search_depth+1):

        query = f"""
                MATCH (start:Company)-[*{path_length}]-(target:{node_type})
                WHERE start.name = "{company}"
                AND target.name IS NOT NULL
                RETURN DISTINCT target.name
                """

        with driver.session() as session:
            result = session.run(query)
            result = [record["target.name"] for record in result]
            if result is not None:
                print(f"Found node requiring change '{result}' for company '{company}' and node_type '{node_type}'")
            else:
                raise ValueError(f"Could not find relevant nodes for company '{company}' and node_type '{node_type}")

        relevant_nodes.extend(result)

        prompt = f"""
                You are a classification assistant. Your task is to analyze a news article and select the SINGLE most relevant node which needs to be changed from a provided list of nodes.
    
                Instructions:
                1. Read the provided news article carefully
                2. Review the list of available nodes
                3. Select ONE node that needs to be changed to keep the Knowledge Graph up-to-date in accordance with the article information . If no node seems to fit, please return "None"
    
                Example input:
    
                Article: "Allianz SE sold PIMCO"
                Available nodes: [Allianz Deutschland, Allianz Holding eins, PIMCO, Allianz New Europe Holding, 'Kraft Versicherungs-AG', 'Allianz Infrastructure Czech HoldCo II']
                Output: PIMCO
                Reasoning: The PIMCO node needs to be changed, as it no longer has a reltionship to Allianz SE after being sold.
    
                Article: "Microsoft Inc bought CyberSystems INC"
                Available nodes: [Allianz Deutschland, EthCyberSecurityCompany, PIMCO, Allianz New Europe Holding, 'Kraft Versicherungs-AG', 'Allianz Infrastructure Czech HoldCo II']
                Output: None of these nodes are relevant
                Reasoning: As none of the available nodes are mentioned in the article, None of these nodes are relevant
                
                Article: "Allianz SE moved their headquarter from Berlin to Frankfurt"
                Available nodes: [Berlin, Munich, Frankfurt, New York]
                Output: Berlin
                Reasoning: The node Berlin is the existing node in the Knowledge Graph which requires a change. 
    
    
                Please analyze the following:
                Article: "{article}"
                Available node_types: {str(relevant_nodes).replace("'", "")}        
                """

        result = _generate_result_from_llm(prompt, enum = relevant_nodes)
        if result != "None":
            print(f"Found node '{result}' to be most relevant for article '{article}' and relevant nodes '{relevant_nodes}")
            return result
        else:
            print(f"Found no node with path_length = {path_length} to be relevant for the article, therefore increasing path_length to {path_length+1}. Relevant Nodes to choose from were: '{relevant_nodes}")
    print(f"Found no node up to path_length = {path_length} to be relevant for the article, therefore returning None")
    return None

def find_type_of_change(article, node_requiring_change):
    types_of_change_enum = ["add relationship", "delete relationship", "modify node information", "replace node", "no change required"]

    prompt = f"""
                You are a classification assistant to keep an existing Knowledge Graph of company data up-to-date. 
                Your task is to analyze a news article and select the SINGLE most relevant type of change required to keep the Knowledge Graph up-to-date.
                The Knowledge Graph currently exists of a company, it's subsidiary companies, Industry Fields, Persons, Cities, Countries, and StockMarketIndices with respective relationships to the company

                Instructions:
                1. Read the provided news article carefully
                2. Review the information stored in the node which is most relevant for the change.
                2. Review the list of available types of changes which are: {types_of_change_enum}
                3. Select the ONE type of change that best captures the primary subject of the article. If no node change is required, please select "no change required"

                Example input:

                Article: "Allianz SE sold PIMCO"
                Node requiring a change: "PIMCO"
                Available types of change: {types_of_change_enum}
                Output: "delete relationship to node"
                Reasoning: The relationship to "PIMCO" is no longer required if "PIMCO" is sold.

                Article: "Allianz SE bought SportGear AG"
                Node requiring a change: "SportGear AG"
                Available types of change: {types_of_change_enum}
                Output: "add node"
                Reasoning: A new company is being acquired, so a new node needs to be added to the Knowledge Graph.
                
                Article: "Woodworking is a new business field of Allianz SE"
                Node requiring a change: "Woodworking"
                Available types of change: {types_of_change_enum}
                Output: "add node"
                Reasoning: A new company is being acquired, so a new node needs to be added to the Knowledge Graph.
                
                Article: "Allianz SE moved their headquarter from Munich to Berlin"
                Node requiring a change: "Munich"                
                Available types of change: {types_of_change_enum}
                Output: "replace node"
                Reasoning: The node 'Munich' has to be replaced by a new node 'Berlin'
                
                Article: "Allianz SE was renamed to Algorithm GmbH"
                Node requiring a change: "Allianz SE"
                Available types of change: {types_of_change_enum}
                Output: "modify node information"
                Reasoning: The node 'Allianz SE' already exists and it's name or other information have to be modified.
                

                Please analyze the following:
                Article: "{article}"
                Node requiring a change: {node_requiring_change}
                """

    result = _generate_result_from_llm(prompt, enum = types_of_change_enum)
    print(f"Found type of change '{result}' to be most fitting for article '{article}' and node '{node_requiring_change}")
    return result

def find_node_name_to_change(article, node_type):
    #todo: find out if this is acutally needed
    prompt = f"""
           You are a knowledge graph node identification assistant. Your task is to identify the name of a new node that should be added, removed or modified in the Knowledge Graph based on the article.

           Instructions:
           1. Read the provided news article.
           2. Consider the specified node type.
           3. Return ONLY a single string containing the name of the new node that should be added.
           4. Do not provide any explanations, reasoning, or additional text.

           Example input:
           Article: "Microsoft acquires Activision Blizzard for $69 billion"
           Node type: Company
           Output: Activision Blizzard

           Please analyze the following:
           Article: "{article}"
           Node type: {node_type}
           """

    result = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.1,  # Lower temperature for more focused responses
            max_output_tokens=70,  # Limit output length
            response_mime_type="text/plain",
        ),
    )

    name_new_node = result.text.strip()
    print(f"Found name '{name_new_node}' to be the most fitting name for the new node for article '{article}'")
    return name_new_node

def _get_and_increment_customID():
    global custom_id
    custom_id += 1
    custom_node_id = "CustomID" + str(custom_id)
    return custom_node_id

def _get_relationship_properties(node_type):
    rel_wikidata_start_time, rel_wikidata_end_time = _get_datetime_now_and_max()

    if node_type == "Company":
        rel_direction = "OUTBOUND"
        rel_type = "OWNS"
    elif node_type == "Industry_Field":
        rel_direction = "OUTBOUND"
        rel_type = "ACTIVE_IN"
    elif node_type == "City":
        rel_direction = "OUTBOUND"
        rel_type = "HAS_HEADQUARTER_IN"
    elif node_type == "Product_or_Service":
        rel_direction = "OUTBOUND"
        rel_type = "OFFERS"
    #todo: add all other options ["Company", "Industry_Field", "Person", "City", "Country", "StockMarketIndex"]
    else:
        raise ValueError(f"Unknown node type '{node_type}'")
    relationship_properties = {
        "rel_direction": rel_direction,
        "rel_type": rel_type,
        "rel_start_time": rel_wikidata_start_time,
        "rel_end_time": rel_wikidata_end_time,
    }
    return relationship_properties

def _add_nodeDEPRECIATED(name_org_node, node_type, article, date_from, date_until, nodes_to_include, search_depth, driver):
    id_org_node = get_wikidata_id_from_name(name_org_node, driver)
    name_new_node = find_node_name_to_change(article, node_type)
    id_new_node = wikidata_wbsearchentities(name_new_node, id_or_name='id')
    rel_props = _get_relationship_properties(node_type)
    if id_new_node == "No wikidata entry found":
        id_new_node = _get_and_increment_customID()
        print(
            Fore.YELLOW + f"Created custom ID '{id_new_node}' for node '{name_new_node}' because no wikidata ID was found" + Style.RESET_ALL)

        property_dict = get_properties(id_new_node, node_type, name_new_node)
        print(property_dict)
        id_new_node = create_new_node(id_new_node, node_type, properties_dict=property_dict, driver=driver)
        print(Fore.GREEN + f"Node with name '{name_new_node}' and wikidata_id: '{id_new_node}' has been added to neo4j graph" + Style.RESET_ALL)
    else:
        build_graph_from_initial_node(name_new_node, node_type, date_from, date_until, nodes_to_include, search_depth, driver=driver)

    create_relationship_in_graph(rel_props.get('rel_direction'), rel_props.get('rel_type'), id_org_node, id_new_node,
                                 rel_props.get('rel_start_time'), rel_props.get('rel_end_time'), driver)
    return id_new_node

def _delete_rel_and_maybe_node(name_company, name_selected_node, driver):
    id_org_node = get_wikidata_id_from_name(name_company, driver)
    id_selected_node = get_wikidata_id_from_name(name_selected_node, driver)
    if id_selected_node is None:
        print("No node with name'{name_selected_node}' found, returning False")
        return False
    rels = get_node_relationships(source_wikidata_id=id_org_node, target_wikidata_id=id_selected_node, driver=driver)
    for rel in rels:
        delete_relationship_by_id(rel['rel_id'], driver)
    if len(get_node_relationships(source_wikidata_id=id_selected_node, driver=driver)) == 0:
        wikidata_id = delete_node(id_selected_node, driver=driver)
        print(Fore.GREEN + f"Node with name: '{name_selected_node}' and wikidata_id: '{wikidata_id}:' has been deleted because it had 0 remaining relationships" + Style.RESET_ALL)
        return wikidata_id
    return True

def _get_datetime_now_and_max():
    rel_wikidata_start_time = str(datetime.now().replace(tzinfo=timezone.utc))  # todo: check if there is a date information available in the news article
    rel_wikidata_end_time = str(datetime.max.replace(tzinfo=timezone.utc))
    return rel_wikidata_start_time, rel_wikidata_end_time

def _generate_result_from_llm(prompt, enum = None, ResponseSchema = None, temperature = 0.5, max_output_tokens = 30):
    if enum is not None:
        result = model.generate_content(prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="text/x.enum",
                response_schema={
                    "type": "STRING",
                    "enum": enum,
                },
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
        return result.text
    elif ResponseSchema is not None:
        result = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ResponseSchema,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            ),
        )
        return result.text
    else:
        raise KeyError(f"No enum or ResponseSchema provided")


def _create_dynamic_dict_schema(key: str) -> Dict[str, str]:
    return {key: str}

def _update_node_properties_dict(article, properties_dict, response_schema):
    prompt =   f"""
                Your task is to determine which dictionary entry has to be changed based on information from an article.

                Instructions:
                1. Read the provided article carefully
                2. Review the available property entries
                3. Return a singe available property entry that needs to be modifiert.

                Example input:

                Article: "Allianz SE changed it's name to Algorithmic GmbH"
                Input properties_dict = {{"employee_number": "", "net_profit": "", "name": "Allianz SE", "isin": "DE0349284901929"}}
                Output: name
        

                Please analyze the following:
                Article: "{article}"
                properties_dict: {properties_dict}        
                """

    key = _generate_result_from_llm(prompt, list(response_schema.keys()))
    print(f"Found property of '{key}' requires a change according to article '{article}' and properties '{properties_dict}")

    prompt = f"""
           Your task is to update a dictionary based on information from an article.

           Instructions:
           1. Read the provided article carefully
           2. Review the dictionary
           3. Change the dictionary according to the article.

           Example input:

           Article: "Allianz SE changed it's name to Algorithmic GmbH"
           Input dictionary = {{'name': 'Allianz SE'}}
           Output dictionary = {{'new_value': 'Algorithmic GmbH'}}
           
           Please analyze the following:
           Article: "{article}"
           properties_dict: {property}        
           """




    result = _generate_result_from_llm(prompt, ResponseSchema=ResponseSchema, temperature=0.3, max_output_tokens=40)
    updated_node_property = json.loads(result)
    updated_node_property = updated_node_property["new_value"]

    properties_dict[key] = updated_node_property

    print(f"Updated nodes properties dict to '{properties_dict}' for article '{article}'")
    return properties_dict



