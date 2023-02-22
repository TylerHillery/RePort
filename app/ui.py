import streamlit as st

from database import SQLite, DuckEngine, get_query_string

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)
duck_engine = DuckEngine(PORTFOLIO_DB)

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

class CashInput():
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
        db.query(get_query_string(QUERIES_DIR + 'create_cash_table')) 
        if submitted:
            if operation == "Add":
            # TO DO: Add error handling for invalid values (e.g. 0 shares)
                db.query(
                    get_query_string(QUERIES_DIR + "insert_cash_values"), 
                    [data[1:]]
                )
            if operation == "Delete":
                db.query(
                    get_query_string(QUERIES_DIR + "delete_cash"), 
                    [(data[1],)]
                )
            if operation == "Update":
                db.query(
                    get_query_string(QUERIES_DIR + "update_cash"), 
                    [data[:0:-1],]
                )
        return data
        

class HoldingsInput():    
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
        db.query(get_query_string(QUERIES_DIR + 'create_holdings_table')) 
        if submitted:
            if operation == "Add":
            # TO DO: Add error handling for invalid values (e.g. 0 shares)
                db.query(
                    get_query_string(QUERIES_DIR + "insert_holdings_values"), 
                    [data[1:]]
                )
            if operation == "Delete":
                db.query(
                    get_query_string(QUERIES_DIR + "delete_holding"), 
                    [data[1:3]]
                )
            if operation == "Update":
                db.query(
                    get_query_string(QUERIES_DIR + "update_holding"), 
                    [data[1:] + data[1:3]]
                )
        return data

class Portfolio():     
    def header():
        st.markdown("#### **Portfolio**")
    def cash():
        cash_columns = {
        "account_name": "Account",
        "cash": "Investable Cash ($)",
        }
        df = (db.fetch(get_query_string(QUERIES_DIR + 'select_cash'))
                .loc[:,list(cash_columns.keys())])
        return df

    def holdings():
        return duck_engine.fetch(get_query_string(QUERIES_DIR + 'select_holdings'))

    def future_holdings():
        return duck_engine.fetch(get_query_string(QUERIES_DIR + 'select_future_holdings'))

    def dynamic_invest(account):

        df = Portfolio.future_holdings()

        cash = duck_engine.fetch(
            f"SELECT cash FROM future_cash WHERE account_name = '{account}'",
            return_df=False
        )[0][0]
        
        is_cash_left =  bool(duck_engine.fetch(
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
            ticker,shares,new_cash,cost = duck_engine.fetch(
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

            duck_engine.query(
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

            duck_engine.query(
                """
                UPDATE future_cash SET
                    cash = ? 
                WHERE
                    account_name    = ?
                """,
                [(new_cash, account)]
            )
        
            df = Portfolio.future_holdings()

            cash = duck_engine.fetch(
                f"SELECT cash FROM future_cash WHERE account_name = '{account}'",
                return_df=False
            )[0][0]
            
            is_cash_left =  bool(duck_engine.fetch(
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
        df = duck_engine.fetch(get_query_string(QUERIES_DIR + 'select_holdings'))

        duck_engine.fetch("DROP TABLE IF EXISTS future_holdings")
        duck_engine.fetch("DROP TABLE IF EXISTS future_cash")

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

        duck_engine.fetch(sql)

        duck_engine.fetch(f"""
        CREATE TABLE future_cash as ( 
            SELECT 
                account_name, 
                max(cash) - sum({column} * price) as cash 
             FROM df 
             GROUP BY 1
            )
       """)

        if rebalance_type == "Investable Cash Dynamic" and not is_frac_shares:
            accounts = list(map(lambda _tup: str(_tup[0]), duck_engine.fetch(
            "SELECT DISTINCT account_name FROM cash",
            return_df=False
                )))
                
            map(Portfolio.dynamic_invest, accounts)
        return