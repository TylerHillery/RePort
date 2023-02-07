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
    
    def number_input():
        investable_cash = st.number_input('Investable Cash ($)',min_value = 0.00)
        return investable_cash

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
    def table():
        # db.query("DROP TABLE IF EXISTS holdings")
        db.query(get_query_string(QUERIES_DIR + 'create_holdings_table')) 
        return db.fetch(get_query_string(QUERIES_DIR + 'select_holdings'))