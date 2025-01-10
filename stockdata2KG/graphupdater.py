import configparser
import json

import google.generativeai as genai
from datetime import datetime, timezone
from colorama import Fore, Style
import typing_extensions as typing
from typing import Dict



from stockdata2KG.graphbuilder import \
    create_new_node, build_graph_from_initial_node, create_relationship_in_graph, \
    check_if_node_exists_in_graph, delete_node, get_node_relationships, get_wikidata_id_from_name, \
    delete_relationship_by_id, get_node_properties, set_node_properties
from stockdata2KG.wikidata import wikidata_wbsearchentities

model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Choose the desired model

config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

global custom_id
custom_id = 0

def findKeyword(article, driver):
    with driver.session() as session:
        query = """MATCH (n) RETURN n"""
        result = session.run(query)
        list = []
        for record in result:
            list.append(dict(record["n"])["name"])

    prompt = f"""
    Read this newspaper article:

    {article}

    Which single keyword of the following keywords ist most relevant in the article?: 

    {list}

    Please only list a single word!"""

    print(prompt)
    response = model.generate_content(prompt)
    print("Gemini says: " + response.text)
    response = response.text.split(" ")
    if response in list:
        print("Gemini Keyword is: " + response)
        return response

def compare_and_suggest_with_llm(news_article, graph_data):
     # Prepare the prompt for the LLM
     prompt = f"""
    Here is the information from a knowledge graph:
    {graph_data}

    And here is a news article:
    {news_article}

    Identify any discrepancies between the knowledge graph and the news article. 
    Suggest the most important update that need to be made to the knowledge graph.

    Please only suggest a single update and start your answer with "Update:", "Insert:" or "Delete:"
    """

     # Call the LLM API
     response = model.generate_content(prompt)
     # Extract LLM response
     return response.text

def update_KG(query, driver):
     with driver.session() as session:
          session.run(query)

def process_news_and_update_KG(article, driver):
     # node_name = findKeyword(article, driver)
     # data = query_graph(driver, node_name)
     data = query_graph(driver, "Munich")
     print("Data retrieved from KG: " + str(data))
     suggestion = compare_and_suggest_with_llm(article, data)
     print("Gemini-Pro 1.5: " + str(suggestion))
     cypher_code = suggestion_to_cypher(driver, data, suggestion)
     cypher_code1 = '\n'.join(cypher_code.split('\n')[1:]) # remove first and last lines: "```cypher" and "```"
     cypher_code2 = '\n'.join(cypher_code1.split('\n')[:-1]) #
     print("Cypher code:\n " + str(cypher_code2))
     # extractRelevantNodes(driver)
     update_KG(cypher_code2, driver)

def findKeyword(article, driver):
     with driver.session() as session:
          query = """MATCH (n) RETURN n"""
          result = session.run(query)
          list = []
          for record in result:
               list.append(dict(record["n"])["name"])

     prompt = f"""
    Read this newspaper article:

    {article}

    Which single keyword of the following keywords ist most relevant in the article?: 

    {list}

    Please only list a single word!"""

     print(prompt)
     response = model.generate_content(prompt)
     print("Gemini says: " + response.text)
     response = response.text.split(" ")
     if response in list:
          print("Gemini Keyword is: " + response)
          return response

def query_graph(driver, node_name):
     with driver.session() as session:
          query = """
        MATCH (n {name: $node_name})-[r]-(m)
        RETURN n, type(r) AS relationship_type, m
        """
          result = session.run(query, {"node_name": node_name})
          graph_data = []
          for record in result:
               graph_data.append({
                    "node": dict(record["n"]),
                    "relationship_type": record["relationship_type"],
                    # "relationship_properties": record["relationship_properties"],
                    "connected_node": dict(record["m"])
               })
          return graph_data

def suggestion_to_cypher(driver, data, suggestion):
     # Prepare the prompt for the LLM
     prompt = f"""
      given this neo4j knowledge graph entry: 

      {data}

      and this update request:

      {suggestion}

      Please write a single cypher query to make this update.
      """

     # Call the LLM API
     response = model.generate_content(prompt)

     # Extract LLM response
     return response.text

