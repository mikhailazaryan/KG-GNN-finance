import json


def initialize_graph(json_path, driver):
    with open(json_path, 'r') as f:
        data = json.load(f)

    print(f"Initializing graph from {json_path}")
    print(data.get("name"))


    with driver.session() as session:
        session.run("MATCH(n) DETACH DELETE n")
        create_nodes_and_relationships(session, data)

def create_nodes_and_relationships(session, data):
    # Create the nodes
    for key, value in data.items():
        label = value["label"]
        for properties in value["nodes"]:
        #properties = value["nodes"][0]

            # Use MERGE to create or match the node
            node_query = f"""
                MERGE (n:{label} {{name: $name}})
                SET n += $properties
                RETURN n
            """
            session.run(node_query, {"name": properties["name"], "properties": properties})

    # Create relationships
    for key, value in data.items():
        source_label = value["label"]
        for source_name in value["nodes"]:
            source_name = source_name["name"]

            for relationship in value.get("relationships", []):
                rel_type = relationship["type"]
                target_key = relationship["target"]
                target_label = data[target_key]["label"]
                #target_name = data[target_key]["nodes"][0]["name"]
                for target_node in data[target_key]["nodes"]:
                    target_name = target_node["name"]  # Extract the target node's name

                    rel_query = f"""
                        MATCH (source:{source_label} {{name: $source_name}})
                        MATCH (target:{target_label} {{name: $target_name}})
                        MERGE (source)-[:{rel_type}]->(target)
                    """
                    session.run(rel_query, {"source_name": source_name, "target_name": target_name})



