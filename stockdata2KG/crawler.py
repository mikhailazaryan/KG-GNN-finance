import csv
import json

from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities

id_of_company = None
wikidata = None

def crawl_wikidata(search_string_or_id):
  global id_of_company
  id_of_company = wikidata_wbsearchentities(search_string_or_id, 'id')
  global wikidata
  wikidata = wikidata_wbgetentities(id_of_company)

  main_company_node()
  stock_market_index()
  industry()
  founders()

def main_company_node():
  company_dict = {
    "node": wikidata_wbsearchentities(id_of_company, 'label'),
    "label": "company",
    "isin" : extract_value_from_id('P946'),
    "inception" : extract_value_from_id('P571')['time'].split('+')[1].split('-')[0],
  }
  print (company_dict)

def stock_market_index():
  stock_market_index_dict = {
    "stock_market_index" : wikidata_wbsearchentities(extract_value_from_id('P361')['id'], 'label') # only returns top index, not the others
  }
  print(stock_market_index_dict)

def industry():
  industry_dict = {
    "industry" : wikidata_wbsearchentities(extract_value_from_id('P452')['id'], 'label')
  }
  print(industry_dict)

def founders():
  founder_dict = {wikidata_wbsearchentities(extract_value_from_id('P112')['id'], 'label')}
  print(founder_dict)


# important questions: are we iteratively adding to the graph or add them all at once? More interesting would be step by step
# so what is the data format? We cannot have it tabular I think, as it will be hard to get
# Chunking: convert large text (string) into several junks

# What is the essential data that we need:

## Node: The_Company_Name
  # Label: Company
  # Relationships:
    # Part of Stock Market Index
    # Active in Industry
    # Founded by Founders
    # Has Subsidiaries
    # Headquartered in
    # Offers Products/Services
    # todo
# Properties:
    # Stock Ticker / ISIN
    # Founding Date / Inception

## Node: The_Stock_Market_Index
  # Label: Stock Market index
  # Relationships:
    # todo
  # Properties: todo

## Node: The_Industry
  # Label: Industry
  # Relationships:
    # todo
  # Properties:
    # todo

## Node: The_Founders
  # Label: Person
  # Relationships:
    # have founded
  # Properties: todo

## Node: The Manager / Director / CEO
  # Label: Person
  # Relationships:
    # manages the company
  # Properties: todo

## Node: The_Board
  # Label: Person
  # Relationships:
    # part of the board of the company
  # Properties: todo

## Node: The_Subsidiaries
  # Label: Company
  # Relationships: todo
  # Properties: todo

## Headquartered_in
  # Label: City / Country?
  # Relationships: todo
  # Properties: todo

## Product or Service
  # Label: Product
  # Relationship


# Nodes: The entities in the data.
# Labels: Each node can have one or more label that specifies the type of the node.
# Relationships: Connect two nodes. They have a single direction and type.
# Properties: Key-value pair properties can be stored on both nodes and relationships.


# Name of Company
# StockTicker to use as an ID of the company?



def extract_value_from_id(id):
  return wikidata["entities"][id_of_company]["claims"][id][0]["mainsnak"]["datavalue"]["value"]

