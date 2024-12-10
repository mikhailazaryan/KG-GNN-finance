from neo4j import GraphDatabase

from stockdata2KG.graphbuilder import (create_placeholder_node_in_neo4j, populate_placeholder_node_in_neo4j,
                                       create_relationships_and_placeholder_nodes_for_node, \
                                       return_all_placeholder_node_wikidata_ids, return_all_nodes_without_relationships)
from stockdata2KG.wikidata import wikidata_wbsearchentities


def main():
     #just input a company, e.g. "Apple Inc" or "Allianz SE"
     #wikidata = wikidata_wbgetentities(wikidata_id_of_company)

     #fill_template(wikidata_id_of_company, wikidata)

     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4jtest"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

     with driver.session() as session:
          session.run("MATCH(n) DETACH DELETE n")

     company_name = "Munich RE"

     # initialize first placeholder node of company name
     wikidata_id_of_company = wikidata_wbsearchentities(company_name)
     create_placeholder_node_in_neo4j(wikidata_id_of_company, "Company", driver)

     # fill first placeholder node of company with information
     #populate_placeholder_node_in_neo4j(wikidata_id_of_company, driver)

     # create relationships for the first company node
     #create_relationships_and_placeholder_nodes_for_node(wikidata_id_of_company, driver)

     # iteratively adding nodes and relationships
     search_depth = 2
     for i in range(search_depth):
          wikidata_ids_of_current_nodes_without_relationships = return_all_nodes_without_relationships(driver)
          for wikidata_id in wikidata_ids_of_current_nodes_without_relationships:
               create_relationships_and_placeholder_nodes_for_node(wikidata_id, driver)

          wikidata_ids_of_current_placeholder_nodes = return_all_placeholder_node_wikidata_ids(driver)
          for wikidata_id in wikidata_ids_of_current_placeholder_nodes:
               populate_placeholder_node_in_neo4j(wikidata_id, driver)

     print(f" ---- sucessfully finised initializing neo4j graph for company {company_name} with a depth of {search_depth} ----")



     # News article text (synthetic example, not crawled)
     article_text = """
         Allianz SE moved their headquarter from Munich to Berlin 
         """

     #Process the article and update the graph
     #process_news_and_update_KG(article_text, driver)


if __name__ == "__main__":
    main()
