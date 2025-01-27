import configparser
import json
import re

import google.generativeai as genai
from datetime import datetime, timezone
from colorama import Fore, Style
from neo4j import Driver
from typing import List, Dict, Tuple, Optional, Any

from wikidata.wikidata import wikidata_wbsearchentities
from graphbuilder import create_relationship, get_node_relationships, \
    get_relationship_triples, update_relationship_property, get_latest_custom_id, \
    find_node_by_wikidata_id, create_new_node, build_node_properties

model = genai.GenerativeModel("gemini-1.5-pro-latest")
config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

global custom_id
custom_id = None


def update_neo4j_graph(article: str, companies: List[str], node_types: List[str], nodes_to_include: List[str],
                       driver) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Updates Neo4j graph based on article analysis and company relationships.

    Identifies changes in company relationships from article content and updates
    the Neo4j graph accordingly by adding new relationships and marking old ones
    as ended.

    Args:
        article: Text content of the article
        companies: List of company names to analyze
        node_types: List of possible node types
        nodes_to_include: List of node types to include in graph
        driver: Neo4j driver instance

    Returns:
        Tuple containing lists of:
        - added relationships
        - deleted relationships
        - unchanged relationships

    """
    # Find central company and node type requiring change
    company = find_company_at_center(article, companies, 1, 3)
    node_type = find_node_type(article, node_types)

    if company == "None":
        print(Fore.RED + f"No central company found in article: '{article}'" + Style.RESET_ALL)
        return [], [], []

    if node_type == "None":
        print(Fore.RED + f"No node type requiring change found in article: '{article}'" + Style.RESET_ALL)
        return [], [], []

    print(Fore.GREEN + f"Analyzing changes for {company} ({node_type})" + Style.RESET_ALL)

    # Get existing relationships
    relevant_triples = get_relationship_triples(company, node_label=node_type, driver=driver)

    # Find changes
    added, deleted, unchanged = find_change_triples(
        article, company, node_type, relevant_triples, 1, 4, driver)

    # These checks can be used to iterate on find_change_triples for a back and forth until checks are passing, although this will require a lot of extra compute
    formal_check = formal_sanity_check(added, deleted, relevant_triples)
    reasoning_check = llm_sanity_check(added, deleted, relevant_triples, article)
    if formal_check["correct_update"]:
        print(Fore.GREEN + "Formal sanity check: " + str(formal_check) + Style.RESET_ALL)
    else:
        print(Fore.RED + "Formal sanity check: " + str(formal_check) + Style.RESET_ALL)
    if reasoning_check["correct_update"]:
        print(Fore.GREEN + "Reasoning sanity check: " + str(reasoning_check) + Style.RESET_ALL)
    else:
        print(Fore.RED + "Reasoning sanity check: " + str(reasoning_check) + Style.RESET_ALL)

    # Process additions
    for triple in added:
        _add_relationship(triple, nodes_to_include, driver)

    # Process deletions
    for triple in deleted:
        _mark_relationship_ended(triple, driver)

    return added, deleted, unchanged


def find_change_triples(article, name_company_at_center, node_type_requiring_change, relevant_triples, attempt,
                        max_attempt, driver):
    if attempt >= max_attempt:
        return False, False, False

    print(f"Relevant information retrieved from graph: {relevant_triples}")
    if relevant_triples is None:
        relevant_triples = ""

    prompt = f"""
    You are a classification assistant. You provide data to keep a Knowledge Graph about a company up to date. 
    Your task is to analyze a news article and analyze existing graph-triples consisting of 'node_from', 'relationship' and 'node_to'.
    You should then update the existing graph-triples according to the article and return them.
    If no change seems to be required, return the triples unchanged.
    You should only make changes when the article describes an event that has happened, but not when it is only vaguely announced.

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

    Article: "Company A divests its Environmental Science Professional business called EnvSciPro to Company B, a British private equity firm, for $2.6 billion.
    Input triples: {{'node_from': 'Company A', 'relationship': 'OFFERS', 'node_to': 'EnvSciPro'}}
    Output triples: {{triples: [{{'node_from': 'Company B', 'relationship': 'OFFERS', 'node_to': 'EnvSciPro'}}]}}



    Please analyze the following:
    Article: "{article.replace("'", "")}"
    Input triples: {relevant_triples} 

    Please stick to the following relationships: OWNS, PARTNERS_WITH, IS_ACTIVE_IN, IS_MANAGED_BY, WAS_FOUNDED_BY, HAS_BOARD_MEMBER, HAS_HEADQUARTER_IN, OFFERS, IS_LISTED_IN. If none of these relationships fit, then do not make any changes.
    Remember to only output a valid json with the format {{triples:[{{'node_from': '', 'relationship': '', 'node_to': ''}}]}}
    """

    result = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.2)).text
    result = result.replace("```json", "").replace("```", "").replace("'", "\"")

    try:
        new_triples = json.loads(result)

        new_triples_set = {json.dumps(t, sort_keys=True) for t in new_triples.get("triples")}
        old_triples_set = {json.dumps(t, sort_keys=True) for t in relevant_triples}

        intersection = set(new_triples_set).intersection(set(old_triples_set))
        intersection = [json.loads(s) for s in intersection]
        print("unchanged: " + str(intersection))

        added = set(new_triples_set).difference(set(old_triples_set))
        added = [json.loads(s) for s in added]
        print("added: " + str(added))

        deleted = set(old_triples_set).difference(set(new_triples_set))
        if "no triples found" in deleted:
            deleted = deleted.remove("no triples found")
        deleted = [json.loads(s) for s in deleted]
        print("deleted: " + str(deleted))

        return added, deleted, intersection
    except Exception as e:
        print(Fore.RED + f"JSONDecodeError: '{e}' with result: '{result}', try again" + Style.RESET_ALL)
        find_change_triples(article, name_company_at_center, node_type_requiring_change, relevant_triples, attempt + 1,
                            max_attempt,
                            driver)
    return False, False, False


def determine_triple_types(triple, nodes_to_include, attempt, max_attempt, ):
    if attempt >= max_attempt:
        return None, None

    prompt = f"""
        You are a classification assistant. You provide data to keep a Knowledge Graph about a company up to date. 
        Your task is to analyze a graph triple and select the the single best fitting node_type from a list.       

        Instructions:
        1. Read the provided graph triple carefully
        2. Review the list of available node_types: {nodes_to_include}.
        3. Select the node_types of the node_from and node_to
        4. If no category seems to fit, please use 'Product_or_Service'

        Example input:

        Input: {{'node_from': 'Henkel AG & Co. KGaA', 'relationship': 'IS_ACTIVE_IN', 'node_to': 'chemical industry'}}
        Available node_types = ['Company', 'Industry_Field', 'Manager', 'Founder', 'Board_Member', 'City', 'Country','Product_or_Service', 'Employer', 'StockMarketIndex']
        Output: {{'type_node_from': 'Company', 'type_node_to': 'Industry_Field'}}

        Input: {{'node_from': 'Continental AG', 'node_to': 'Nikolai Setzer', 'relationship': 'IS_MANAGED_BY'}}
        Available node_types = ['Company', 'Industry_Field', 'Manager', 'Founder', 'Board_Member', 'City', 'Country','Product_or_Service', 'Employer', 'StockMarketIndex']
        Output: {{'type_node_from': 'Company', 'type_node_to': 'Manager'}}


        Please analyze the following:
        Input: {triple}
        Available node_types: {nodes_to_include}       
        """

    result = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.2)).text
    result = result.replace("```json", "").replace("```", "").replace("'", "\"").replace("Output: ", "")

    try:
        result = json.loads(result)
        type_node_from = result.get("type_node_from")
        type_node_to = result.get("type_node_to")
        if (type_node_from in nodes_to_include) and (type_node_to in nodes_to_include):
            print(
                Fore.GREEN + f"Determined type_node_from = '{type_node_from}' and type_node_to = '{type_node_to}'" + Style.RESET_ALL)
            return type_node_from, type_node_to
        else:
            determine_triple_types(triple, nodes_to_include, attempt + 1, max_attempt)
    except Exception as e:
        print(
            Fore.RED + f"JSONDecodeError while trying to determine node types: '{e}' with result: '{result}', try again" + Style.RESET_ALL)
        determine_triple_types(triple, nodes_to_include, attempt + 1, max_attempt)


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

    name = _generate_result_from_llm(prompt, enum=companies, max_output_tokens=30, temperature=0.4)

    if name not in companies:
        find_company_at_center(article, companies, attempt + 1, max_attempt)

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

    result = _generate_result_from_llm(prompt, enum=node_types)
    return result


def formal_sanity_check(added, deleted, relevant_triples) -> dict:
    """
    Performs sanity checks on proposed knowledge graph updates.

    Args:
        added: List of triples to be added
        deleted: List of triples to be deleted
        relevant_triples: List of existing triples in the graph
        article: Text of the news article

    Returns:
        dict: Contains validation results with format:
            {
                'correct_update': bool,
                'reasoning': str,
                'how_to_correct_the_mistake': str
            }
    """
    result = {
        'correct_update': True,
        'reasoning': '',
        'how_to_correct_the_mistake': ''
    }

    # Check 1: Verify we're not simultaneously adding and deleting the same triple
    overlapping_triples = [t for t in added if t in deleted]
    if overlapping_triples:
        result.update({
            'correct_update': False,
            'reasoning': f"Contradiction: Same triple(s) appearing in both added and deleted lists: {overlapping_triples}",
            'how_to_correct_the_mistake': "Review the triples and ensure no triple is both added and deleted"
        })
        return result

    # Check 2: Verify deleted triples exist in relevant_triples
    invalid_deletions = [t for t in deleted if t not in relevant_triples]
    if invalid_deletions:
        result.update({
            'correct_update': False,
            'reasoning': f"Invalid deletion: Attempting to delete non-existent triples: {invalid_deletions}",
            'how_to_correct_the_mistake': "Only delete triples that exist in the current graph"
        })
        return result

    # Check 3: Verify relationship types are valid
    valid_relationships = {
        "OWNS", "PARTNERS_WITH", "IS_ACTIVE_IN", "IS_MANAGED_BY",
        "WAS_FOUNDED_BY", "HAS_BOARD_MEMBER", "HAS_HEADQUARTER_IN",
        "OFFERS", "IS_LISTED_IN"
    }

    invalid_relationships = []
    for triple in added + deleted:
        if triple['relationship'] not in valid_relationships:
            invalid_relationships.append(triple)

    if invalid_relationships:
        result.update({
            'correct_update': False,
            'reasoning': f"Invalid relationship types found: {invalid_relationships}",
            'how_to_correct_the_mistake': f"Use only valid relationship types: {valid_relationships}"
        })
        return result

    # If all checks pass
    if result['correct_update']:
        result[
            'reasoning'] = "All sanity checks passed: Changes are consistent with current graph and article content"
        result['how_to_correct_the_mistake'] = "No corrections needed"

    return result


def llm_sanity_check(added, deleted, relevant_triples, article):
    """
    Validates the logical reasoning of proposed knowledge graph updates.

    Args:
        added: List of triples to be added
        deleted: List of triples to be deleted
        relevant_triples: List of existing triples in the graph
        article: Text of the news article

    Returns:
        dict: Validation results with format:
            {
                'correct_update': bool,
                'reasoning': str,
                'how_to_correct_the_mistake': str
            }
    """

    prompt = f"""
    You are a validation expert for knowledge graph updates. Your task is to analyze whether the proposed changes to a knowledge graph make logical sense given the article content.

    Context:
    - Article: "{article}"
    - Existing triples in graph: {relevant_triples}
    - Proposed additions: {added}
    - Proposed deletions: {deleted}

    Please analyze the following aspects:

    1. Temporal Logic:
    - Are the changes based on events that have actually happened (not just announcements or possibilities)?
    - Do the changes respect chronological order of events?

    2. Causal Logic:
    - Is there a clear cause-effect relationship supporting each change?
    - Are the changes supported by explicit statements in the article?

    3. Business Logic:
    - Do the changes align with typical business relationships and operations?
    - Are the relationship types appropriate for the entities involved?

    4. Consistency:
    - Are there any contradictions between added and deleted triples?
    - Do the changes maintain the graph's overall consistency?

    5. Completeness:
    - Are all relevant changes from the article captured?
    - Are there any unnecessary changes not supported by the article?

    Please provide your analysis in the following JSON format:
    {{
        'correct_update': boolean,
        'reasoning': "Detailed explanation of why the updates are correct or incorrect",
        'how_to_correct_the_mistake': "If incorrect, provide specific guidance on how to fix the issues"
    }}

    Only respond with valid JSON. Focus on logical reasoning rather than technical validation.
    """

    response = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.6)).text

    try:
        return _parse_llm_reasoning_check_response(response)
    except json.JSONDecodeError as e:
        return {
            'correct_update': False,
            'reasoning': 'Failed to parse validation response',
            'how_to_correct_the_mistake': 'Please review the updates manually',
            'JSONDecodeError': str(e)
        }


"""functions below are helper functions"""


def _get_and_increment_customID(driver):
    global custom_id

    custom_id = get_latest_custom_id("CustomID", driver)
    custom_id += 1

    custom_node_id = "CustomID" + str(custom_id)
    return custom_node_id


def _add_relationship(triple: Dict, nodes_to_include: List[str], driver) -> None:
    """Helper function to add new relationship to graph."""
    try:
        # Determine node types
        node_type_from, node_type_to = determine_triple_types(triple, nodes_to_include, 1, 3)
        if not all([node_type_from, node_type_to]):
            print(Fore.RED + f"Missing node type for triple {triple}" + Style.RESET_ALL)
            return

        name_node_from = triple["node_from"]
        name_node_to = triple["node_to"]

        # Create/get nodes and relationship
        id_node_from = _get_or_create_node_id(name_node_from, driver)
        id_node_to = _get_or_create_node_id(name_node_to, driver)

        create_new_node(
            id_node_from,
            node_type_from,
            properties=build_node_properties(id_node_from, node_type_from, name_node_from),
            driver=driver,
        )

        create_new_node(
            id_node_to,
            node_type_to,
            properties=build_node_properties(id_node_to, node_type_to, name_node_to),
            driver=driver,
        )

        create_relationship(
            triple["relationship"],
            id_node_from,
            id_node_to,
            str(datetime.now(timezone.utc)),
            "NA",
            driver,
            name_org_node=triple["node_from"],
            name_rel_node=triple["node_to"]
        )
    except KeyError as e:
        print(Fore.RED + f"Error adding relationship {triple}: {e}" + Style.RESET_ALL)


def _mark_relationship_ended(triple: Dict, driver) -> None:
    """Helper function to mark relationship as ended."""
    try:
        # Find nodes
        source_id = find_node_by_wikidata_id(triple["node_from"], driver) or \
                    wikidata_wbsearchentities(triple["node_from"], id_or_name='id')
        target_id = find_node_by_wikidata_id(triple["node_to"], driver) or \
                    wikidata_wbsearchentities(triple["node_to"], id_or_name='id')

        # Update end time for active relationships
        relationships = get_node_relationships(source_id, target_id, driver)
        for rel in relationships:
            if rel['rel_end_time'] == "NA":
                _update_end_time(rel, triple, driver)

    except KeyError as e:
        print(Fore.RED + f"Error ending relationship {triple}: {e}" + Style.RESET_ALL)


def _update_end_time(rel: Dict, triple: Dict, driver) -> None:
    """Helper function to update relationship end time."""
    rel_id, end_time = update_relationship_property(
        rel['rel_id'],
        "end_time",
        str(datetime.now(timezone.utc)),
        driver
    )
    if rel_id:
        print(Fore.GREEN +
              f"Updated end time for {triple['node_from']} -> {triple['node_to']} to {end_time}" +
              Style.RESET_ALL)


def _generate_result_from_llm(prompt, enum=None, ResponseSchema=None, temperature=0.5, max_output_tokens=30):
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


def _get_or_create_node_id(node_name: str, driver: Driver) -> str:
    """Gets existing node ID or creates new node with generated ID.

    Attempts to find existing node by Wikidata ID, then searches Wikidata,
    and finally creates custom ID if needed.

    Args:
        node_name: Name of node to find/create
        driver: Neo4j driver instance

    Returns:
        str: Node ID (either existing or newly created)
    """
    # Try to find existing node or get Wikidata ID
    node_id = (
            find_node_by_wikidata_id(node_name, driver) or
            wikidata_wbsearchentities(node_name, id_or_name='id')
    )

    # Generate custom ID if needed
    if node_id == "No wikidata entry found":
        node_id = _get_and_increment_customID(driver)

    # Create/update node and return ID
    return node_id


def _parse_llm_reasoning_check_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response with robust handling of problematic characters.

    Args:
        response: Raw string response from LLM
    """
    default = {
        'correct_update': False,
        'reasoning': "Failed to parse response",
        'how_to_correct_the_mistake': None
    }

    try:
        # Extract each field separately using regex
        correct_update_match = re.search(r'"correct_update":\s*(true|false)', response)
        reasoning_match = re.search(r'"reasoning":\s*"([^"]*(?:"[^"]*"[^"]*)*)"', response)
        correction_match = re.search(r'"how_to_correct_the_mistake":\s*(null|"[^"]*")', response)

        if not correct_update_match:
            return default

        result = {
            'correct_update': correct_update_match.group(1).lower() == 'true',
            'reasoning': reasoning_match.group(1) if reasoning_match else 'No reasoning provided',
            'how_to_correct_the_mistake': None if (not correction_match or correction_match.group(1) == 'null')
            else correction_match.group(1).strip('"')
        }

        return result

    except Exception as e:
        print(f"Failed to parse response: {e}")
        return default


"""functions below are  currently not in use , but might be used for future functionality"""


def _get_datetime_now_and_max():
    rel_wikidata_start_time = str(datetime.now().replace(tzinfo=timezone.utc))
    rel_wikidata_end_time = str(datetime.max.replace(tzinfo=timezone.utc))
    return rel_wikidata_start_time, rel_wikidata_end_time


def _update_node_properties_dict(article, properties_dict, response_schema):
    # todo: currently not implemented, does not support changing of node properties
    prompt = f"""
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
    print(
        f"Found property of '{key}' requires a change according to article '{article}' and properties '{properties_dict}")

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

    class ResponseSchema(response_schema.ResponseSchema):
        # todo
        test = "test"

    result = _generate_result_from_llm(prompt, ResponseSchema=ResponseSchema, temperature=0.3, max_output_tokens=40)
    updated_node_property = json.loads(result)
    updated_node_property = updated_node_property["new_value"]

    properties_dict[key] = updated_node_property

    print(f"Updated nodes properties dict to '{properties_dict}' for article '{article}'")
    return properties_dict
