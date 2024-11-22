from stockdata2KG.crawler import crawl_wikidata

def main():
     # just input a company, e.g. "Apple Inc" or "Allianz SE"
     crawl_wikidata("Apple Inc")


if __name__ == "__main__":
    main()
