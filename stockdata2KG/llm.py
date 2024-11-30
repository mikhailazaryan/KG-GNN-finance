# from py2neo import Graph
# import openai
# import spacy
#
# # Connect to the Neo4j database
# def connect_to_neo4j(uri: str, user: str, password: str) -> Graph:
#     graph = Graph(uri, auth=(user, password))
#     return graph
#
# def get_entity_from_graph(graph: Graph, entity_name: str):
#     # Query to find a node matching a given name (e.g., article or person)
#     query = f"MATCH (n) WHERE n.name = '{entity_name}' RETURN n"
#     result = graph.run(query)
#     return result.data()
#
# # Load spacy model
# nlp = spacy.load("en_core_web_sm")
#
#
# def extract_entities_from_text(text: str):
#     doc = nlp(text)
#     entities = {}
#
#     for ent in doc.ents:
#         entities[ent.label_] = entities.get(ent.label_, []) + [ent.text]
#
#     return entities
#
#
# openai.api_key = "" ##todo neuer key
#
# def extract_entities_using_gpt(text: str):
#     response = openai.Completion.create(
#         model="gpt-4",
#         prompt=f"Extract key entities from this article:\n\n{text}",
#         max_tokens=500
#     )
#
#     return response.choices[0].text.strip()
#
#
#
# def process_article_and_update_graph(graph: Graph, article_text: str):
#     # Step 1: Parse the news article
#     entities_from_article = extract_entities_from_text(article_text)
#
#     # Step 2: Retrieve relevant entities from Neo4j
#     graph_entities = get_entity_from_graph(graph, "Entity")
#
#     # Step 3: Compare and find new entities
#     new_entities = compare_with_graph(entities_from_article, graph_entities)
#
#     # Step 4: Update Neo4j with new entities
#     if new_entities:
#         update_graph_with_new_entities(graph, new_entities)
#         print(f"Added new entities: {new_entities}")
#     else:
#         print("No new entities to add.")
#
# def update_graph_with_new_entities(graph: Graph, new_entities: list):
#     for entity in new_entities:
#         # Add new nodes (assuming nodes have a "name" property)
#         query = f"CREATE (n:Entity {{name: '{entity}'}})"
#         graph.run(query)
#
#
#
# def compare_with_graph(entities_from_article, graph_entities):
#     ###Compare the extracted entities from the article with the entities already in the Neo4j knowledge graph.
#
#     new_entities = []
#
#     # Check for missing entities
#     for label, entity_list in entities_from_article.items():
#         for entity in entity_list:
#             if not any(entity == graph_entity['n']['name'] for graph_entity in graph_entities):
#                 new_entities.append(entity)
#
#     return new_entities
#
#
