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



def main():
     init() # for colorama

     wikidata_wbgetentities("Q116170621", True) #just for inspecting the wggetentities.json

     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4jtest"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
     reset_graph(driver)

     # this builds the initial graph from wikidata
     company_names = ["Allianz SE", "Commerzbank AG", "BASF SE"]
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



     #Process the article and update the graph
     #process_news_and_update_KG(article_text, driver)


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