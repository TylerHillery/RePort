import duckdb
    
def get_query_string(file_path: str) -> str: 
    with open(file_path + ".sql", 'r') as file:
        return file.read()

class DuckDB:
    def __init__(self):
        self.database   =":memory:"
        self.connection = duckdb.connect(self.database)

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