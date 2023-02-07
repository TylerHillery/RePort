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
    Portfolio rebalancing tool to help investors get positions back to target weights.
    """)

with st.expander("Input"):
    tab1, tab2 = st.tabs(["Holdings", "Cash"])
    with tab1:
        operation,account,ticker,shares,target,cost,price = HoldingsInput.form()
    with tab2:
         operation,account,cash = CashInput.form()

with st.container():
    holdings_columns = {
        "account_name":     "Account",
        "ticker":           "Ticker",
        "security_name":    "Name",
        "shares":           "Shares",
        "target_weight":    "Target Weight (%)",
        # "current_weight":   "Current Weight (%)",
        # "target_diff":      "Target Difference (%)",
        "cost":             "Cost ($)",
        "market_value":     "Market Value($)",
        "price":            "Price ($)",
        "gain_loss":        "Gain or Loss ($)",
        "gain_loss_pct":    "Gain or Loss (%)"
    }
    cash_columns = {
        "account_name":     "Account",
        "cash":             "Investable Cash ($)",
    }
    # TO DO: Handle empty df. 
    market_value = Portfolio.holdings().price * Portfolio.holdings().shares

    st.table(Portfolio
                .holdings()
                # .assign(target_diff =  (
                #     Portfolio.holdings().current_weight - Portfolio.holdings().target_weight
                #     )
                # )
                .assign(cost   = Portfolio.holdings().cost / 100)
                .assign(price  = Portfolio.holdings().price / 100)
                .assign(market_value = (market_value) / 100)
                .assign(gain_loss = (
                   market_value - Portfolio.holdings().cost 
                   ) / 100
                )
                .assign(gain_loss_pct =(
                   market_value - Portfolio.holdings().cost 
                   ) / Portfolio.holdings().cost * 100
                )
                .rename(columns=holdings_columns)
                .loc[:,list(holdings_columns.values())]
    )

    st.table(Portfolio
                .cash()
                .assign(cash   = Portfolio.cash().cash / 100)
                .rename(columns=cash_columns)
                .loc[:,list(cash_columns.values())]
                )
