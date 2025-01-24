import configparser
import json
from datetime import datetime, timezone
import colorama
from colorama import init, Fore, Style
from neo4j import GraphDatabase

from articles import preprocess_news, generate_real_articles, save_to_json
from graphbuilder import reset_graph, build_graph_from_root
from graphupdater import update_neo4j_graph
from wikidata.wikidataCache import WikidataCache

# Initialize colorama for colored output
colorama.init()

# Configuration and constants
CONFIG_FILE = 'config.ini'
BENCHMARK_FILE = "files/benchmarking_data/synthetic_articles_benchmarked.json"  # Consistent file path
REAL_ARTICLES_BENCHMARK_FILE = "files/benchmarking_data/real_articles_benchmarked.json"


def connect_to_neo4j(config_file=CONFIG_FILE):
    """Establishes a connection to the Neo4j database."""
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        driver = GraphDatabase.driver(
            config['neo4j']['uri'],
            auth=(config['neo4j']['username'], config['neo4j']['password'])
        )
        driver.verify_connectivity()
        print("Connection successful!")
        return driver
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def build_knowledge_graph(driver, companies, date_range, included_nodes, search_depth):
    """Builds the initial knowledge graph in Neo4j."""
    reset_graph(driver)
    print("Resetting graph.")

    for company_name in companies:
        print(Fore.GREEN + f"\n--- Started building graph for {company_name} ---\n" + Style.RESET_ALL)
        build_graph_from_root(company_name, "Company", date_range, included_nodes, search_depth,
                              driver)
        print(Fore.GREEN + f"\n--- Finished building graph for {company_name} ---\n" + Style.RESET_ALL)

    print(
        f"\n--- Successfully finished building neo4j graph for companies {companies} with a depth of {search_depth} ---\n")
    WikidataCache.strip_cache()
    WikidataCache.print_current_stats()


def update_knowledge_graph(driver, companies, included_nodes, benchmark_mode=False,
                           filepath=BENCHMARK_FILE):
    """Updates the knowledge graph based on articles in a JSON file."""

    print(Fore.LIGHTMAGENTA_EX + f"\n--- Started updating existing neo4j graph ---\n" + Style.RESET_ALL)

    try:
        with open(filepath, 'r+', encoding='utf-8') as f:
            articles_json = json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"Error: File not found: {filepath}" + Style.RESET_ALL)
        return

    for company, articles in articles_json.items():
        if company in companies:
            print("---")
            for article_key, article_data in articles.items():
                try:
                    # Check if already benchmarked
                    with open(filepath, 'r', encoding='utf-8') as z:
                        articles_benchmarked_json = json.load(z)
                        if articles_benchmarked_json[company][article_key].get("benchmarking", {}).get(
                                "correct update") is not None:
                            print(
                                f"Skipping {company}, {article_key} because it seems to have already been benchmarked")
                            continue  # Skip to the next article

                    print("---")
                    print(f"Company: {company}, Article Nr: {article_key}, Article Text: {article_data['text']}")
                    added, deleted, unchanged = update_neo4j_graph(article_data['text'], companies, included_nodes,
                                                                   included_nodes, driver=driver)

                    if benchmark_mode:
                        benchmark_update(filepath, company, article_key, articles_json, added, deleted, unchanged)

                except KeyError as e:
                    raise KeyError(f"Error: Key not found in article data: {e}")

    print(Fore.LIGHTMAGENTA_EX + f"\n--- Finished updating existing neo4j graph ---\n" + Style.RESET_ALL)


