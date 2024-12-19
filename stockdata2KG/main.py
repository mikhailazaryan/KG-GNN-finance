from datetime import datetime, timezone
from neo4j import GraphDatabase
from colorama import init, Fore, Back, Style


from stockdata2KG.files.wikidata_cache.wikidataCache import WikidataCache
from stockdata2KG.graphbuilder import (create_placeholder_node_in_neo4j, populate_placeholder_node_in_neo4j,
                                       create_relationships_and_placeholder_nodes_for_node_in_neo4j, \
                                       return_all_wikidata_ids_of_nodes_without_relationships,
                                       return_wikidata_id_of_all_placeholder_nodes, create_demo_graph)
from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities

import google.generativeai as genai

model = genai.GenerativeModel("gemini-pro")

genai.configure(api_key="AIzaSyDelNHiE50S_HsupCznAy9Zrphz_6d9dTY")



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




def main():
     init() # for colorama

     wikidata_wbgetentities("Q116170621", True) #just for inspecting the wggetentities.json

     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4j"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
     reset_graph(driver)

     # this builds the initial graph from wikidata
     company_names = ["Allianz SE", "Microsoft", "BlaBlaCar"]
     date_from = datetime(1995, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
     date_until = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
     nodes_to_include = ["InitialCompany", "Company", "Industry", "Person", "City", "Country", "StockMarketIndex"]
     search_depth = 5

     for company_name in company_names:
          print(Fore.GREEN + f"\n---Started building graph for {company_name}---\n" + Style.RESET_ALL)
          build_initial_graph(company_name, date_from, date_until, nodes_to_include, search_depth, driver)
          print(Fore.GREEN + f"\n--- Finished building graph for {company_name}---\n" + Style.RESET_ALL)

     print(f"\n--- Successfully finished building neo4j graph for company {company_names} with a depth of {search_depth} ---\n")



     WikidataCache.print_current_stats()

     #create_demo_graph(driver)

     model = genai.GenerativeModel("gemini-pro")  # Choose the desired model
     genai.configure(api_key="AIzaSyCArmUNcsj4EX-SjeU0XlF0hMY_Oet4CCI")

     # News article text (synthetic example, not crawled)
     article_text = """
         Allianz SE moved their headquarter from Munich to Berlin 
         """

     news1 = ["Allianz SE moved their headquarter from Munich to Berlin","Allianz SE bought SportGear AG","Allianz SE","Allianz SE is no longer active in insurance","Allianz SE sold PIMCO", "Allianz SE is not listed in EURO STOXX 50 anymore"]
     news2 = ["Allianz SE bought SportGear AG headquartered in Cologne", "Allianz SE moved their headquarter from Munich to Berlin", "Allianz SE moved their headquarter from Berlin to Frankfurt", "Allianz SE is no longer active in insurance, woodworking is a new business field of Allianz SE", "Allianz SE was renamed to Algorithm GmbH"]

     #todiscuss: #todo: (1) Mehr syntetische und echte News nachrichten, ggf. mit preprocessing/cleaning (which are allowed to be crawled)
     #todiscuss: #todo (2) News Keyword extraction and graph retrieval and updating
     #DONE #todo:         - veränderliche schwierigkeiten
     #todo:         -
     #todo (3) More detailed Nodes Information from Wikidata




     #Process the article and update the graph
     process_news_and_update_KG(article_text, driver)


def build_initial_graph(company_name, date_from, date_until, nodes_to_includel, search_depth, driver):

     # initialize first placeholder node of company name
     wikidata_id_of_company = wikidata_wbsearchentities(company_name)
     create_placeholder_node_in_neo4j(wikidata_id_of_company, "InitialCompany", driver)
     populate_placeholder_node_in_neo4j(wikidata_id_of_company, driver)

     # iteratively adding nodes and relationships
     for i in range(search_depth):
          print(Fore.BLUE + f"\n---Started building graph for {company_name} on depth {i}---\n"+ Style.RESET_ALL)
          for wikidata_id in return_all_wikidata_ids_of_nodes_without_relationships(driver):
               create_relationships_and_placeholder_nodes_for_node_in_neo4j(org_wikidata_id=wikidata_id,
                                                                            from_date_of_interest= date_from,
                                                                            until_date_of_interest=date_until,
                                                                            nodes_to_include=nodes_to_includel,
                                                                            driver=driver)

          for wikidata_id in return_wikidata_id_of_all_placeholder_nodes(driver):
               populate_placeholder_node_in_neo4j(wikidata_id, driver)
          print(Fore.BLUE + f"\n---Finished building graph for {company_name} on depth {i}---\n" + Style.RESET_ALL)

def reset_graph(driver):
     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4jtest"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

     with driver.session() as session:
          session.run("MATCH(n) DETACH DELETE n")

if __name__ == "__main__":
    main()
