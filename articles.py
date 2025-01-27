import json
import configparser
import google.generativeai as genai
import requests
#from newspaper import Article

# Initialize the generative model
model = genai.GenerativeModel("gemini-1.5-pro-latest")
config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

output_file_path = "files/benchmarking_data/real_articles_temp.json"


def scrape_article(url):
    try:
        # Initialize the article object
        article = Article(url)
        # Download and parse the article
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def fetch_news(search_term, max_articles=10):
    """
    Fetch news articles for a given search term from Google RSS feed.

    Args:
        search_term (str): The search term for querying Google News RSS.
        max_articles (int): Maximum number of articles to fetch.

    Returns:
        list: A list of dictionaries, each containing details of a news article.
    """
    search_term = search_term.replace(" ", "+")
    bugfree_sources = "\"The New York Times\",  \"International New York Times\", \"International Herald Tribune\""
    bugfree_sources = bugfree_sources.replace(" ", "+")
    articles = []
    response = requests.get(
        f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={search_term}&fq=source:({bugfree_sources})&sort=relevance&api-key={config['nytimes']['api_key']}")
    data = response.json()['response']['docs']
    # print(data)

    if True:
        print(f"Found {len(data)} articles.")
        for news_item in data[:max_articles]:  # Limit the number of articles
            print(f"Processing article: {news_item['snippet']}")
            full_text = scrape_article(news_item['web_url'])
            summary = preprocess_news(full_text)
            article = {
                "text": summary,
                "source": news_item['source'],
                "date": news_item['pub_date'],
                "benchmarking": {
                    "model update triples": {
                        "unchanged": [],
                        "added": [],
                        "deleted": []
                    },
                    "correct update": None,
                    "wikidata structure": None
                }
            }
            articles.append(article)
    else:
        print(f"No news found for the term: {search_term}")
    return articles


def preprocess_news(full_text):
    """Uses the LLM to condense a news article into one sentence."""
    prompt = f"""
    You are a summarization assistant. Your task is to access the full text of the article {full_text} and then summarize this article from this into a single sentence. Keep the main event and relevant company details. 
    
    """
    result = model.generate_content(prompt, generation_config={"temperature": 0.2})
    return result.text.strip()


def generate_real_articles(companies):
    """
    Build a JSON structure for real articles.

    Args:
        companies (list): List of company names for which to fetch articles.

    Returns:
        dict: A dictionary structured as real articles JSON.
    """
    real_articles = {}

    for company in companies:
        print(f"\nFetching articles for company: {company}")
        articles = fetch_news(company)  # Fetch news articles for the company
        company_data = {company: {}}

        for idx, article in enumerate(articles, 1):
            article_key = f"article_{idx}"
            print(f"Adding article {idx} to {company}'s data.")
            company_data[company][article_key] = article  # Directly assign the article data

        real_articles.update(company_data)
        print(f"Completed processing for company: {company}")
    print("All companies processed. Returning synthetic articles JSON.")
    return real_articles


def save_to_json(data, filename=output_file_path):
    """Saves the generated data to a JSON file."""
    print(f"Saving synthetic articles to {filename}")
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print("Data successfully saved.")
