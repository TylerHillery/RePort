import streamlit as st

from database import SQLite, get_query_string

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)

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
            cash*100
        )

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
            cost*100,
            price*100
        )

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
    def holdings():
        db.query(get_query_string(QUERIES_DIR + 'create_holdings_table')) 
        df = db.fetch(get_query_string(QUERIES_DIR + 'select_holdings'))
        holdings_columns = {
            "account_name":     "Account",
            "ticker":           "Ticker",
            "security_name":    "Name",
            "shares":           "Shares",
            "target_weight":    "Target Weight (%)",
            "current_weight":   "Current Weight (%)",
            "target_diff":      "Target Difference (%)",
            "cost":             "Cost ($)",
            "market_value":     "Market Value($)",
            "price":            "Price ($)",
            "gain_loss":        "Gain or Loss ($)",
            "gain_loss_pct":    "Gain or Loss (%)"
        }
        market_value = df.price * df.shares
        df = (df.assign(target_diff =  (df.current_weight - df.target_weight))
                .assign(cost = df.cost / 100)
                .assign(price = df.price / 100)
                .assign(market_value = (market_value) / 100)
                .assign(gain_loss = (market_value - df.cost) / 100)
                .assign(gain_loss_pct =(market_value - df.cost) / df.cost * 100)
                .rename(columns=holdings_columns)
                .loc[:,list(holdings_columns.values())]
                .style.format(precision=2,thousands=",")
            )
        return df
    def cash():
        db.query(get_query_string(QUERIES_DIR + 'create_cash_table')) 
        cash_columns = {
        "account_name": "Account",
        "cash": "Investable Cash ($)",
        }
        df = db.fetch(get_query_string(QUERIES_DIR + 'select_cash'))
        df = (df.assign(cash = df.cash / 100)
                .rename(columns = cash_columns)
                .loc[:,list(cash_columns.values())]
                .style.format(precision=2,thousands=",")
            )
        return df