from neo4j import GraphDatabase

from stockdata2KG.graphbuilder import (create_placeholder_node_in_neo4j, populate_placeholder_node_in_neo4j,
                                       create_relationships_and_placeholder_nodes_for_node_in_neo4j, \
                                       return_all_wikidata_ids_of_nodes_without_relationships,
                                       return_wikidata_id_of_all_placeholder_nodes)
from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities


def main():
     #just input a company, e.g. "Apple Inc" or "Allianz SE"
     #wikidata = wikidata_wbgetentities(wikidata_id_of_company)

     #fill_template(wikidata_id_of_company, wikidata)
     wikidata_wbgetentities("Q166637", True)

     company_name = "Munich RE"
     build_initial_graph(company_name)


     # News article text (synthetic example, not crawled)
     article_text = """
         Allianz SE moved their headquarter from Munich to Berlin 
         """

     #Process the article and update the graph
     #process_news_and_update_KG(article_text, driver)


def build_initial_graph(company_name):
     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4jtest"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

     with driver.session() as session:
          session.run("MATCH(n) DETACH DELETE n")


     # initialize first placeholder node of company name
     wikidata_id_of_company = wikidata_wbsearchentities(company_name)
     create_placeholder_node_in_neo4j(wikidata_id_of_company, "Company", driver)

     # iteratively adding nodes and relationships
     search_depth = 4
     for i in range(search_depth):
          wikidata_ids_of_current_nodes_without_relationships = return_all_wikidata_ids_of_nodes_without_relationships(driver)
          for wikidata_id in wikidata_ids_of_current_nodes_without_relationships:
               create_relationships_and_placeholder_nodes_for_node_in_neo4j(wikidata_id, driver)

          wikidata_ids_of_current_placeholder_nodes = return_wikidata_id_of_all_placeholder_nodes(driver)
          for wikidata_id in wikidata_ids_of_current_placeholder_nodes:
               populate_placeholder_node_in_neo4j(wikidata_id, driver)

     wikidata_ids_of_current_placeholder_nodes = return_wikidata_id_of_all_placeholder_nodes(driver)
     for wikidata_id in wikidata_ids_of_current_placeholder_nodes:
          populate_placeholder_node_in_neo4j(wikidata_id, driver)

     print(
          f" ---- sucessfully finised initializing neo4j graph for company {company_name} with a depth of {search_depth} ----")


if __name__ == "__main__":
    main()