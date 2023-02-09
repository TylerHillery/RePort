import sqlite3
import os

import duckdb
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

class DuckEngine:
    def __init__(self, attach_db=None):
        self.database   =":memory:"
        self.connection = duckdb.connect(self.database)
        self.connection.execute(f"""
        INSTALL sqlite;
        LOAD    sqlite;
        CALL sqlite_attach("{os.path.join(os.path.dirname(__file__),attach_db)}");
        """)

    def query(self, sql_statement: str, parameters=None):
        if parameters is None:
            self.connection.execute(sql_statement)
        else:
            self.connection.executemany(sql_statement,parameters)
        self.connection.commit()
    
    def fetch(self, sql_statement: str, return_df=True):
        if return_df:
            return self.connection.execute(sql_statement).df()
        else:
            return self.connection.execute(sql_statement).fetchall()