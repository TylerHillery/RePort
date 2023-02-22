import streamlit as st

import pandas as pd

from database import DuckDB, get_query_string

db = DuckDB()

class Sidebar(): 
    def header():
        st.header("Configurations")
    
    def select_box():
        rebalance_type = st.selectbox(
            "Select Rebalance Type",
            (
                "Investable Cash Dynamic",
                "Investable Cash Target",
                "Whole Portfolio"
            )
        )
        return rebalance_type
    
    def check_box():
        is_frac_shares = st.checkbox("Allow fractional share investing?")
        return is_frac_shares

    def radio():
        input_method = st.radio("Input Method",('Manual', 'File'))
        return input_method

class CashInput():
    def file():
        uploaded_data = st.file_uploader(
        "Drag and Drop Cash File or Click to Upload", type=".csv", 
        accept_multiple_files=False
        )

        if uploaded_data is None:
            st.info("Using example data. Upload a file above to use your own data!")
            uploaded_data = "app/example_cash.csv"
        else:
            st.success("Uploaded your file!")
            uploaded_data = uploaded_data

        df = pd.read_csv(uploaded_data) 

        db.query("DELETE FROM cash")
        db.query("INSERT INTO cash SELECT * FROM df")
        return None

    def form():
        form  = st.form("cash_input")
        c1, c2, c3  = form.columns((1.5,1.5,1.5))
        operation   = c1.selectbox('Select Operation',('Add','Update','Delete'))
        account     = c2.text_input('Account Name')
        cash        = c3.number_input('Investable Cash ($)',min_value = 0.00)
        submitted   = form.form_submit_button("Submit")

        data = (
            operation,
            account.strip(),
            cash
        )

        if submitted:
            if operation == "Add":
                parms = [data[1:]]
            if operation == "Delete":
                parms = [(data[1],)]
            if operation == "Update":
                parms = [data[:0:-1],]

            db.crud(operation,'cash',parms)

        return data
        

class HoldingsInput():   
    def file():
        uploaded_data = st.file_uploader(
        "Drag and Drop Holdings File or Click to Upload", type=".csv",
        accept_multiple_files=False
        )

        if uploaded_data is None:
            st.info("Using example data. Upload a file above to use your own data!")
            uploaded_data = "app/example_holdings.csv"
        else:
            st.success("Uploaded your file!")
            uploaded_data = uploaded_data

        df = pd.read_csv(uploaded_data) 

        db.query("DELETE FROM holdings")
        db.query("INSERT INTO holdings SELECT * FROM df")
        return None 

    def form():
        form  = st.form("holdings_input")
        row_1 = form.container()
        row_2 = form.container()
        
        with row_1:
            c1, c2, c3  = row_1.columns((1.5,1.5,1.5))
            operation   = c1.selectbox('Select Operation',('Add','Update','Delete'))
            account     = c2.text_input('Account Name')
            ticker      = c3.text_input('Ticker')
        
        with row_2:
            c1, c2, c3, c4  = row_2.columns((1.25,1.25,1.25,1.25))
            shares          = c1.number_input('Shares',min_value = 0.00)
            target          = c2.number_input('Target Weight (%)')
            cost            = c3.number_input(
                                'Cost', 
                                min_value = 0.00, 
                                help = "Total Cost for all shares"
                            )

            price           = c4.number_input(
                                'Price',
                                min_value = 0.00,
                                help = """
                                Current stock price or price you plan on
                                purchasing the stock at
                                """
                            ) 
        
        submitted = form.form_submit_button("Submit")

        data = (
            operation,
            account.strip(),
            ticker.strip(),
            shares,
            target,
            cost,
            price
        )
        
        if submitted:
            if operation == "Add":
                parms = [data[1:]]
            if operation == "Delete":
                parms = [data[1:3]]
            if operation == "Update":
                parms = [data[1:] + data[1:3]]
            
            db.crud(operation,'holdings',parms)
        
        return data

