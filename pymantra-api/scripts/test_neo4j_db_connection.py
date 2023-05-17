import os
from pymantra.database.base import Neo4jBaseConnector


with Neo4jBaseConnector("bolt://neo4j-db:7687", (os.environ.get("NEO4J_USER"), os.environ.get("NEO4J_PASSWORD"))) as cnx:
    if not cnx.active_connection():
        exit -1
