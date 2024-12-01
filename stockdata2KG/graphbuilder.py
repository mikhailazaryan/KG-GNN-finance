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
    # global json_path

    with open(json_path, 'r') as f:
        data = json.load(f)

    print(f"Initializing graph from {json_path}")
    print(data.get("name"))

    create_company_node(data, driver)




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
                    create_relationship(session, label, properties, rel, data)


def create_node(session, label, properties):
    #query = f"CREATE (n:{label} {{ {', '.join([f'{k}: ${k}' for k in properties.keys()])} }})"
    query = f"MERGE (n:{label} {{ {', '.join([f'{k}: ${k}' for k in properties.keys()])} }})"
    session.run(query, properties)
    print(f"Node created: {label} with properties {properties}")



def create_relationship(session, source_label, source_properties, relationship, data):
    try:
        target_label = relationship.get("target_label")
        rel_type = relationship.get("type")

        if not target_label:
            print(f"Skipping relationship with type {rel_type} due to missing target_label.")
            return

        #target_name = relationship.get("properties", {}).get("name")
        #target = data[target_label]["properties"]["name"]

        target_name = None
        for key, value in data.items():
            if value.get("label") == target_label:
                    target_name = value.get("properties", {}).get("name")
                    break  # Exit loop once the match is found



        if not target_name:
            print(f"Skipping relationship with type {rel_type}: Target node properties missing 'name'.")
            return

        target_properties = {"name": target_name}

        if target_name is None:
            print(f"Skipping creation of {target_label} due to missing 'name' property.")
            return

        target_query = f"""
            MERGE (t:{target_label} {{ {', '.join([f'{k}: ${k}' for k in target_properties.keys()])} }})
            RETURN t
        """
        session.run(target_query, target_properties)

        rel_query = f"""
           MATCH (s:{source_label} {{name: $source_name}})
           MATCH (t:{target_label} {{name: $target_name}})
           MERGE (s)-[:{rel_type}]->(t)
        """
        session.run(rel_query, {
            "source_name": source_properties["name"],
            "target_name": target_properties["name"]
        })
        print(f"Relationship created: {source_label} -[{rel_type}]-> {target_label}")

    except KeyError as e:
        print(f"KeyError in create_relationship: {e}")
    except Exception as e:
        print(f"Unexpected error in create_relationship: {e}")


def create_relationshipJakob(session, source_label, source_properties, relationship, data):
    try:
        target = relationship.get("target")
        rel_type = relationship.get("type")

        if rel_type == "FOUNDED":
            print("foundet")

        if not target:
            print(f"Skipping relationship with type {rel_type} due to missing target.")
            return

        target_name = data[target]["properties"]["name"]

        if not target_name:
            print(f"Skipping relationship with type {rel_type}: Target node properties missing 'name'.")
            return

        target_properties = {"name": target_name}

        if target_name is None:
            print(f"Skipping creation of {target} due to missing 'name' property.")
            return

        target_query = f"""
            MERGE (t:{target} {{ {', '.join([f'{k}: ${k}' for k in target_properties.keys()])} }})
            RETURN t
        """
        print(target_query)
        session.run(target_query, target_properties)

        rel_query = f"""
           MATCH (s:{source_label} {{name: $source_name}})
           MATCH (t:{target} {{name: $target_name}})
           MERGE (s)-[:{rel_type}]->(t)
        """
        session.run(rel_query, {
            "source_name": source_properties["name"],
            "target_name": target_properties["name"]
        })
        print(f"Relationship created: {source_label} -[{rel_type}]-> {target}")

    except KeyError as e:
        print(f"KeyError in create_relationship: {e}")
    except Exception as e:
        print(f"Unexpected error in create_relationship: {e}")
