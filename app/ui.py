from hashlib import md5

import pandas as pd
import streamlit as st

from database import DuckDB, get_query_string

db = DuckDB()

class Sidebar(): 
    def header():
        st.header("Configurations")
    
    def radio():
        input_method = st.radio("Input Method",('File','Manual'))
        return input_method
    
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
    
    def check_box_frac_shares():
        is_frac_shares = st.checkbox("Allow fractional share investing?")
        return is_frac_shares
    
    def check_box_sample_data():
        def add_sample_data():
            if st.session_state.add_sample_data:
                db.query("DELETE FROM cash")
                db.query("DELETE FROM holdings")
                db.query("""
                INSERT INTO 
                    cash 
                SELECT 
                    * 
                FROM
                    read_csv_auto('app/data/example_cash.csv')
                """)        
                db.query("""
                INSERT INTO
                    holdings 
                SELECT 
                    md5(concat(lower(trim(account_name)),lower(trim(ticker)))),
                    * 
                FROM 
                    read_csv_auto('app/data/example_holdings.csv')
                """)
            else:
                db.query("DELETE FROM cash")
                db.query("DELETE FROM holdings")

        add_sample_data = st.checkbox(
            "Add sample data?",
            help="Warning: This will delete all current data!",
            on_change= add_sample_data,
            key="add_sample_data"
        )
        
        return add_sample_data

class CashInput():
    def file():
        uploaded_data = st.file_uploader(
        "Drag and Drop Cash File or Click to Upload", type=".csv", 
        accept_multiple_files=False
        )

        if uploaded_data is not None:
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
        if uploaded_data is not None:
            st.success("Uploaded your file!")
            uploaded_data = uploaded_data

            df = pd.read_csv(uploaded_data) 

            db.query("DELETE FROM holdings")
            db.query("""
            INSERT INTO
                holdings 
            SELECT 
                md5(concat(lower(trim(account_name)),lower(trim(ticker)))),
                * 
            FROM df
            """)
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
            md5((account.strip() + ticker.strip()).lower().encode('utf-8')).hexdigest(),
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
                parms = [(data[1],)]
            if operation == "Update":
                parms = [data[4:] + (data[1],)]
            
            db.crud(operation,'holdings',parms)
        
        return data

class Portfolio():
    def create_tables(rebalance_type, is_frac_shares):
        db.query(get_query_string('create_holdings_table')) 
        db.query(get_query_string('create_cash_table')) 

    def update_tables(table: tuple,df: pd.DataFrame) -> None:
        if table == 'cash':
            db.query("DELETE FROM cash")
            db.query("""
                INSERT INTO 
                    cash 
                SELECT
                    *
                FROM 
                    df
                """)  
        elif table == 'holdings':
            db.query("DELETE FROM holdings")
            db.query("""
            INSERT INTO
                holdings 
            SELECT 
                md5(concat(lower(trim(account_name)),lower(trim(ticker)))),
                * 
            FROM 
                df
            """)
        return
    
    def get_cash_table():
        df = (db.fetch(get_query_string('select_cash')))
        return df

    def get_holdings_table(): 
        return db.fetch(get_query_string('select_holdings'))

    def get_raw_holdings_table():
        return db.fetch("SELECT account_name,ticker,security_name,shares,target_weight,cost,price FROM holdings ORDER BY account_name,ticker")
    
    def get_raw_cash_table():
        return db.fetch("SELECT account_name,cash FROM cash ORDER BY account_name")

    def get_accounts():
        accounts = list(map(lambda _tup: str(_tup[0]), db.fetch(
            "SELECT DISTINCT account_name FROM cash",
            return_df=False
                )))
        return accounts 

    def get_account_cash(account: str) -> float: 
        return db.fetch(f"SELECT cash FROM cash WHERE account_name = '{account}'",return_df=False)[0][0]

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
                holding_id,
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
            for account in accounts:
                Portfolio.dynamic_invest(account)
        return
    
    def get_future_holdings_table(rebalance_type, is_frac_shares):
        Portfolio.create_future_holdings(rebalance_type, is_frac_shares)
        return db.fetch(get_query_string('select_future_holdings'))
    
    def get_account_future_cash(account: str,rebalance_type, is_frac_shares) -> float: 
        df = Portfolio.get_future_holdings_table(rebalance_type, is_frac_shares)
        return db.fetch(f"SELECT max(cash) FROM df WHERE account_name = '{account}'",return_df=False)[0][0]