import google.generativeai as genai
import configparser
import json
import typing_extensions as typing



model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Choose the desired model

config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])


#todo next steps:
# (1) test with a lot more synthetically created articles
# (2) start crawling real articles
# (3) preprocessing real articles and trying them on the functions


def get_articles(company):
    new_articles = {}

    example_articles = {
        "article_1": "Allianz SE moved their headquarter from Munich to Berlin",
        "article_2": "Allianz SE bought Ergo Group",
        "article_3": "Allianz SE is no longer active in the insurance industry",
        "article_4": "Allianz SE sold PIMCO",
        "article_5": "Allianz SE is not listed in EURO STOXX 50 anymore",
        "article_6": "Allianz SE bought SportGear AG headquartered in Cologne",
        "article_7": "Allianz SE bought Jamo Data GmbH headquartered in Jena",
        "article_8": "Allianz SE moved their headquarter from Berlin to Frankfurt",
        "article_9": "Woodworking is a new business field of Allianz SE",
        "article_10": "Westbank was renamed to Westbank Privatbank",
        "article_11": "Allianz SE was renamed to Algorithm GmbH"
    }

    prompt = f"""
    Your task is to come up with 9 short articles that are similar to the ones provided for the companie Allianz AG, but now for the company: {company}.
    The articles should be about the Companies, their industry fields, change of Managers, Cities, Countries or Stock Market Indices.
    
    Be creative and unusual!
    
    Example Articles: {example_articles}
    Company for the articles: {company}
            """


    class ResponseSchema(typing.TypedDict):
        article_1 : str
        article_2 : str
        article_3 : str
        article_4 : str
        article_5 : str
        article_6 : str
        article_7 : str
        article_8 : str
        article_9 : str

    result = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=list[ResponseSchema],
        ),
    )
    result = result.text
    articles = json.loads(result)

    for article in articles:
        print(str(article) + "\n")

    return example_articles