import csv

# important questions: are we iteratively adding to the graph or add them all at once? More interesting would be step by step

# so what is the data format? We cannot have it tabular I think, as it will be hard to get

# Chunking: convert large text (string) into several junks



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