def update_neo4j_graph(article, companies, node_types, date_from, date_until, nodes_to_include, search_depth, driver):
    name_org_node = find_company(article, companies)
    node_type = find_node_type(article, node_types)
    name_selected_node = find_node_requiring_change(article, name_org_node, node_type, driver)  # todo issue: secondary connections are not taken into account (e.g. Allianz SE subsiary company1 bought company 2), maybe I can iteratively increase the scope? This should happen in the find company field
    type_of_change = find_type_of_change(article, name_selected_node)

    if type_of_change == "add node":
        id_new_node = _add_node(name_org_node, node_type, article, date_from, date_until, nodes_to_include, search_depth, driver)

    elif type_of_change == "delete relationship to node":
        id_node_deleted = _delete_rel_and_maybe_node(name_org_node, name_selected_node, driver)

    elif type_of_change == "replace node":
        id_new_node = _add_node(name_org_node, node_type, article, date_from, date_until, nodes_to_include, search_depth, driver)
        id_node_deleted = _delete_rel_and_maybe_node(name_org_node, name_selected_node, driver)

        return
    elif type_of_change == "modify node information":
        id_of_selected_node = get_wikidata_id_from_name(name_selected_node, driver)
        prop_dict = get_node_properties(id_of_selected_node, driver)
        updated_node_properties_dict = _update_node_properties_dict(article, prop_dict, prop_dict)
        id_of_updated_node = set_node_properties(id_of_selected_node, updated_node_properties_dict, driver)

        return

def find_company(article, companies):
    prompt = f"""
                You are a classification assistant. Your task is to analyze a news article and select the SINGLE most relevant company from a provided list that is discussed in the article.

                Instructions:
                1. Read the provided news article carefully
                2. Review the list of available companies
                3. Return ONE company which is most relevant in the article

                Example input:

                Article: "Tesla announces new electric vehicle model with 500-mile range"
                Available companies: [Tesla, Microsoft, Apple, Volkswagen, Allianz SE, Siemens AG]
                Output: Tesla

                Article: "Allianz SE bought SportGear AG"
                Available companies: [Tesla, Microsoft, Apple, Volkswagen, Allianz SE, Siemens AG]
                Output: Allianz SE

                Please analyze the following:
                Article: "{article}"
                Available node_types: {str(companies).replace("'", "")}        
                """

    result = _generate_result_with_enum(prompt, companies)
    print(f"Found company '{result}' for article '{article}' and companies '{companies}'.")
    return result

def find_node_type(article, node_types):
    prompt = f"""
            You are a classification assistant. Your task is to analyze a news article and select the SINGLE most relevant node type from a provided list that best represents the main entity or concept being updated in the article.

            Instructions:
            1. Read the provided news article carefully
            2. Review the list of available node_types
            3. Select ONE node_type that best captures the primary subject matter or entity being discussed

            Example input:
            
            Article: "Tesla announces new electric vehicle model with 500-mile range"
            Available node_types: [Company, Industry, Person, City, Country, StockMarketIndex]
            Output: Company
        
            Article: "Volkswagen AG moved their headquarter from Munich to Berlin",
            Available node_types: [Company, Industry_Field, Person, City, Country, StockMarketIndex]
            Output: City
                    
            Article: "Allianz SE is no longer active in the insurance industry",
            Available node_types: [Company, Industry_Field, Person, City, Country, StockMarketIndex]
            Output: Industry
                    

            Please analyze the following:
            Article: "{article}"
            Available node_types: {str(node_types).replace("'", "")}        
            """

    result = _generate_result_with_enum(prompt, node_types)
    print(f"Found node_type of '{result}' for article '{article}' and node_types '{node_types}")
    return result

