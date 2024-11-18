import csv

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





def read_csv(file_path):
  """Reads a CSV file and returns a list of rows.

  Args:
    file_path: The path to the CSV file.

  Returns:
    A list of rows, where each row is a list of values.
  """

  with open(file_path, 'r') as csvfile:
    reader = csv.reader(csvfile)
    data = []
    for row in reader:
      data.append(row)
    return data
