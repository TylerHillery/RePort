import streamlit as st

class sidebar(): 
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

class holdings_input():
    def header():
        st.markdown("#### **Input Holdings**") 
    def widgets():
        c1, c2, c3, c4, c5, c6, c7 = st.columns((1,1.5,1,1.5,1.5,3,3))
        operation   = c1.selectbox('Select Operation',('Add','Update','Delete'))
        account     = c2.text_input('Account Name')
        ticker      = c3.text_input('Ticker')
        shares      = c4.number_input('Shares')
        cost        = c5.number_input('Cost')
        target      = c6.slider('Target Weight (%)')
        return (operation,account,ticker,shares,cost,target)
    def button():
        enter = st.button(label='Enter')
        return enter