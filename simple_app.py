import streamlit as st
import pandas as pd
from utils import fetch_api_data, format_percentage, load_power_rankings_data, load_weekly_results

# Configure page
st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Basic CSS
st.markdown("""
<style>
.stApp {
    background-color: rgba(10, 12, 20, 0.95);
}
h1 {
    color: #ffffff;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


def main():
    try:
        # Header
        st.title("ABL Analytics")
        
        # Simple tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "League Info", 
            "Standings", 
            "Power Rankings", 
            "Team Rosters", 
            "Dynasty Dominance Index"
        ])
        
        with tab1:
            st.write("League Information")
            
        with tab2:
            st.write("Standings")
            
        with tab3:
            st.write("Power Rankings")
            
        with tab4:
            st.write("Team Rosters")
            
        with tab5:
            st.write("Dynasty Dominance Index")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Stack trace:", exc_info=e)


if __name__ == "__main__":
    main()