def benchmark_update(filepath, company, article_key, articles_json, added, deleted, unchanged):
    """Handles the benchmarking logic for a single article update."""

    articles_json[company][article_key].setdefault("benchmarking", {})["model update triples"] = {
        "unchanged": unchanged, "added": added, "deleted": deleted
    }

    for question in ["correct update", "wikidata structure"]:
        while True:
            user_input = input(f"Is the {question} for {company} - {article_key} correct? [y/n]: ")
            if user_input.lower() in ('y', 'n'):
                articles_json[company][article_key]["benchmarking"][question] = user_input.lower() == 'y'
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    with open(filepath, 'w', encoding='utf-8') as f:  # Save after each article in benchmark mode
        json.dump(articles_json, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved updates for '{company} - {article_key}' to '{filepath}'")
    print("---")


def calculate_benchmark_statistics(filepath: str) -> dict:
    """
    Calculates comprehensive benchmark statistics from a JSON file containing article data.

    Args:
        filepath: Path to the JSON file containing benchmark data

    Returns:
        Dictionary containing various statistics including success rates and counts

    """
    stats = {
        'total_articles': 0,
        'correct_updates': 0,
        'incorrect_updates': 0,
        'correct_structure': 0,
        'incorrect_structure': 0,
        'update_success_rate': 0.0,
        'structure_success_rate': 0.0,
        'companies_analyzed': set(),
        'articles_per_company': {},
        'success_by_company': {}
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            articles_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: Benchmark file not found: {filepath}")
        return stats

    # Process each article
    for company, articles in articles_json.items():
        stats['companies_analyzed'].add(company)
        company_stats = {
            'total': 0,
            'correct_updates': 0,
            'correct_structure': 0
        }

        for article_key, article_data in articles.items():
            stats['total_articles'] += 1
            company_stats['total'] += 1

            benchmarking = article_data.get("benchmarking", {})

            # Update statistics
            if benchmarking.get("correct update") is True:
                stats['correct_updates'] += 1
                company_stats['correct_updates'] += 1
            elif benchmarking.get("correct update") is False:
                stats['incorrect_updates'] += 1

            # Structure statistics
            if benchmarking.get("wikidata structure") is True:
                stats['correct_structure'] += 1
                company_stats['correct_structure'] += 1
            elif benchmarking.get("wikidata structure") is False:
                stats['incorrect_structure'] += 1

        # Store company-specific stats
        stats['articles_per_company'][company] = company_stats['total']
        if company_stats['total'] > 0:
            stats['success_by_company'][company] = {
                'update_rate': (company_stats['correct_updates'] / company_stats['total']) * 100,
                'structure_rate': (company_stats['correct_structure'] / company_stats['total']) * 100
            }

    # Calculate success rates
    if stats['total_articles'] > 0:
        stats['update_success_rate'] = (stats['correct_updates'] / stats['total_articles']) * 100
        stats['structure_success_rate'] = (stats['correct_structure'] / stats['total_articles']) * 100

    # Print detailed statistics
    print("\n=== Benchmark Statistics ===")
    print(f"\nOverall Metrics:")
    print(f"Total Articles Analyzed: {stats['total_articles']}")
    print(f"Number of Companies: {len(stats['companies_analyzed'])}")
    print(f"\nSuccess Rates:")
    print(f"Update Success Rate: {stats['update_success_rate']:.2f}%")
    print(f"Structure Success Rate: {stats['structure_success_rate']:.2f}%")

    print(f"\nDetailed Counts:")
    print(f"Correct Updates: {stats['correct_updates']}")
    print(f"Incorrect Updates: {stats['incorrect_updates']}")
    print(f"Correct Structure: {stats['correct_structure']}")
    print(f"Incorrect Structure: {stats['incorrect_structure']}")

    print("\nPer-Company Statistics:")
    for company in stats['companies_analyzed']:
        print(f"\n{company}:")
        print(f"  Articles: {stats['articles_per_company'][company]}")
        if company in stats['success_by_company']:
            print(f"  Update Success Rate: {stats['success_by_company'][company]['update_rate']:.2f}%")
            print(f"  Structure Success Rate: {stats['success_by_company'][company]['structure_rate']:.2f}%")

    return stats


def main():
    driver = connect_to_neo4j()
    if not driver:
        return  # Exit if connection failed

    # Configuration
    build_graph = True
    update_graph = True
    benchmark = True
    benchmark_stats = True

    companies = ["Adidas AG", "Airbus SE", "Allianz SE", "BASF SE", "Beiersdorf AG"]
    DAX_companies = ["Adidas AG", "Airbus SE", "Allianz SE", "BASF SE", "Bayer AG", "Beiersdorf AG",
                     "Bayerische Motoren Werke AG", "Brenntag SE", "Commerzbank AG", "Continental AG", "Covestro AG",
                     "Daimler Truck Holding AG", "Deutsche Bank AG", "Deutsche Börse AG", "Deutsche Post AG",
                     "Deutsche Telekom AG", "E.ON SE", "Fresenius SE & Co. KGaA", "Hannover Rück SE",
                     "Heidelbergcement AG", "Henkel AG & Co. KGaA", "Infineon Technologies AG", "Mercedes-Benz",
                     "Merck KGaA", "MTU Aero Engines AG", "Munich RE AG", "Porsche AG",
                     "Porsche Automobil Holding SE", "QIAGEN N.V.", "Rheinmetall AG", "RWE AG", "SAP SE",
                     "Sartorius AG", "Siemens AG", "Siemens Energy AG", "Siemens Healthineers AG", "Symrise AG",
                     "Volkswagen AG", "Vonovia SE", "Zalando SE"]

    date_range = (datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2024, 12, 31, tzinfo=timezone.utc))

    included_nodes = ["Company", "Industry_Field", "Manager", "Founder", "Board_Member", "City", "Country",
                      "Product_or_Service", "Employer", "StockMarketIndex"]
    search_depth = 1

    if build_graph:
        build_knowledge_graph(driver, companies, date_range, included_nodes, search_depth)

    filepath = filepath = "files/benchmarking_data/synthetic_articles_benchmarked.json"

    if update_graph:
        update_knowledge_graph(driver, companies, included_nodes, benchmark_mode=benchmark, filepath=filepath)

    if benchmark_stats:
        calculate_benchmark_statistics(filepath=filepath)


if __name__ == "__main__":
    main()
