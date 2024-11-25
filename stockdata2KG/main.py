from stockdata2KG.crawler import crawl_wikidata
from stockdata2KG.graphbuilder import initialize_graph, build_graph


def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     crawl_wikidata("Allianz SE")
     initialize_graph()

     # then go to browser and type http://localhost:7474/browser


if __name__ == "__main__":
    main()
