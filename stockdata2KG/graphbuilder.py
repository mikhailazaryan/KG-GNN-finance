import json

import neo4j as neo
from neo4j import GraphDatabase
import csv

## Setup connection to Neo4j
neo4j_uri = "neo4j://localhost:7687"
username = "neo4j"
password = "neo4j"

## File Paths
csv_file = './files/Unicorn_Companies.csv'

def initialize_graph(json_path):
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    # global json_path

    with open(json_path, 'r') as f:
        data = json.load(f)

    # this creates only the central company node
    print(f"Initializing graph from {json_path}")
    print(data.get("name"))

    create_company_node(data, driver)


    # todo: create all other initial nodes defined in crawler



def create_company_node(data, driver):
    print("test: " +str(data))
    with driver.session() as session:
        # intitally delete all existing nodes
        session.run("MATCH(n) DETACH DELETE n")

        # create initial company node
        # query = "CREATE (c:Company {name: $name, isin: $isin, inception: $inception})"
        # params = {
        #    "name": data["company"]["properties"]["name"],
        #    "isin": data["company"]["properties"]["isin"],
        #    "inception": data["company"]["properties"]["founding_date"]
        # }
        # session.run(query, params)

        for key, entity in data.items():
            label = entity["label"]
            properties = entity["properties"]

            create_node(session, label, properties)

            if "relationships" in entity:
                for rel in entity["relationships"]:
                    create_relationship(session, label, properties, rel)


def create_node(session, label, properties):
    query = f"CREATE (n:{label} {{ {', '.join([f'{k}: ${k}' for k in properties.keys()])} }})"
    session.run(query, properties)
    print(f"Node created: {label} with properties {properties}")

def create_relationship(session, source_label, source_properties, relationship):
    target_label = relationship["target_label"]
    rel_type = relationship["type"]

    target_properties = {"name": f"Placeholder {target_label}"}

    # Match or create target node
    target_query = f"""
    MERGE (t:{target_label} {{name: $name}})
    RETURN t
    """
    session.run(target_query, target_properties)

    # Create relationship
    rel_query = f"""
    MATCH (s:{source_label} {{name: $source_name}})
    MATCH (t:{target_label} {{name: $target_name}})
    CREATE (s)-[:{rel_type}]->(t)
    """
    session.run(rel_query, {
        "source_name": source_properties["name"],
        "target_name": target_properties["name"]
    })
    print(f"Relationship created: {source_label} -[{rel_type}]-> {target_label}")

