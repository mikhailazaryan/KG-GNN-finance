from dataclasses import replace

from neo4j import GraphDatabase
import json
from stockdata2KG.crawler import crawl_wikidata
from stockdata2KG.fill_template import fill_template
from stockdata2KG.graphbuilder import initialize_graph, neo4j_uri
from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities


def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     id_of_company = wikidata_wbsearchentities("Apple Inc", 'id')
     wikidata = wikidata_wbgetentities(id_of_company)
     fill_template(id_of_company, wikidata)


if __name__ == "__main__":
    main()
