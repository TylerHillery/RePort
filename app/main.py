import streamlit as st

from ui import Sidebar, HoldingsInput, CashInput,Portfolio

st.set_page_config(layout="wide")

Portfolio.create_tables()

with st.sidebar:
    Sidebar.header()
    rebalance_type  = Sidebar.select_box()
    is_frac_shares  = Sidebar.check_box()


with st.container():
    st.title("RePort ⚖️")
    st.text("A portfolio rebalancing tool to help investors " +
    "get their positions back to target weights.")

with st.expander("Input"):
    tab1, tab2 = st.tabs(["Holdings", "Cash"])
    with tab1:
        operation,account,ticker,shares,target,cost,price = HoldingsInput.form()
    with tab2:
         operation,account,cash = CashInput.form()

with st.container():    
    st.markdown("#### **Portfolio**")
    st.table(Portfolio.get_holdings_table())
    st.table(Portfolio.get_cash_table())
    st.table(Portfolio.get_future_holdings_table(rebalance_type,is_frac_shares))

    st.write(Portfolio.get_accounts())