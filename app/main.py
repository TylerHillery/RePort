import streamlit as st

from database import SQLite
from ui import Sidebar, HoldingsInput, Portfolio

PORTFOLIO_DB = "data/portfolio.db"
QUERIES_DIR = "app/data/queries/"

db = SQLite(PORTFOLIO_DB)
st.set_page_config(layout="wide")

with st.sidebar:
    Sidebar.header()
    rebalance_type  = Sidebar.select_box()
    investable_cash = Sidebar.number_input()
    is_frac_shares  = Sidebar.check_box()

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
        "current_weight":   "Current Weight (%)",
        "target_diff":      "Target Difference (%)",
        "cost":             "Cost ($)",
        "market_value":     "Market Value($)",
        "price":            "Price ($)",
        "gain_loss":        "Gain or Loss ($)",
        "gain_loss_pct":    "Gain or Loss (%)"
    }
    # TO DO: Handle empty df. 
    market_value = Portfolio.table().price * Portfolio.table().shares
    
    st.table(Portfolio
                .table()
                .assign(target_diff =  (
                    Portfolio.table().current_weight - Portfolio.table().target_weight
                    )
                )
                .assign(cost   = Portfolio.table().cost / 100)
                .assign(price  = Portfolio.table().price / 100)
                .assign(market_value = (market_value) / 100)
                .assign(gain_loss = (
                   market_value - Portfolio.table().cost 
                   ) / 100
                )
                .assign(gain_loss_pct =(
                   market_value - Portfolio.table().cost 
                   ) / Portfolio.table().cost * 100
                )
                .rename(columns=columns)
                .loc[:,list(columns.values())]
    )
