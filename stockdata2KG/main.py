from neo4j import GraphDatabase

from stockdata2KG.crawler import crawl_wikidata
from stockdata2KG.graphbuilder import initialize_graph, neo4j_uri


def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     list_of_initial_data = crawl_wikidata("Allianz SE")
     initialize_graph(# todo make this read from json)





if __name__ == "__main__":
    main()
