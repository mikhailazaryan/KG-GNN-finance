import configparser
import json
from datetime import datetime, timezone
from neo4j import GraphDatabase
from colorama import init, Fore, Style

from articles import preprocess_news
from graphbuilder import build_graph_from_initial_node, reset_graph
from graphupdater import update_neo4j_graph
from wikidata.wikidataCache import WikidataCache


def main():
    init()  # for colorama

    ## Setup connection to Neo4j
    config = configparser.ConfigParser()
    config.read('config.ini')
    neo4j_uri = config['neo4j']['uri']
    username = config['neo4j']['username']
    password = config['neo4j']['password']
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))

    try:
        driver.verify_connectivity()
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")

    build_graph_bool = True
    update_graph_bool = False
    benchmark_bool = False

    # this builds the initial graph from wikidata
    companies_to_include_in_graph = ["MTU Aero Engines AG"]
    companies_to_include_in_graph = ["Daimler Truck Holding AG"]
    DAX_companies = ["Adidas AG", "Airbus SE", "Allianz SE", "BASF SE", "Bayer AG", "Beiersdorf AG",
                     "Bayerische Motoren Werke AG", "Brenntag SE", "Commerzbank AG", "Continental AG", "Covestro AG",
                     "Daimler Truck Holding AG", "Deutsche Bank AG", "Deutsche Börse AG", "Deutsche Post AG",
                     "Deutsche Telekom AG", "E.ON SE", "Fresenius SE & Co. KGaA", "Hannover Rück SE",
                     "Heidelbergcement AG", "Henkel AG & Co. KGaA", "Infineon Technologies AG",
                     "Mercedes-Benz", "Merck KGaA", "MTU Aero Engines AG",
                     "Münchener Rückversicherungs-Gesellschaft AG", "Dr. Ing. h.c. F. Porsche AG",
                     "Porsche Automobil Holding SE", "QIAGEN N.V.", "Rheinmetall AG", "RWE AG", "SAP SE",
                     "Sartorius AG", "Siemens AG", "Siemens Energy AG", "Siemens Healthineers AG", "Symrise AG",
                     "Volkswagen AG", "Vonovia SE", "Zalando SE"]

    #companies_to_include_in_graph = DAX_companies

    date_from = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    date_until = datetime(2024, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
    nodes_to_include = ["Company", "Industry_Field", "Manager", "Founder", "Board_Member", "City", "Country",
                        "Product_or_Service", "Employer", "StockMarketIndex"]
    search_depth = 1

    if build_graph_bool:
        reset_graph(driver)
        for company_name in companies_to_include_in_graph:
            print(Fore.GREEN + f"\n---Started building graph for {company_name}---\n" + Style.RESET_ALL)
            build_graph_from_initial_node(company_name, "Company", date_from, date_until, nodes_to_include,
                                          search_depth, driver)
            print(Fore.GREEN + f"\n--- Finished building graph for {company_name}---\n" + Style.RESET_ALL)

            # reduce unuseful cache information in 30% of the time,

        print(
            f"\n--- Successfully finished building neo4j graph for companies {companies_to_include_in_graph} with a depth of {search_depth} ---\n")

        print("---")
        WikidataCache.strip_cache()
        WikidataCache.print_current_stats()
        print("---")

    if update_graph_bool:
        '''
        If update_graph_bool == True, then 
            (1) opens filepath = "files/benchmarking_data/synthetic_articles.json" and loads articles
            (2) updates KG according to articles
            (3) saves updates into variables added, deleted and unchanged.
        '''

        print(Fore.LIGHTMAGENTA_EX + f"\n--- Stated updating existing neo4j graph ---\n" + Style.RESET_ALL)

        filepath = "files/benchmarking_data/synthetic_articles.json"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                synthetic_articles_json = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            return

        for company, articles in synthetic_articles_json.items():
            if company in companies_to_include_in_graph:
                for article_key, article_data in articles.items():
                    try:
                        print("---")
                        print(f"Company: {company}, Article Nr: {article_key}, Article Text: {article_data['text']}")
                        added, deleted, unchanged = update_neo4j_graph(article_data['text'],
                                                                       companies_to_include_in_graph,
                                                                       nodes_to_include, date_from,
                                                                       date_until, nodes_to_include,
                                                                       search_depth_new_nodes=1,
                                                                       search_depth_for_changes=search_depth,
                                                                       driver=driver)

                        if benchmark_bool:
                            '''
                            If benchmark_bool == True, then 
                                (1) saves the updates (addd, deleted, unchanged) into synthetic_articles_benchmarked.json
                                (2) asks for keyboard input whether the updates were correct and adhered to the wikidata structure
                                (3) also saves these infos into synthetic_articles_benchmarked.json
                            '''
                            synthetic_articles_json[company][article_key]["benchmarking"]["model update triples"]["unchanged"] = unchanged
                            synthetic_articles_json[company][article_key]["benchmarking"]["model update triples"]["added"] = added
                            synthetic_articles_json[company][article_key]["benchmarking"]["model update triples"]["deleted"] = deleted

                            while True:  # Loop until valid input is received
                                user_input = input(f"Is the update for {company} - {article_key} correct? [y/n]: ")
                                if user_input.lower() == 'y':
                                    synthetic_articles_json[company][article_key]["correct update"] = True
                                    break
                                elif user_input.lower() == 'n':
                                    synthetic_articles_json[company][article_key]["correct update"] = False
                                    break
                                else:
                                    print("Invalid input. Please enter 'y' or 'n'.")

                            while True:  # Loop until valid input is received
                                user_input = input(
                                    f"Is the update in accordance with the wikidata structure for {company} - {article_key} correct? [y/n]: ")
                                if user_input.lower() == 'y':
                                    synthetic_articles_json[company][article_key]["wikidata structure"] = True
                                    break
                                elif user_input.lower() == 'n':
                                    synthetic_articles_json[company][article_key]["wikidata structure"] = False
                                    break
                                else:
                                    print("Invalid input. Please enter 'y' or 'n'.")

                            print(synthetic_articles_json[company][article_key])


                    except KeyError as e:
                        print(f"Error: Key not found in article synthetic_articles_json: {e}")

                    filepath = "files/benchmarking_data/synthetic_articles_benchmarked.json"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(synthetic_articles_json, f, indent=4, ensure_ascii=False)
                        print(f"successfully saved '{synthetic_articles_json[company][article_key]}' to '{filepath}'")
                    print("---")

                print(Fore.LIGHTMAGENTA_EX + f"\n--- Finished updating existing neo4j graph ---\n" + Style.RESET_ALL)

    #news_article = preprocess_news("""Germany’s DAX 40 has a new female CEO: Daimler Truck appoints Karin Radstrom as next head in rare move Karin Radstrom will take up the role next month with a term that runs through January 2029. Daimler Truck Holding AG named Karin Radstrom as its next chief executive officer in a rare appointment of a woman at the head of one of Germany’s top listed companies. She will take up the role next month with a term that runs through January 2029, the company said in a statement on Wednesday. The 45-year old succeeds Martin Daum, who will remain a management board member through the end of this year “to support a smooth handover,” Daimler Truck said. Radstrom will become just the second female CEO of a DAX 40 firm, joining Belen Garijo, the head of pharmaceutical giant Merck KGaA. While Germany has an international reputation for being progressive on gender parity, the country has one of the largest male-female pay gaps in Europe. Radstrom, a former elite rower who competed internationally for her native Sweden, joined the Daimler Truck board in 2021 and has since been responsible for Mercedes-Benz Trucks, where she’s been credited with improving customer service. During Radstrom’s tenure, Mercedes-Benz Trucks saw its profit margins rise, even as it invested heavily in the transition to zero-emission trucks. The company is betting on both hydrogen and battery-electric models as the eventual alternatives to combustion engines. “Within a short period of time, the trained engineer has successfully reshaped the segment profitability and advanced its transformation toward sustainability,” the company said. She introduced a range of new battery-electric trucks, according to the statement. Radstrom rose to prominence at Scania CV AB, Daimler Truck’s Swedish rival. Insiders often point to her popularity among employees, her consensual management style and her focus on the shift to zero-emission logistics. Her appointment comes at a turbulent time for Germany’s industrial sector. Rising interest rates and higher energy prices since Russia’s invasion of Ukraine are squeezing capital investment budgets, making it harder to invest in new assets like trucks. A worsening shortage of skilled engineers — a result of a demographic crisis that’s developed over decades — is also increasing the cost of producing in Germany.""")
    #print(news_article)

    news_article = """Daimler Truck Holding AG appointed Karin Radstrom as its new CEO, succeeding Martin Daum, making her the second female CEO of a DAX 40 company."""
    print(Fore.LIGHTMAGENTA_EX + f"\n--- Stated updating existing neo4j graph ---\n" + Style.RESET_ALL)

    added, deleted, unchanged = update_neo4j_graph(news_article,
                                                   companies_to_include_in_graph,
                                                   nodes_to_include, date_from,
                                                   date_until, nodes_to_include,
                                                   search_depth_new_nodes=1,
                                                   search_depth_for_changes=search_depth,
                                                   driver=driver)

    print(Fore.LIGHTMAGENTA_EX + f"\n--- Finished updating existing neo4j graph ---\n" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
