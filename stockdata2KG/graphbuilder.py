import neo4j as neo
from neo4j import GraphDatabase
import csv

## Setup connection to Neo4j
neo4j_uri = "neo4j://localhost:7687"
username = "neo4j"
password = "neo4jtest"

## File Paths
csv_file = './files/Unicorn_Companies.csv'


def buildgraph():
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    with driver.session() as session:

        session.run('CREATE (database:Database {name:"Neo4j"})-[r:SAYSAgain]->(message:Message {name:"Hello World!"}) RETURN database, message, r')

        session.run("MATCH (n) RETURN n")

        # Load CSV and create nodes and relationships
        # with open(csv_file, newline='') as csvfile:
        #     reader = csv.DictReader(csvfile)
        #     for row in reader:
        #         session.run(
        #             """
        #             MERGE (n:Node {id: $id, name: $name})
        #             WITH n
        #             MATCH (m:Node {id: $related_to})
        #             MERGE (n)-[:RELATED_TO]->(m)
        #             """,
        #             id=int(row['id']),
        #             name=row['name'],
        #             related_to=int(row['related_to'])
        #         )
    driver.close()



    #print("Hello, world!")