import duckdb
import streamlit as st

from ui import Sidebar, HoldingsInput, CashInput,Portfolio

st.set_page_config(layout="wide")

with st.sidebar:
    Sidebar.header()
    input_method = Sidebar.radio()
    rebalance_type = Sidebar.select_box()
    is_frac_shares = Sidebar.check_box_frac_shares()
    add_sample_data = Sidebar.check_box_sample_data()
    Portfolio.create_tables(rebalance_type,is_frac_shares)

with st.container():
    st.title("RePort ⚖️")
    st.text("A portfolio rebalancing tool to help investors " +
    "get their positions back to target weights.")

with st.expander("Input"):
    if input_method == "Manual":
        tab1, tab2 = st.tabs(["Holdings", "Cash"])
        with tab1:
            # HoldingsInput.form()
            holdings_df = Portfolio.get_raw_holdings_table()
            edit_holdings_df = st.experimental_data_editor(holdings_df, key='edit_holdings',num_rows="dynamic")
            Portfolio.update_tables('holdings',edit_holdings_df)
        with tab2:
            cash_df = Portfolio.get_raw_cash_table()
            edit_cash_df = st.experimental_data_editor(cash_df,key="edit_cash",num_rows="dynamic")
            Portfolio.update_tables('cash',edit_cash_df)
    elif input_method == "File":
        tab1, tab2 = st.tabs(["Holdings", "Cash"])
        with tab1:
            HoldingsInput.file()
        with tab2:
            CashInput.file()

with st.container():    
    accounts = Portfolio.get_accounts()

    if not accounts:
        st.error("Please enter in some data!", icon="🚨")
    else:
        for index,container in enumerate(st.tabs(accounts)):
            with container:
                with st.container():
                    Portfolio.metrics(accounts,index)
                
                with st.container():
                   Portfolio.dataframes(accounts,index)

                with st.container():
                    Portfolio.visuals(accounts,index)