def find_node_requiring_change(article, company, node_type, driver):
    query = f"""
            MATCH (n:{node_type})-[]-(target {{name: "{company}"}})
            WHERE n.name IS NOT NULL
            RETURN DISTINCT n.name
            """
    with driver.session() as session:
        result = session.run(query)
        result = [record["n.name"] for record in result]
        if result is not None:
            print(f"Found relevant nodes '{result}' for company '{company}' and node_type '{node_type}'")
        else:
            raise ValueError(f"Could not find relevant nodes for company '{company}' and node_type '{node_type}")

    relevant_nodes = result
    relevant_nodes.append('None of these nodes are relevant')
    if node_type == "Company":
        relevant_nodes.append(company) #If e.g. a company is buying another company, it makes sense to include it in the list of relevant nodes, mostly used if new nodes need to be created

    prompt = f"""
            You are a classification assistant. Your task is to analyze a news article and select the SINGLE most relevant node which needs to be changed from a provided list of nodes.

            Instructions:
            1. Read the provided news article carefully
            2. Review the list of available nodes
            3. Select ONE node that needs to be changed to keep the Knowledge Graph up-to-date in accordance with the article information . If no node seems to fit, please return "None of these nodes are relevant"

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

    result = _generate_result_with_enum(prompt, relevant_nodes)
    print(f"Found node '{result}' to be most relevant for article '{article}' and relevant nodes '{relevant_nodes}")
    return result

def find_type_of_change(article, node_requiring_change):
    types_of_change_enum = ["add node", "delete relationship to node", "modify node information", "replace node", "no change required"]

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

    result = _generate_result_with_enum(prompt, types_of_change_enum)
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

def _replace_node(most_relevant_node, new_node_name, date_from, date_until, nodes_to_include, search_depth, driver):
    #   (1) copy node_type and relationship type of old node
    node_relationships = get_node_relationships()
    #   (2) create new node with relationship type
    #   (3) create new relationship with same relationship type (both can use the add function)
        #_add_new_node(new_node_name, org_node=most_relevant_node, node_type, rel_properties, date_from, date_until, nodes_to_include, search_depth, driver)
    #   (4) check if old node has remaining relationships and delete if not
    return

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

def _add_node(name_org_node, node_type, article, date_from, date_until, nodes_to_include, search_depth, driver):
    id_org_node = get_wikidata_id_from_name(name_org_node, driver)
    name_new_node = find_node_name_to_change(article, node_type)
    id_new_node = wikidata_wbsearchentities(name_new_node, id_or_name='id')
    rel_props = _get_relationship_properties(node_type)

    if id_new_node == "No wikidata entry found":
        id_new_node = _get_and_increment_customID()
        print(
            Fore.YELLOW + f"Created custom ID '{id_new_node}' for node '{name_new_node}' because no wikidata ID was found" + Style.RESET_ALL)
        id_new_node = create_new_node(id_new_node, name_new_node, node_type, driver=driver)
        print(Fore.GREEN + f"Node with name '{name_new_node}' and wikidata_id: '{id_new_node}' has been added to neo4j graph" + Style.RESET_ALL)

    else:
        build_graph_from_initial_node(name_new_node, node_type, date_from, date_until, nodes_to_include, search_depth, driver=driver)

    create_relationship_in_graph(rel_props.get('rel_direction'), rel_props.get('rel_type'), id_org_node, id_new_node,
                                 rel_props.get('rel_start_time'), rel_props.get('rel_end_time'), driver)
    return id_new_node

def _delete_rel_and_maybe_node(name_company, name_selected_node, driver):
    id_org_node = get_wikidata_id_from_name(name_company, driver)
    id_selected_node = get_wikidata_id_from_name(name_selected_node, driver)
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

def _generate_result_with_enum(prompt, enum):
    result = model.generate_content(prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="text/x.enum",
            response_schema={
                "type": "STRING",
                "enum": enum,
            },
        ),
    )
    return result.text

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

    key = _generate_result_with_enum(prompt, list(response_schema.keys()))
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

    class ResponseSchema(typing.TypedDict):
        new_value: str

    result = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ResponseSchema,
            temperature = 0.3,
            max_output_tokens=30
        ),
    )
    updated_node_property = result.text
    updated_node_property = json.loads(updated_node_property)
    updated_node_property = updated_node_property["new_value"]

    properties_dict[key] = updated_node_property

    print(f"Updated nodes properties dict to '{properties_dict}' for article '{article}'")
    return properties_dict



