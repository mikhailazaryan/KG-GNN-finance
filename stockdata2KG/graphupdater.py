import configparser
import google.generativeai as genai
from datetime import datetime, timezone

from stockdata2KG.graphbuilder import \
    create_new_node, build_graph_from_initial_node, create_relationship_in_graph, \
    check_if_node_exists_in_graph, delete_node
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
    company = find_company(article, companies)
    node_type = find_node_type(article, node_types)
    most_relevant_node = find_most_relevant_node(article, company, node_type, driver)
    type_of_change = find_type_of_change(article, company, most_relevant_node)
    if type_of_change == "add node":
        name_of_node_to_add = find_node_name_to_change(article, node_type)
        _add_new_node(name_of_node_to_add, company, node_type, date_from, date_until, nodes_to_include, search_depth, driver)
    #todo: now determine the type of change (add new node, delete existing node, modify existing node, modify relationship between two existing nodes) using an llm
    # then make the change using 4 different json templates as structured output (see here https://ai.google.dev/gemini-api/docs/structured-output?lang=python)
    # issues: secondary connections are not taken into account (e.g. Allianz SE subsiary company1 bought company 2), maybe I can iteratively increase the scope? This should happen in the find company field
    elif type_of_change == "remove node":
        _remove_node(most_relevant_node)
        return
    elif type_of_change == "replace node":
        # options to replace node:
        # better
        #   (1) copy node_type and relationship type of old node
        _replace_node(most_relevant_node)
        #   (2) create new node with relationship type
        #   (3) create new relationship with same relationship type (both can use the add function)
        #   (4) check if old node has remaining relationships and delete if not

        return
    elif type_of_change == "modify node information":
        # how to modify node information?
        # (1) get node id
        # (2) get node information as a properties dict of changable propertiers
        # (3) ask the LLM to change the property dict based on the news article
        # (4) run the new property dict
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

def find_most_relevant_node(article, company, node_type, driver):
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
            You are a classification assistant. Your task is to analyze a news article and select the SINGLE most relevant node from a provided list of nodes.

            Instructions:
            1. Read the provided news article carefully
            2. Review the list of available nodes
            3. Select ONE node that best captures the primary subject matter or entity being discussed. If no node seems to fit, please return "None of these nodes are relevant"

            Example input:

            Article: "Allianz SE sold PIMCO"
            Available nodes: [Allianz Deutschland, Allianz Holding eins, PIMCO, Allianz New Europe Holding, 'Kraft Versicherungs-AG', 'Allianz Infrastructure Czech HoldCo II']
            Output: PIMCO

            Article: "Microsoft Inc bought CyberSystems INC"
            Available nodes: [Allianz Deutschland, EthCyberSecurityCompany, PIMCO, Allianz New Europe Holding, 'Kraft Versicherungs-AG', 'Allianz Infrastructure Czech HoldCo II']
            Output: None of these nodes are relevant

            Please analyze the following:
            Article: "{article}"
            Available node_types: {str(relevant_nodes).replace("'", "")}        
            """

    result = _generate_result_with_enum(prompt, relevant_nodes)
    print(f"Found node '{result}' to be most relevant for article '{article}' and relevant nodes '{relevant_nodes}")
    return result

def find_type_of_change(article, company, most_relevant_node):
    types_of_change_enum = ["add node", "remove node", "modify node information", "replace node", "no change required"]

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
                Most Relevant Node: "PIMCO"
                Available types of change: {types_of_change_enum}
                Output: "delete node"
                Reasoning: The Knowledge Graph most probably has a node "PIMCO" which is no longer required if "PIMCO" is sold.

                Article: "Allianz SE bought SportGear AG"
                Most Relevant Node: "Allianz SE"
                Available types of change: {types_of_change_enum}
                Output: "add node"
                Reasoning: A new company is being acquired, so a new node needs to be added to the Knowledge Graph.
                
                Article: "Allianz SE moved their headquarter from Munich to Berlin"
                Most Relevant Node: "Munich"
                Available types of change: {types_of_change_enum}
                Output: "replace node"
                Reasoning: The node 'Munich' has to be replaced by a new node 'Berlin'
                
                Article: "Allianz SE was renamed to Algorithm GmbH' and companies"
                Most Relevant Node: "Allianz SE"
                Available types of change: {types_of_change_enum}
                Output: "modify node information"
                Reasoning: The node 'Allianz SE' already exists and it's name or other information have to be modified.
                

                Please analyze the following:
                Article: "{article}"
                Most Relevant Node: {most_relevant_node}
                """

    result = _generate_result_with_enum(prompt, types_of_change_enum)
    print(f"Found type of change '{result}' to be most fitting for article '{article}' and node '{most_relevant_node}")
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

def _add_new_node(name_new_node, company, node_type, date_from, date_until, nodes_to_include, search_depth, driver):
    wikidata_id = wikidata_wbsearchentities(name_new_node, id_or_label = 'id')

    if wikidata_id == "No wikidata entry found":
        wikidata_id = _get_and_increment_customID()
        print(f"Created custom ID '{wikidata_id}' for node '{name_new_node}' because no wikidata ID was found")
        create_new_node(wikidata_id, name_new_node, node_type, has_wikidata_entry=False, driver=driver)
    else:
        build_graph_from_initial_node(name_new_node, node_type, date_from, date_until, nodes_to_include, search_depth, driver=driver)

    rel_wikidata_start_time = str(datetime.now().replace(tzinfo=timezone.utc)) #todo: check if there is a date information available in the news article
    rel_wikidata_end_time = str(datetime.max.replace(tzinfo=timezone.utc))

    if node_type == "Company":
        rel_direction = "OUTBOUND"
        rel_type = "OWNS"
    elif node_type == "Industry_Field":
        rel_direction = "OUTBOUND"
        rel_type = "ACTIVE_IN"
    #todo: add all other options ["Company", "Industry_Field", "Person", "City", "Country", "StockMarketIndex"]
    else:
        raise ValueError(f"Unknown node type '{node_type}'")

    org_label = check_if_node_exists_in_graph(name=company, driver=driver).get("label")
    org_wikidata_id = check_if_node_exists_in_graph(name=company, driver=driver).get("wikidata_id")
    #print(rel_direction, rel_type, org_label, node_type, org_wikidata_id, wikidata_id, rel_wikidata_start_time, rel_wikidata_end_time)
    create_relationship_in_graph(rel_direction, rel_type, org_label, node_type, org_wikidata_id, wikidata_id, rel_wikidata_start_time, rel_wikidata_end_time, driver)
    return

def _remove_node(most_relevant_node):
    wikidata_id = wikidata_wbsearchentities(most_relevant_node, id_or_label = 'id')
    if wikidata_id == "No wikidata entry found":
        raise KeyError(f"No wikidata_if for '{most_relevant_node}' found")
    if not delete_node(wikidata_id):
        raise Exception(f"Deletion of node '{most_relevant_node}' failed")

def _replace_node(most_relevant_node):
    #   (1) copy node_type and relationship type of old node
    #   (2) create new node with relationship type
    #   (3) create new relationship with same relationship type (both can use the add function)
    #   (4) check if old node has remaining relationships and delete if not
    return

def _get_and_increment_customID():
    global custom_id
    custom_id += 1
    custom_node_id = "CustomID" + str(custom_id)
    return custom_node_id

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