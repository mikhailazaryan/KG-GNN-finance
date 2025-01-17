import configparser
import json
from json import JSONDecodeError
import google.generativeai as genai
from datetime import datetime, timezone
from colorama import Fore, Style

from graphbuilder import \
    create_new_node, create_relationship_in_graph, \
    get_node_relationships, get_wikidata_id_from_name, \
    get_properties, get_graph_information, \
    update_relationship_property
from wikidata.wikidata import wikidata_wbsearchentities

model = genai.GenerativeModel("gemini-1.5-pro-latest")
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
        old_triples = ""

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

    added, deleted, unchanged = find_change_triples(article, name_company_at_center, label_node_requiring_change, 1, 3, driver)

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

    return added, deleted, unchanged

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

    name = _generate_result_from_llm(prompt, enum = companies, max_output_tokens=30, temperature=0.4)

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

def _get_and_increment_customID():
    global custom_id
    custom_id += 1
    custom_node_id = "CustomID" + str(custom_id)
    return custom_node_id

def _get_datetime_now_and_max():
    rel_wikidata_start_time = str(datetime.now().replace(tzinfo=timezone.utc))
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

def _update_node_properties_dict(article, properties_dict, response_schema):
    #todo: currently not implemented, does not support changing of node properties
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



