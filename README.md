# Graph Builder and Updater for publicly listed Companies

This project builds and dynamically updates a knowledge graph from Wikidata, incorporating information from news articles provided by The New York Times API. The project utilizes Neo4j as the graph database.

## Features

* **Knowledge Graph Construction:**  Builds a knowledge graph from Wikidata, starting with a list of seed companies and expanding outwards based on specified relationships and depth.
* **Dynamic Updates:**  Continuously updates the knowledge graph with new information extracted from news articles.
* **Configurable:**  Allows customization of the knowledge graph structure, including entity types, relationship depth, and date range.
* **Efficient Caching:**  Implements a caching mechanism to reduce redundant Wikidata queries.
* **Demo Graph:**  Provides an option to build a smaller demo graph for testing and experimentation.

## Requirements

* Python 3.7+
* Neo4j (including a running Neo4j instance)
* A selection of Libraries (install via `pip install -r requirements.txt`):
    * neo4j~=5.0
    * colorama
    *configparser
    *google-generativeai
    *requests


## Installation

1. Clone the repository: `git clone <repository_url>`
2. Navigate to the project directory: `cd <project_directory>`
3. Install the required libraries: `pip install -r requirements.txt`
4. Configure the Neo4j connection: Update the `config.ini` file with your Neo4j URI, username, and password.  An example `config.ini` file is provided.

## Configuration

The project is configured using the `config.ini` file:

```ini
[neo4j]
uri = neo4j://localhost:7687
username = neo4j
password = your neo4j password

[gemini]
api_key = your Gemini api key

[nytimes]
api_key = your NYTimes api key
