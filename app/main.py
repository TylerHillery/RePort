import streamlit as st

from database import SQLite
from ui import sidebar, holdings_input

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)
st.set_page_config(layout="wide")

with st.sidebar:
    sidebar.header()
    rebalance_type = sidebar.select_box()
    is_frac_shares = sidebar.check_box()

with st.container():
    st.title("Portfolio Rebalancer ⚖️")
    st.text("Tool to help investors get positions back to target weights.")

with st.container():
    holdings_input.header() 
    operation,account,ticker,shares,cost,target = holdings_input.widgets()
    enter = holdings_input.button()