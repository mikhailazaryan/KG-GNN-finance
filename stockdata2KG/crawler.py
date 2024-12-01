# from stockdata2KG import wikidata
# from stockdata2KG.wikidata import wikidata_wbsearchentities, wikidata_wbgetentities
# from neo4j import GraphDatabase
#
# def crawl_wikidata(search_string_or_id):
#   id_of_company = wikidata_wbsearchentities(search_string_or_id, 'id')
#   return id_of_company, wikidata_wbgetentities(id_of_company)
#
#
#   # main_company_node()
#   # founders()
#   #
#   # list_of_dicts = []
#   # list_of_querries = [('stock_market_index', 'P361'),
#   #         ('industry', 'P452')]
#   #
#   # for tupple in list_of_querries:
#   #   list_of_dicts.append(create_dict(tupple[0], tupple[1]))
#
#
#
# ## Node: The_Company_Name
#   # Label: Company
#   # Relationships:
#     # Part of Stock Market Index
#     # Active in Industry
#     # Founded by Founders
#     # Has Subsidiaries
#     # Headquartered in
#     # Offers Products/Services
#     # todo
# # Properties:
#     # Stock Ticker / ISIN
#     # Founding Date / Inception
#
# def main_company_node():
#   company_dict = {
#     "node": wikidata_wbsearchentities(id_of_company, 'label'),
#     "label": "company",
#     "isin" : extract_value_from_id('P946'),
#     "inception" : extract_value_from_id('P571')['time'].split('+')[1].split('-')[0],
#   }
#   return company_dict
#
# def stock_market_index():
#   stock_market_index_dict = {
#     "stock_market_index" : wikidata_wbsearchentities(extract_value_from_id('P361')['id'], 'label') # only returns top index, not the others
#   }
#   print(stock_market_index_dict)
#
# def industry():
#   industry_dict = {
#     "industry" : wikidata_wbsearchentities(extract_value_from_id('P452')['id'], 'label')
#   }
#   print(industry_dict)
#
#
# def founders():
#   founder_dict = {wikidata_wbsearchentities(extract_value_from_id('P112')['id'], 'label')}
#   print(founder_dict)
#
#
# def create_dict(dict_name, id):
#   dict_name = {
#     dict_name : wikidata_wbsearchentities(extract_value_from_id(id)['id'], 'label') # only returns top index, not the others
#   }
#   print(dict_name)
#   return dict_name
#
#
#
#
# # important questions: are we iteratively adding to the graph or add them all at once? More interesting would be step by step
# # so what is the data format? We cannot have it tabular I think, as it will be hard to get
# # Chunking: convert large text (string) into several junks
#
# # What is the essential data that we need:
#
# ## Node: The_Company_Name
#   # Label: Company
#   # Relationships:
#     # Part of Stock Market Index
#     # Active in Industry
#     # Founded by Founders
#     # Has Subsidiaries
#     # Headquartered in
#     # Offers Products/Services
#     # todo
# # Properties:
#     # Stock Ticker / ISIN
#     # Founding Date / Inception
#
# ## Node: The_Stock_Market_Index
#   # Label: Stock Market index
#   # Relationships:
#     # todo
#   # Properties: todo
#
# ## Node: The_Industry
#   # Label: Industry
#   # Relationships:
#     # todo
#   # Properties:
#     # todo
#
# ## Node: The_Founders
#   # Label: Person
#   # Relationships:
#     # have founded
#   # Properties: todo
#
# ## Node: The Manager / Director / CEO
#   # Label: Person
#   # Relationships:
#     # manages the company
#   # Properties: todo
#
# ## Node: The_Board
#   # Label: Person
#   # Relationships:
#     # part of the board of the company
#   # Properties: todo
#
# ## Node: The_Subsidiaries
#   # Label: Company
#   # Relationships: todo
#   # Properties: todo
#
# ## Headquartered_in
#   # Label: City / Country?
#   # Relationships: todo
#   # Properties: todo
#
# ## Product or Service
#   # Label: Product
#   # Relationship
#
#
# # Nodes: The entities in the data.
# # Labels: Each node can have one or more label that specifies the type of the node.
# # Relationships: Connect two nodes. They have a single direction and type.
# # Properties: Key-value pair properties can be stored on both nodes and relationships.
#
#
# # Name of Company
# # StockTicker to use as an ID of the company?
#
#
#
# def extract_value_from_id(id):
#   return wikidata["entities"][id_of_company]["claims"][id][0]["mainsnak"]["datavalue"]["value"]
#
#
#
#
# # def founders():
# #     founders_list = []
# #     values = list(extract_value_from_id('P112'))
# #     for i, value in enumerate(values):
# #       founder_info = wikidata_wbsearchentities(value, 'label')
# #       founders_list.append({"founder_" + str(i + 1): founder_info})
# #
# #     founders_dict = {}
# #     for founder in founders_list:
# #       founders_dict.update(founder)
# #     print(founders_dict)
#
# # def extract_value_from_id(id):
# #   entry_count = len(wikidata["entities"][id_of_company]["claims"][id])
# #   #print(str(id) + " = count: "+ str(entry_count))
# #   list = []
# #   for i in range(entry_count):
# #     list.append(wikidata["entities"][id_of_company]["claims"][id][i]["mainsnak"]["datavalue"]["value"])
# #   #print(list)
# #   if len(list) > 1:
# #     return list
# #   else:
# #     return list[0]
# #   #return wikidata["entities"][id_of_company]["claims"][id][0]["mainsnak"]["datavalue"]["value"]
#
#
#
#
