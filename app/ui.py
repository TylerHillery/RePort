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
            ("Investable Cash","Whole Portfolio")
        )
        return rebalance_type
    
    def check_box():
        is_frac_shares = st.checkbox("Are you allowed fractional share investing?")
        return is_frac_shares

class HoldingsInput():    
    def form():
        form = st.form("holdings_input")
        c1, c2, c3, c4, c5, c6, c7 = form.columns((1,1.5,1,1.5,1.5,3,3))
        operation   = c1.selectbox('Select Operation',('Add','Update','Delete'))
        account     = c2.text_input('Account Name')
        ticker      = c3.text_input('Ticker')
        shares      = c4.number_input('Shares')
        cost        = c5.number_input('Cost')
        target      = c6.slider('Target Weight (%)')
        submitted   = form.form_submit_button("Submit")
        
        data = (operation,account,ticker,shares,cost,target)

        if submitted:
            if operation == 'Add':
                db.query(
                    get_query_string(QUERIES_DIR + 'insert_holdings_values'), 
                    [data[1:]]
                )
        return data

class Portfolio():
    def header():
        st.markdown("#### **Portfolio**")
    def table():
        # db.query("DROP TABLE IF EXISTS holdings")
        db.query(get_query_string(QUERIES_DIR + 'create_holdings_table')) 
        return db.fetch(get_query_string(QUERIES_DIR + 'select_holdings'))