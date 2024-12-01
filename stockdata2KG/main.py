from dataclasses import replace

from neo4j import GraphDatabase
import json
from stockdata2KG.crawler import crawl_wikidata
from stockdata2KG.fill_template import fill_template
from stockdata2KG.graphbuilder import initialize_graph
#from stockdata2KG.llm import process_article_and_update_graph, connect_to_neo4j
from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities


def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     id_of_company = wikidata_wbsearchentities("Microsoft", 'id')
     wikidata = wikidata_wbgetentities(id_of_company)
     fill_template(id_of_company, wikidata)

     json_initial_graph_data_path = "files/initial_graph_data/template_with_data.json"
     initialize_graph(json_initial_graph_data_path)

    # graph = connect_to_neo4j("bolt://localhost:7687", "neo4j", "neo4jtest")

     # Example article text
     article_text = """
         Example News 
         """

     # Process the article and update the graph
     #process_article_and_update_graph(graph, article_text)


if __name__ == "__main__":
    main()
