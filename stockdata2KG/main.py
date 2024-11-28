from neo4j import GraphDatabase

from stockdata2KG.crawler import crawl_wikidata
from stockdata2KG.graphbuilder import initialize_graph, neo4j_uri


def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     list_of_initial_data = crawl_wikidata("Allianz SE")

     json_initial_graph_data_path = "files/initial_graph_data/inital_graph_data_in_own_format.json"
     initialize_graph(json_initial_graph_data_path)





if __name__ == "__main__":
    main()
