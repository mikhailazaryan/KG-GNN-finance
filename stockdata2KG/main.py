import neo4j as neo
from neo4j import GraphDatabase
import csv
from stockdata2KG.graphbuilder import buildgraph



def main():
     buildgraph()


if __name__ == "__main__":
    main()
