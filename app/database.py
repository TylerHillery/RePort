import duckdb

def get_query_string(file_path: str) -> str: 
    with open("app/data/queries/" + file_path + ".sql", 'r') as file:
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
    
    def crud(self,operation,table,parms):
        # TO DO: Should be better way to abstract this to I don't repeat myself
        # TO DO: Find better way to create initial tables
        if table == 'cash':            
            if operation == "Add":
                self.query(
                    get_query_string("insert_cash_values"), 
                    parms
            )
            if operation == "Delete":
                self.query(
                    get_query_string("delete_cash"), 
                    parms
                )
            if operation == "Update":
                self.query(
                    get_query_string("update_cash"), 
                    parms
                )
        if table == 'holdings':
            # TO DO: Add error handling for invalid values (e.g. 0 shares)           
            if operation == "Add":
                self.query(
                    get_query_string("insert_holdings_values"), 
                    parms
            )
            if operation == "Delete":
                self.query(
                    get_query_string("delete_holding"), 
                    parms
                )
            if operation == "Update":
                self.query(
                    get_query_string("update_holding"), 
                    parms
                )
        return 