class Portfolio():     
    def create_tables():
        db.query(get_query_string('create_holdings_table')) 
        db.query(get_query_string('create_cash_table')) 
        
    def get_cash_table():
        df = (db.fetch(get_query_string('select_cash')))
        return df

    def get_holdings_table(): 
        return db.fetch(get_query_string('select_holdings'))

    def get_accounts():
        accounts = list(map(lambda _tup: str(_tup[0]), db.fetch(
            "SELECT DISTINCT account_name FROM cash",
            return_df=False
                )))
        return accounts 

    def dynamic_invest(account):

        df = db.fetch(get_query_string('select_future_holdings'))

        cash = db.fetch(
            f"SELECT cash FROM future_cash WHERE account_name = '{account}'",
            return_df=False
        )[0][0]
        
        is_cash_left =  bool(db.fetch(
            f"""
            SELECT 
                * 
            FROM 
                df 
            WHERE
                price <= {cash}
                AND account_name = '{account}'
            """,
            return_df=False
        ))

        while is_cash_left:
            ticker,shares,new_cash,cost = db.fetch(
                f"""
                SELECT
                    ticker,
                    dynamic_shares_to_invest_whole + 1 + shares,
                    cash - price as new_cash,
                    cost + (( dynamic_shares_to_invest_whole + 1)* price) as cost
                FROM 
                    df
                WHERE
                    price <= {cash}
                    AND account_name = '{account}'
                ORDER BY
                    target_diff
                Limit 1
                """,
                return_df=False
            )[0]

            db.query(
                """
                UPDATE future_holdings SET
                    shares = ?,
                    cost = ?
                WHERE
                    account_name    = ?
                AND ticker          = ?
                """,
                [(shares, cost, account, ticker)]
            )

            db.query(
                """
                UPDATE future_cash SET
                    cash = ? 
                WHERE
                    account_name    = ?
                """,
                [(new_cash, account)]
            )
        
            df = db.fetch(get_query_string('select_future_holdings'))

            cash = db.fetch(
                f"SELECT cash FROM future_cash WHERE account_name = '{account}'",
                return_df=False
            )[0][0]
            
            is_cash_left =  bool(db.fetch(
                f"""
                SELECT 
                    * 
                FROM 
                    df 
                WHERE
                    price <= {cash}
                    AND account_name = '{account}'
                """,
                return_df=False
            ))

        return
    
    def create_future_holdings(rebalance_type, is_frac_shares):

        df = db.fetch(get_query_string('select_holdings'))

        db.fetch("DROP TABLE IF EXISTS future_holdings")
        db.fetch("DROP TABLE IF EXISTS future_cash")

        if rebalance_type   == "Investable Cash Dynamic" and is_frac_shares:
            column = 'dynamic_shares_to_invest_frac'
        elif rebalance_type == "Investable Cash Dynamic" and not is_frac_shares:
            column = 'dynamic_shares_to_invest_whole'
        elif rebalance_type   == "Investable Cash Target" and is_frac_shares:
            column = 'target_shares_to_invest_frac'
        elif rebalance_type == "Investable Cash Target" and not is_frac_shares:
            column = 'target_shares_to_invest_whole'
        elif rebalance_type   == "Whole Portfolio" and is_frac_shares:
            column = 'all_shares_to_invest_frac'
        elif rebalance_type == "Whole Portfolio" and not is_frac_shares:
            column = 'all_shares_to_invest_whole'
        else:
            None

        sql = (f"""
        CREATE TABLE future_holdings as (
            SELECT 
                account_name,   
                ticker,         
                security_name,  
                shares + {column} as shares,        
                target_weight,  
                cost + ({column} * price) as cost,           
                price
             FROM df 
            )
       """)

        db.fetch(sql)

        db.fetch(f"""
        CREATE TABLE future_cash as ( 
            SELECT 
                account_name, 
                max(cash) - sum({column} * price) as cash 
             FROM df 
             GROUP BY 1
            )
       """)

        if rebalance_type == "Investable Cash Dynamic" and not is_frac_shares:
            accounts = list(map(lambda _tup: str(_tup[0]), db.fetch(
            "SELECT DISTINCT account_name FROM cash",
            return_df=False
                )))
                
            map(Portfolio.dynamic_invest, accounts)
        return
    
    def get_future_holdings_table(rebalance_type, is_frac_shares):
        Portfolio.create_future_holdings(rebalance_type, is_frac_shares)
        return db.fetch(get_query_string('select_future_holdings'))