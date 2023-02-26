import json

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

    def get_raw_holdings_table():
        return db.fetch(get_query_string("select_raw_holdings"))
    
    def get_raw_cash_table():
        return db.fetch(get_query_string("select_raw_cash"))

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
    
    def get_holdings_df_filtered(accounts, index):
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
        return holdings_df,future_holdings_df
    
    def investable_cash_metric(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
                                        )

        cash = db.fetch("SELECT max(cash) FROM holdings_df",return_df=False)[0][0]
        cash_formatted = f"${cash:,.2f}"
        column.metric("Investable Cash",cash_formatted)
        return 
    
    def future_cash_metric(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
                                        )
        cash = db.fetch("SELECT max(cash) FROM holdings_df",return_df=False)[0][0]
        future_cash = db.fetch("SELECT max(cash) FROM future_holdings_df",
                               return_df=False)[0][0]
        future_cash_formatted = f"${future_cash:,.2f}"
        cash_delta = f"{future_cash - cash:,.2f}"
        column.metric("Investable Cash After Rebalance",
                  future_cash_formatted,delta=cash_delta)
        return None

    def market_value_metric(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
                                        )
        
        market_value = db.fetch("SELECT sum(market_value) FROM holdings_df",
                                return_df=False)[0][0]
        market_value_formatted = f"${market_value:,.2f}"

        gain_loss = db.fetch("SELECT sum(market_value) - sum(cost) FROM holdings_df",
                             return_df=False)[0][0]
        gain_loss_formatted = f"{gain_loss:,.2f}"
        column.metric("Account Market Value",
                  market_value_formatted,
                  delta=gain_loss_formatted)
        return None
    
    def gain_loss_metric(accounts,index,column): 
        holdings_df, future_holdings_df = (Portfolio
                                    .get_holdings_df_filtered(accounts,index)
                                )
        gain_loss_pct = db.fetch("SELECT (sum(market_value) - sum(cost))/sum(cost) " +
                                 "FROM holdings_df",
                                 return_df=False)[0][0]
        gain_loss_pct_formatted = f"{gain_loss_pct*100:,.2f}%"
        column.metric("Account Gain/Loss (%)",gain_loss_pct_formatted)
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

        return 'color: %s' % color

  
    def holdings_df_styled(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
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
        column.markdown(            
            '<div style="text-align: center;">' +
            '<strong>Before  Rebalance </strong>' +
            '</div>',
             unsafe_allow_html=True
            )
        column.dataframe(holdings_df.loc[:,list(holdings_df_columns.keys())]
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
    
    def future_holdings_df_styled(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
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
        column.markdown(            
            '<div style="text-align: center;">' +
            '<strong>After Rebalance </strong>' +
            '</div>',
            unsafe_allow_html=True
            )
        column.dataframe(future_holdings_df.loc[:,list(holdings_df_columns.keys())]
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
        
    
    def grouped_bar_chart(accounts,index,column): 
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
                                        )
        combined_df = db.fetch(get_query_string("combined_holdings"))

        with open('app/grouped_bar_chart.json',"r") as file:
            vega_chart = json.load(file)

        column.markdown(
            '<div style="text-align: left;">' +
            '<strong>Comparison of Target Weight Differences Before vs ' +
            'After Rebalance</strong>' +
            '</div>',
            unsafe_allow_html=True)
        
        column.vega_lite_chart(combined_df,vega_chart,use_container_width=True)
        
        return None
    
    def orders_df_styled(accounts,index,column):
        holdings_df, future_holdings_df = (Portfolio
                                           .get_holdings_df_filtered(accounts,index)
                                        )
        combined_df = db.fetch(get_query_string("combined_holdings"))

        orders_df = db.fetch(get_query_string("select_orders"))

        column.markdown(
            '<div style="text-align: left;">' +
            '<strong>Orders Needed For Rebalance</strong>' +
            '</div>',
            unsafe_allow_html=True)
        
        column.dataframe(orders_df.style
                            .applymap(Portfolio.color_negative_red, 
                                      subset=["Trade Amount"])
                            .format({
                            'Price':            lambda x: f"${x:,.2f}",
                            'Trade Amount':     lambda x: f"${x:,.2f}",
                            'Shares':           lambda x: f"{x:,.4f}"    
                        }))
        return None
