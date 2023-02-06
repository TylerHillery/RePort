import streamlit as st

class sidebar(): 
    def header():
        st.header("Configurations")
    def select_box():
        rebalance_type = st.selectbox(
            "Select Rebalance Type",
            ("New Money Only","Whole Portfolio")
        )
        return rebalance_type
    
    def check_box():
        is_frac_shares = st.checkbox("Are you allowed fractional share investing?")
        return is_frac_shares

class holdings_input():
    def header():
        st.markdown("#### **Input Holdings**") 
    def widgets():
        c1, c2, c3, c4, c5, c6 = st.columns((1.5,1.5,1.5,1.5,3,6))
        operation   = c1.selectbox("Select Operation",("Add","Update","Delete"))
        ticker      = c2.text_input('Ticker')
        shares      = c3.number_input('Shares')
        cost        = c4.number_input('Cost')
        target      = c5.slider('Target Weight (%)')
        return (operation, ticker,shares,cost,target)
    def button():
        enter = st.button(label='Enter')
        return enter