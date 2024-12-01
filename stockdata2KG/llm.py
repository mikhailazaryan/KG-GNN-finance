import google.generativeai as genai

model = genai.GenerativeModel("gemini-pro")  # Choose the desired model
genai.configure(api_key="AIzaSyCArmUNcsj4EX-SjeU0XlF0hMY_Oet4CCI")


def test(article, driver):
     #node_name = findKeyword(article, driver)
     #data = query_graph(driver, node_name)
     data = query_graph(driver, "Munich")
     print("data: " + str(data))
     suggestion = analyze_with_llm(article, data)
     print ("suggestion: " + str(suggestion))
     cyper_code = suggestion_to_cypher(driver, data, suggestion)
     print("cypher code: " + str(cyper_code))
     #extractRelevantNodes(driver)


def findKeyword(article, driver):
    with driver.session() as session:
        query = """MATCH (n) RETURN n"""
        result = session.run(query)
        list = []
        for record in result:
            list.append(dict(record["n"])["name"])

    prompt = f"""
    Read this newspaper article:
    
    {article}
    
    Which single keyword of the following keywords ist most relevant in the article?: 
    
    {list}
    
    Please only list a single word!"""
    print(prompt)
    response = model.generate_content(prompt)
    print("Gemini says: " + response.text)
    response = response.text.split(" ")
    if response in list:
        print("Gemini Keyword is: " + response)
        return response

def query_graph(driver, node_name):
    with driver.session() as session:
        query = """
        MATCH (n {name: $node_name})-[r]-(m)
        RETURN n, type(r) AS relationship_type, m
        """
        result = session.run(query, {"node_name": node_name})
        graph_data = []
        for record in result:
            graph_data.append({
                "node": dict(record["n"]),
                "relationship_type": record["relationship_type"],
                #"relationship_properties": record["relationship_properties"],
                "connected_node": dict(record["m"])
            })
        return graph_data

def analyze_with_llm(news_article, graph_data):
    # Prepare the prompt for the LLM
    prompt = f"""
    Here is the information from a knowledge graph:
    {graph_data}
    
    And here is a news article:
    {news_article}
    
    Identify any discrepancies between the knowledge graph and the news article. 
    Suggest the most important update that need to be made to the knowledge graph.
    
    Please only suggest a single update and start your answer with "Update:", "Add new node:" or "Delete node:"
    """

    # Call the LLM API
    response = model.generate_content(prompt)

    # Extract LLM response
    return response.text

def suggestion_to_cypher(driver, data, suggestion):
    # Prepare the prompt for the LLM
    prompt = f"""
      given this neo4j knowledge graph entry: 

      {data}
      
      and this update request:
      
      {suggestion}
      
      Please write a single cypher query to make this update.
      """

    # Call the LLM API
    response = model.generate_content(prompt)

    # Extract LLM response
    return response.text
