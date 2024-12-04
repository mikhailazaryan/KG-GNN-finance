from neo4j import GraphDatabase

from stockdata2KG.fill_template import fill_template
from stockdata2KG.graphbuilder import initialize_graph
from stockdata2KG.llm import process_news_and_update_KG
from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities


def main():
     #just input a company, e.g. "Apple Inc" or "Allianz SE"
     id_of_company = wikidata_wbsearchentities("Munich RE", 'id')
     wikidata = wikidata_wbgetentities(id_of_company)
     fill_template(id_of_company, wikidata)

     ## Setup connection to Neo4j
     neo4j_uri = "neo4j://localhost:7687"
     username = "neo4j"
     password = "neo4jtest"

     driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

     json_initial_graph_data_path = "files/initial_graph_data/template_with_data.json"
     initialize_graph(json_initial_graph_data_path, driver)

     # News article text (synthetic example, not crawled)
     article_text = """
         Allianz SE moved their headquarter from Munich to Berlin 
         """

     #Process the article and update the graph
     #process_news_and_update_KG(article_text, driver)


if __name__ == "__main__":
    main()
