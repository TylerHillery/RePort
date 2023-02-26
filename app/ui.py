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

class Portfolio():
    def create_tables(rebalance_type, is_frac_shares):
        db.query(get_query_string('create_holdings_table')) 
        db.query(get_query_string('create_cash_table'))
        Portfolio.create_future_holdings(rebalance_type,is_frac_shares)

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

    def metrics(accounts,index):
        c1,c2,c3,c4 = st.columns([2,2,2,2,])
        raw_holdings_df = db.fetch(get_query_string("select_holdings"))
        raw_future_holdings_df = db.fetch(get_query_string("select_future_holdings"))
        holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )
        
        future_holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_future_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )

        cash = db.fetch("SELECT max(cash) FROM holdings_df",return_df=False)[0][0]
        cash_formatted = f"${cash:,.2f}"
        c1.metric("Investable Cash",cash_formatted)


        future_cash = db.fetch("SELECT max(cash) FROM future_holdings_df",return_df=False)[0][0]
        future_cash_formatted = f"${future_cash:,.2f}"
        
        cash_delta = f"{future_cash - cash:,.2f}"
        c2.metric("Investable Cash After Rebalance",
                  future_cash_formatted,delta=cash_delta)

        market_value = db.fetch("SELECT sum(market_value) FROM holdings_df",
                                return_df=False)[0][0]
        market_value_formatted = f"${market_value:,.2f}"

        gain_loss = db.fetch("SELECT sum(market_value) - sum(cost) FROM holdings_df",
                             return_df=False)[0][0]
        gain_loss_formatted = f"{gain_loss:,.2f}"
        c3.metric("Account Market Value",
                  market_value_formatted,
                  delta=gain_loss_formatted)

        gain_loss_pct = db.fetch("SELECT (sum(market_value) - sum(cost))/sum(cost) FROM holdings_df",
                                 return_df=False)[0][0]
        gain_loss_pct_formatted = f"{gain_loss_pct*100:,.2f}%"
        c4.metric("Account Gain/Loss (%)",gain_loss_pct_formatted)

        return None

    def color_negative_red(value):
        """
        Colors elements in a date frame
        green if positive and red if
        negative. Does not color NaN
        values.
        """

        if value < 0:
            color = 'red'
        elif value > 0:
            color = 'green'
        else:
            color = 'black'

        return f'{color}: %s'

    def dataframes(accounts,index):
        c1, c2 = st.columns([2,2])
        raw_holdings_df = db.fetch(get_query_string("select_holdings"))
        raw_future_holdings_df = db.fetch(get_query_string("select_future_holdings"))
        holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )
        
        future_holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_future_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )    
        holdings_df_columns = {
                            "account_name"  : "Account",
                            "ticker"        : "Ticker",
                            "shares"        : "Shares",
                            "price"         : "Price",
                            "market_value"  : "Market Value",
                            "cost"          : "Cost",
                            "gain_loss"     : "Gain/Loss",
                            "gain_loss_pct" : "Gain/Loss %",
                            "target_weight" : "Target Weight",
                            "current_weight": "Current Weight",
                            "target_diff"   : "Target Diff"

                        }

        c1.markdown("**Before Rebalance**")
        c1.dataframe(holdings_df.loc[:,list(holdings_df_columns.keys())]
                        .rename(columns=holdings_df_columns)
                        .style
                        .applymap(Portfolio.color_negative_red, 
                                  subset=['Target Diff',"Gain/Loss","Gain/Loss %"])
                        .format({
                            'Target Weight':    lambda x: f"{x:,.2f}%",
                            'Current Weight':   lambda x: f"{x:,.2f}%",
                            'Target Diff':      lambda x: f"{x:,.2f}%",
                            'Gain/Loss %':      lambda x: f"{x:,.2f}%",
                            'Cost':             lambda x: f"${x:,.2f}",
                            'Market Value':     lambda x: f"${x:,.2f}",
                            'Price':            lambda x: f"${x:,.2f}",
                            'Gain/Loss':        lambda x: f"${x:,.2f}",
                            'Shares':           lambda x: f"{x:,.4f}"    
                        }))
        c2.markdown("**After Rebalance**")
        c2.dataframe(future_holdings_df.loc[:,list(holdings_df_columns.keys())]
                        .rename(columns=holdings_df_columns)
                        .style
                        .applymap(Portfolio.color_negative_red, 
                                  subset=['Target Diff',"Gain/Loss","Gain/Loss %"])
                        .format({
                            'Target Weight':    lambda x: f"{x:,.2f}%",
                            'Current Weight':   lambda x: f"{x:,.2f}%",
                            'Target Diff':      lambda x: f"{x:,.2f}%",
                            'Gain/Loss %':      lambda x: f"{x:,.2f}%",
                            'Cost':             lambda x: f"${x:,.2f}",
                            'Market Value':     lambda x: f"${x:,.2f}",
                            'Price':            lambda x: f"${x:,.2f}",
                            'Gain/Loss':        lambda x: f"${x:,.2f}",
                            'Shares':           lambda x: f"{x:,.4f}"    
                        }))
        
        return None

    def visuals(accounts,index):
        c1,c2 = st.columns([7,3])
        raw_holdings_df = db.fetch(get_query_string("select_holdings"))
        raw_future_holdings_df = db.fetch(get_query_string("select_future_holdings"))
        holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )
        
        future_holdings_df = db.fetch(
            f"""
            SELECT *
            FROM raw_future_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )   
        combined_df = db.fetch(
            f"""
            SELECT
                'Before' as rebalance,
                ticker,
                shares,
                target_weight,
                current_weight,
                target_diff,
                cost,
                market_value,
                price,
                gain_loss,
                gain_loss_pct,
            FROM
                holdings_df
            WHERE account_name = '{accounts[index]}'
            UNION
            SELECT
                'After' as rebalance,
                ticker,
                shares,
                target_weight,
                current_weight,
                target_diff,
                cost,
                market_value,
                price,
                gain_loss,
                gain_loss_pct,
            FROM
                future_holdings_df
            WHERE account_name = '{accounts[index]}'
            """
        )

        vega_chart = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": "bar",
            "encoding": {
                "x": {"field": "ticker","title" :"Ticker"},
                "y": {"field": "target_diff", "type": "quantitative","title" :"Diff From Target Weight (%)"},
                "tooltip": [
                    {"field": "ticker", "type": "nominal", "title": "Ticker"},
                    {"field": "target_weight", "type": "quantitative", "title":"Target Weight (%)"},
                    {"field": "target_diff", "type": "quantitative","title":"Target Diff (%)"}
                ],
                "xOffset": {"field": "rebalance", "sort": "descending"},
                "color": {
                    "field": "rebalance", 
                    "sort": "descending",
                    "title":"After or Before Rebalance"
                }   
            }
        }
            
        c1.markdown('<div style="text-align: center;"><strong>Comparison of Target Weight Differences Before vs After Rebalance</strong></div>', unsafe_allow_html=True)
        
        c1.vega_lite_chart(combined_df,vega_chart,use_container_width=True)

        orders_df = db.fetch(
            """
            SELECT
                CASE
                    WHEN (future.shares - current.shares) > 0 then 'Buy'
                    ELSE 'Sell'
                END AS "Order Type",
                current.ticker AS Ticker,
                future.shares - current.shares AS Shares,
                current.price AS Price,
                (future.shares - current.shares) * -1 * current.price AS "Trade Amount"
            FROM
                holdings_df AS current
                INNER JOIN future_holdings_df AS future using(holding_id)
            WHERE
                (future.shares - current.shares) != 0           
            ORDER BY
                Ticker
            """
        )
        c2.markdown(
            '''
            <div style="text-align: center;"><strong>Orders Needed For Rebalance</strong></div>
            ''',
            unsafe_allow_html=True)
        c2.dataframe(orders_df.style
                            .applymap(Portfolio.color_negative_red, 
                                      subset=["Trade Amount"])
                            .format({
                            'Price':            lambda x: f"${x:,.2f}",
                            'Trade Amount':     lambda x: f"${x:,.2f}",
                            'Shares':           lambda x: f"{x:,.4f}"    
                        }))
        return None