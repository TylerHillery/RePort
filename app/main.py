import streamlit as st

from database import SQLite
from ui import Sidebar, HoldingsInput, CashInput, Portfolio

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)
st.set_page_config(layout="wide")

with st.sidebar:
    Sidebar.header()
    rebalance_type  = Sidebar.select_box()
    is_frac_shares  = Sidebar.check_box()

with st.container():
    st.title("RePort ⚖️")
    st.text("""
    A portfolio rebalancing tool to help investors get their positions back to target weights.
    """)

with st.expander("Input"):
    tab1, tab2 = st.tabs(["Holdings", "Cash"])
    with tab1:
        operation,account,ticker,shares,target,cost,price = HoldingsInput.form()
    with tab2:
         operation,account,cash = CashInput.form()

with st.container():    
    Portfolio.header()
    st.table(Portfolio.holdings())
    st.table(Portfolio.cash())
