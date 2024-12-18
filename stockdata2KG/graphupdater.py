import google.generativeai as genai

model = genai.GenerativeModel("gemini-pro")  # Choose the desired model
genai.configure(api_key="AIzaSyCArmUNcsj4EX-SjeU0XlF0hMY_Oet4CCI")

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