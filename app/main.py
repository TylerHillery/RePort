import streamlit as st

from database import SQLite
from ui import Sidebar, HoldingsInput, Portfolio

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)
st.set_page_config(layout="wide")

with st.sidebar:
    Sidebar.header()
    rebalance_type = Sidebar.select_box()
    is_frac_shares = Sidebar.check_box()

with st.container():
    st.title("Portfolio Rebalancer ⚖️")
    st.text("Tool to help investors get positions back to target weights.")

with st.expander("Input Holdings"):
    operation,account,ticker,shares,target,cost,price = HoldingsInput.form()

with st.container():
    columns = {
        "account_name":     "Account",
        "ticker":           "Ticker",
        "security_name":    "Name",
        "shares":           "Shares",
        "target_weight":    "Target Weight (%)",
        "cost":             "Cost",
        "price":            "Price"
    }
    st.table(Portfolio
                .table()
                .rename(columns=columns)
                .assign(Cost_Dollars   = Portfolio.table().cost / 100)
                .assign(Price_Dollars  = Portfolio.table().price / 100)

    )