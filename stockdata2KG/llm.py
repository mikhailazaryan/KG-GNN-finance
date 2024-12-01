import google.generativeai as genai

def process_article_and_update_graph(article_text, driver):

    genai.configure(api_key="AIzaSyCArmUNcsj4EX-SjeU0XlF0hMY_Oet4CCI")

    model = genai.GenerativeModel("gemini-pro")  # Choose the desired model
    response = model.generate_content("What is the meaning of life?")
    print(response.text)
    return