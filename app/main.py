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
                    c1,c2,c3,c4 = st.columns([2,2,2,2,])
                    raw_holdings_df = Portfolio.get_holdings_table()
                    raw_future_holdings_df = Portfolio.get_future_holdings_table(rebalance_type,is_frac_shares)

                    holdings_df = duckdb.query(
                        f"""
                        SELECT *
                        FROM raw_holdings_df
                        WHERE account_name = '{accounts[index]}'
                        """
                    ).df()
                    
                    future_holdings_df = duckdb.query(
                        f"""
                        SELECT *
                        FROM raw_future_holdings_df
                        WHERE account_name = '{accounts[index]}'
                        """
                    ).df()


                    cash = duckdb.query(f"SELECT max(cash) FROM holdings_df").fetchall()[0][0]
                    cash_formatted = f"${cash:,.2f}"
                    c1.metric("Investable Cash",cash_formatted)


                    future_cash = duckdb.query(f"SELECT max(cash) FROM future_holdings_df").fetchall()[0][0]
                    future_cash_formatted = f"${future_cash:,.2f}"
                    
                    cash_delta = f"{future_cash - cash:,.2f}"
                    c2.metric("Investable Cash After Rebalance",future_cash_formatted,delta=cash_delta)

                    market_value = duckdb.query(f"SELECT sum(market_value) FROM holdings_df").fetchall()[0][0]
                    market_value_formatted = f"${market_value:,.2f}"

                    gain_loss = duckdb.query(f"SELECT sum(market_value) - sum(cost) FROM holdings_df").fetchall()[0][0]
                    gain_loss_formatted = f"{gain_loss:,.2f}"
                    c3.metric("Account Market Value",market_value_formatted, delta=gain_loss_formatted)

                    gain_loss_pct = duckdb.query(f"SELECT (sum(market_value) - sum(cost))/sum(cost) FROM holdings_df").fetchall()[0][0]
                    gain_loss_pct_formatted = f"{gain_loss_pct*100:,.2f}%"
                    c4.metric("Account Gain/Loss (%)",gain_loss_pct_formatted)
                
                with st.container():
                    c1, c2 = st.columns([2,2])
                    def color_negative_red(value):
                        """
                        Colors elements in a dateframe
                        green if positive and red if
                        negative. Does not color NaN
                        values.
                        """

                        if value < 0:
                            color = 'red'
                        elif value > 0:
                            color = 'green'
                        else:
                            color = 'black'

                        return 'color: %s' % color
                    
                    holdings_df_columns = {
                            "account_name"  : "Account",
                            "ticker"        : "Ticker",
                            "shares"        : "Shares",
                            "price"         : "Price",
                            "market_value"  : "Market Value",
                            "cost"          : "Cost",
                            "gain_loss"     : "Gain/Loss",
                            "gain_loss_pct" : "Gain/Loss %",
                            "target_weight" : "Target Weight",
                            "current_weight": "Current Weight",
                            "target_diff"   : "Target Diff"

                        }

                    c1.markdown("**Before Rebalance**")
                    c1.dataframe(holdings_df.loc[:,list(holdings_df_columns.keys())]
                                    .rename(columns=holdings_df_columns)
                                    .style
                                    .applymap(color_negative_red, subset=['Target Diff',"Gain/Loss","Gain/Loss %"])
                                    .format({
                                        'Target Weight':    lambda x: f"{x:,.2f}%",
                                        'Current Weight':   lambda x: f"{x:,.2f}%",
                                        'Target Diff':      lambda x: f"{x:,.2f}%",
                                        'Gain/Loss %':    lambda x: f"{x:,.2f}%",
                                        'Cost':             lambda x: f"${x:,.2f}",
                                        'Market Value':     lambda x: f"${x:,.2f}",
                                        'Price':            lambda x: f"${x:,.2f}",
                                        'Gain/Loss':        lambda x: f"${x:,.2f}",
                                        'Shares':           lambda x: f"{x:,.4f}"    
                                    }))
                    c2.markdown("**After Rebalance**")
                    c2.dataframe(future_holdings_df.loc[:,list(holdings_df_columns.keys())]
                                    .rename(columns=holdings_df_columns)
                                    .style
                                    .applymap(color_negative_red, subset=['Target Diff',"Gain/Loss","Gain/Loss %"])
                                    .format({
                                        'Target Weight':    lambda x: f"{x:,.2f}%",
                                        'Current Weight':   lambda x: f"{x:,.2f}%",
                                        'Target Diff':      lambda x: f"{x:,.2f}%",
                                        'Gain/Loss %':    lambda x: f"{x:,.2f}%",
                                        'Cost':             lambda x: f"${x:,.2f}",
                                        'Market Value':     lambda x: f"${x:,.2f}",
                                        'Price':            lambda x: f"${x:,.2f}",
                                        'Gain/Loss':        lambda x: f"${x:,.2f}",
                                        'Shares':           lambda x: f"{x:,.4f}"    
                                    }))

                    
                with st.container():
                    c1,c2 = st.columns([7,3])
                    combined_df = duckdb.query(
                        f"""
                        SELECT
                            'Before' as rebalance,
                            ticker,
                            shares,
                            target_weight,
                            current_weight,
                            target_diff,
                            cost,
                            market_value,
                            price,
                            gain_loss,
                            gain_loss_pct,
                        FROM
                            holdings_df
                        WHERE account_name = '{accounts[index]}'
                        UNION
                        SELECT
                            'After' as rebalance,
                            ticker,
                            shares,
                            target_weight,
                            current_weight,
                            target_diff,
                            cost,
                            market_value,
                            price,
                            gain_loss,
                            gain_loss_pct,
                        FROM
                            future_holdings_df
                        WHERE account_name = '{accounts[index]}'
                        """
                    ).df()


                    vega_chart = {
                        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                        # "title": {"text": "Comparison of Target Weight Differences Before vs After Rebalance","anchor": "middle"},
                        "mark": "bar",
                        "encoding": {
                            "x": {"field": "ticker","title" :"Ticker"},
                            "y": {"field": "target_diff", "type": "quantitative","title" :"Diff From Target Weight (%)"},
                            "tooltip": [
                                {"field": "ticker", "type": "nominal", "title": "Ticker"},
                                {"field": "target_weight", "type": "quantitative", "title":"Target Weight (%)"},
                                {"field": "target_diff", "type": "quantitative","title":"Target Diff (%)"}
                            ],
                            "xOffset": {"field": "rebalance", "sort": "descending"},
                            "color": {
                                "field": "rebalance", 
                                "sort": "descending",
                                "title":"After or Before Rebalance"
                            }   
                        }
                    }
                        
                    c1.markdown('<div style="text-align: center;"><strong>Comparison of Target Weight Differences Before vs After Rebalance</strong></div>', unsafe_allow_html=True)
                    
                    c1.vega_lite_chart(combined_df,vega_chart,use_container_width=True)

                    orders_df = duckdb.query(
                        """
                        SELECT
                            CASE
                                WHEN (future.shares - current.shares) > 0 then 'Buy'
                                ELSE 'Sell'
                            END AS "Order Type",
                            current.ticker AS Ticker,
                            future.shares - current.shares AS Shares,
                            current.price AS Price,
                            (future.shares - current.shares) * -1 * current.price AS "Trade Amount"
                        FROM
                            holdings_df AS current
                            INNER JOIN future_holdings_df AS future using(holding_id)
                        WHERE
                            (future.shares - current.shares) != 0           
                        ORDER BY
                            Ticker
                        """
                    ).df()
                    c2.markdown('<div style="text-align: center;"><strong>Orders Needed For Rebalance</strong></div>', unsafe_allow_html=True)
                    c2.dataframe(orders_df.style
                                        .applymap(color_negative_red, subset=["Trade Amount"])
                                        .format({
                                        'Price':            lambda x: f"${x:,.2f}",
                                        'Trade Amount':     lambda x: f"${x:,.2f}",
                                        'Shares':           lambda x: f"{x:,.4f}"    
                                    }))