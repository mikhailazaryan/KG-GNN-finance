import configparser
from datetime import datetime, timezone
from neo4j import GraphDatabase
from colorama import init, Fore, Style


from stockdata2KG.files.wikidata_cache.wikidataCache import WikidataCache
from stockdata2KG.graphbuilder import build_demo_graph, build_graph_from_initial_node, reset_graph
from stockdata2KG.graphupdater import process_news_and_update_KG, update_neo4j_graph, find_node_requiring_change


def main():
     init() # for colorama

     #wikidata_wbgetentities("Q116170621", True) # just for inspecting the wggetentities.json

     ## Setup connection to Neo4j
     config = configparser.ConfigParser()
     config.read('config.ini')
     neo4j_uri = config['neo4j']['uri']
     username = config['neo4j']['username']
     password = config['neo4j']['password']
     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

     try:
        driver.verify_connectivity()
        print("Connection successful!")
     except Exception as e:
        print(f"Connection failed: {e}")

     build_actual_graph_bool = True
     build_demo_graph_bool = False
     update_graph_bool = True

     # this builds the initial graph from wikidata
     company_names = ["Allianz SE"]
     date_from = datetime(1995, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
     date_until = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
     nodes_to_include = ["Company", "Industry_Field", "Person", "City", "Country", "StockMarketIndex"]
     search_depth = 3

     if build_actual_graph_bool:
         reset_graph(driver)
         for company_name in company_names:
              print(Fore.GREEN + f"\n---Started building graph for {company_name}---\n" + Style.RESET_ALL)
              build_graph_from_initial_node(company_name, "Company", date_from, date_until, nodes_to_include, search_depth, driver)
              print(Fore.GREEN + f"\n--- Finished building graph for {company_name}---\n" + Style.RESET_ALL)

         print(f"\n--- Successfully finished building neo4j graph for companies {company_names} with a depth of {search_depth} ---\n")

         WikidataCache.print_current_stats()


     if build_demo_graph_bool:
        reset_graph(driver)
        build_demo_graph(driver)
        print(
            f"\n--- Successfully finished building neo4j demo graph ---\n")

     if update_graph_bool:
         print(Fore.LIGHTMAGENTA_EX + f"\n--- Stated updating existing neo4j graph ---\n" + Style.RESET_ALL)


         articles = {
             "article_1" : "Allianz SE moved their headquarter from Munich to Berlin",
             "article_2" : "Allianz SE bought Ergo Group",
             "article_3" : "Allianz SE is no longer active in the insurance industry",
             "article_4" : "Allianz SE sold PIMCO",
             "article_5" : "Allianz SE is not listed in EURO STOXX 50 anymore",
             "article_6" : "Allianz SE bought SportGear AG headquartered in Cologne",
             "article_7" : "Allianz SE bought Jamo Data GmbH headquartered in Jena",
             "article_8" : "Allianz SE moved their headquarter from Berlin to Frankfurt",
             "article_9" : "Woodworking is a new business field of Allianz SE",
             "article_10" : "Allianz SE was renamed to Algorithm GmbH",
             "article_11" : "Westbank was renamed to Westbank Privatbank"
         }


         #todo:
         #  (1) Better and more realistic prompts,
         #  (3) More detailed Nodes Information from Wikidata
         #  (4) test on more prompts and extend the graphupdater function to also handle more changes, especially in _get_relationship_properties



         nodes_to_include = ["Company", "Industry_Field", "Person", "City", "Country", "StockMarketIndex"] # only temporatry, seems like it works best with industry field
         company_names = ["Allianz SE", "Volkswagen AG"] # temporary


         for article in articles.values():
            print("\n")
            update_neo4j_graph(article, company_names, nodes_to_include, date_from, date_until, nodes_to_include, search_depth_new_nodes=1, search_depth_for_changes=search_depth, driver=driver)
         #update_neo4j_graph(articles.get('article_11'), company_names, nodes_to_include, date_from, date_until, nodes_to_include, 1, driver)

     print(Fore.LIGHTMAGENTA_EX + f"\n--- Finished updating existing neo4j graph ---\n" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
