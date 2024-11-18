import neo4j as neo
from neo4j import GraphDatabase
import csv

csv_file = './files/Unicorn_Companies.csv'
neo4j_uri = "bolt://localhost:7687"
username = "neo4j"
password = "neo4j"

def main():
     ##todo


    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS ON (n:Node) ASSERT n.id IS UNIQUE")

        # Load CSV and create nodes and relationships
        with open(csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                session.run(
                    """
                    MERGE (n:Node {id: $id, name: $name})
                    WITH n
                    MATCH (m:Node {id: $related_to})
                    MERGE (n)-[:RELATED_TO]->(m)
                    """,
                    id=int(row['id']),
                    name=row['name'],
                    related_to=int(row['related_to'])
                )
    driver.close()



    #print("Hello, world!")

if __name__ == "__main__":
    main()
