import configparser
from datetime import datetime, timezone
from neo4j import GraphDatabase
from colorama import init, Fore, Style
import random

from arcticles import get_synthetic_articles
from graphbuilder import build_demo_graph, build_graph_from_initial_node, reset_graph
from graphupdater import update_neo4j_graph
from wikidata.wikidataCache import WikidataCache


def main():
     init() # for colorama

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


     build_graph_bool = True
     update_graph_bool = True

     # this builds the initial graph from wikidata
     companies_to_include_in_graph = ["MTU Aero Engines AG"]
     DAX_companies = ["Adidas AG", "Airbus SE", "Allianz SE", "BASF SE", "Bayer AG", "Beiersdorf AG",
                      "Bayerische Motoren Werke AG", "Brenntag SE", "Commerzbank AG", "Continental AG", "Covestro AG",
                      "Daimler Truck Holding AG", "Deutsche Bank AG", "Deutsche Börse AG", "Deutsche Post AG",
                      "Deutsche Telekom AG", "E.ON SE", "Fresenius SE & Co. KGaA", "Hannover Rück SE",
                      "Heidelbergcement AG", "Henkel AG & Co. KGaA", "Infineon Technologies AG",
                      "Mercedes-Benz", "Merck KGaA", "MTU Aero Engines AG",
                      "Münchener Rückversicherungs-Gesellschaft AG", "Dr. Ing. h.c. F. Porsche AG",
                      "Porsche Automobil Holding SE", "QIAGEN N.V.", "Rheinmetall AG", "RWE AG", "SAP SE",
                      "Sartorius AG", "Siemens AG", "Siemens Energy AG", "Siemens Healthineers AG", "Symrise AG",
                      "Volkswagen AG", "Vonovia SE", "Zalando SE"]

     #companies_to_include_in_graph = DAX_companies

     date_from = datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
     date_until = datetime(2024, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
     nodes_to_include = ["Company", "Industry_Field", "Manager", "Founder", "Board_Member", "City", "Country", "Product_or_Service", "Employer", "StockMarketIndex"]
     search_depth = 2

     if build_graph_bool:
         reset_graph(driver)
         for company_name in companies_to_include_in_graph:
              print(Fore.GREEN + f"\n---Started building graph for {company_name}---\n" + Style.RESET_ALL)
              build_graph_from_initial_node(company_name, "Company", date_from, date_until, nodes_to_include, search_depth, driver)
              print(Fore.GREEN + f"\n--- Finished building graph for {company_name}---\n" + Style.RESET_ALL)

              # reduce unuseful cache information in 30% of the time,
              if random.random() < 0.1:
                WikidataCache.strip_cache()

         print(f"\n--- Successfully finished building neo4j graph for companies {companies_to_include_in_graph} with a depth of {search_depth} ---\n")

         print("")
         WikidataCache.print_current_stats()
         print("")


     if update_graph_bool:
         print(Fore.LIGHTMAGENTA_EX + f"\n--- Stated updating existing neo4j graph ---\n" + Style.RESET_ALL)

         synthetic_articles_list = get_synthetic_articles(companies_to_include_in_graph)
         for synthetic_articles in synthetic_articles_list:
             for synthetic_article in synthetic_articles.values():
                 update_neo4j_graph(synthetic_article, companies_to_include_in_graph, nodes_to_include, date_from, date_until, nodes_to_include, search_depth_new_nodes=1, search_depth_for_changes=search_depth, driver=driver)

         print(Fore.LIGHTMAGENTA_EX + f"\n--- Finished updating existing neo4j graph ---\n" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
