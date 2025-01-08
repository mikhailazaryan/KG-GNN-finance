import configparser
import google.generativeai as genai


model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Choose the desired model

config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

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

def update_neo4j_graph(article, companies, node_types, driver):
    company = find_company(article, companies)
    node_type = find_node_type(article, node_types)
    most_relevant_node = find_most_relevant_node(article, company, node_type, driver)
    #todo: now determine the type of change (add new node, delete existing node, modify existing node, modify relationship between two existing nodes) using an llm
    # then make the change using 4 different json templates as structured output (see here https://ai.google.dev/gemini-api/docs/structured-output?lang=python)
    # issues: secondary connections are not taken into account (e.g. Allianz SE subsiary company1 bought company 2), maybe I can iteratively increase the scope? This should happen in the find company field

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

    result = model.generate_content(
        [prompt, article],
        generation_config=genai.GenerationConfig(
            response_mime_type="text/x.enum",
            response_schema={
                "type": "STRING",
                "enum": companies,
            },
        ),
    )
    print(f"Found company '{result.text}' for article '{article}' and companies '{companies}'.")
    return result.text

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

    result = model.generate_content(
        [prompt, article],
        generation_config=genai.GenerationConfig(
            response_mime_type="text/x.enum",
            response_schema={
                "type": "STRING",
                "enum": node_types,
            },
        ),
    )
    print(f"Found node_type of '{result.text}' for article '{article}' and node_types '{node_types}")
    return result.text

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
    if node_type == ("Company"):
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

    result = model.generate_content(
        [prompt, article],
        generation_config=genai.GenerationConfig(
            response_mime_type="text/x.enum",
            response_schema={
                    "type": "STRING",
                    "enum": relevant_nodes,
                },
            ),
        )
    print(f"Found node '{result.text}' to be most relevant for article '{article}' and relevant nodes '{relevant_nodes}")
    return result.text

