import csv

## structure of the unicorn_companies.csv

## Field,Description
## Company,Company name
## Valuation,Company valuation in billions (B) of dollars
## Date Joined,The date in which the company reached $1 billion in valuation
## Industry,Company industry
## City,City the company was founded in
## Country,Country the company was founded in
## Continent,Continent the company was founded in
## Year Founded,Year the company was founded
## Funding,Total amount raised across all funding rounds in billions (B) or millions (M) of dollars
## Select Investors,Top 4 investing firms or individual investors (some have less than 4)

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

# Example usage:
file_path = "files/Unicorn_Companies.csv"
data = read_csv(file_path)
print(data)