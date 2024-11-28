import json

import neo4j as neo
from neo4j import GraphDatabase
import csv

## Setup connection to Neo4j
neo4j_uri = "neo4j://localhost:7687"
username = "neo4j"
password = "neo4jtest"

## File Paths
csv_file = './files/Unicorn_Companies.csv'

def initialize_graph(json_path):
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

    # this creates only the central company node
    data = json.load(json_path)
    create_company_node(data, driver)

    # todo: create all other initial nodes defined in crawler



def create_company_node(company_dict, driver):
    print("test: " +str(company_dict))
    with driver.session() as session:
        # intitally delete all existing nodes
        session.run("MATCH(n) DETACH DELETE n")

        # create initial company node
        query = "CREATE (c:Company {name: $name, isin: $isin, inception: $inception})"
        params = {
            "name": company_dict["node"],
            "isin": company_dict["isin"],
            "inception": company_dict["inception"]
        }
        session.run(query, params)








