import sqlite3
import os

import pandas as pd
    
def get_query_string(file_path: str) -> str: 
    with open(file_path + ".sql", 'r') as file:
        return file.read()

class SQLite:
    def __init__(self, database=":memory:"):
        self.database   = os.path.join(os.path.dirname(__file__),database)
        self.connection = sqlite3.connect(self.database)
        self.cursor     = self.connection.cursor()

    def query(self, sql_statement: str, parameters=None):
        if parameters is None:
            self.cursor.execute(sql_statement)
        else:
            self.cursor.executemany(sql_statement,parameters)
        self.connection.commit()
    
    def fetch(self, sql_statement: str) -> pd.DataFrame:
        return pd.read_sql_query(sql_statement, self.connection)

