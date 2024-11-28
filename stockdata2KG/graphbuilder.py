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

def initialize_graph(path):
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    global json_path

    with open(path, 'r') as f:
        data = json.load(f)

    # this creates only the central company node

    print(data.get("name"))

    create_company_node(data, driver)


    # todo: create all other initial nodes defined in crawler



def create_company_node(data, driver):
    print("test: " +str(data))
    with driver.session() as session:
        # intitally delete all existing nodes
        session.run("MATCH(n) DETACH DELETE n")

        # create initial company node
        query = "CREATE (c:Company {name: $name, isin: $isin, inception: $inception})"
        params = {
            "name": data["company"]["properties"]["name"],
            "isin": data["company"]["properties"]["isin"],
            "inception": data["company"]["properties"]["founding_date"]
        }
        session.run(query, params)








