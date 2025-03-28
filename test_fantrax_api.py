import streamlit as st
import os
import json
from api_client import FantraxAPI

def main():
    st.set_page_config(page_title="Test Fantrax API", layout="wide")
    
    st.title("Fantrax API Test")
    
    # Check if cookie file exists
    if os.path.exists("fantraxloggedin.cookie"):
        st.success("✅ Fantrax authentication cookie found")
    else:
        st.warning("⚠️ Fantrax authentication cookie not found")
        st.info("Please run the create_fantrax_cookie.py script to generate the authentication cookie")
        
    # Initialize the API client
    api = FantraxAPI()
    
    st.write("### API Client Status")
    st.write(f"Mock Mode: {api.mock_mode}")
    st.write(f"League ID: {api.league_id}")
    
    st.markdown("---")
    
    # Create tabs for testing different API endpoints
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "League Info", 
        "Teams", 
        "Standings", 
        "Rosters", 
        "Scoring Periods",
        "Transactions"
    ])
    
    with tab1:
        st.subheader("League Info")
        if st.button("Fetch League Info", key="league_info"):
            with st.spinner("Fetching league information..."):
                league_info = api.get_league_info()
                st.json(league_info)
    
    with tab2:
        st.subheader("Teams")
        if st.button("Fetch Teams", key="teams"):
            with st.spinner("Fetching teams..."):
                teams = api.get_teams()
                st.json(teams)
    
    with tab3:
        st.subheader("Standings")
        if st.button("Fetch Standings", key="standings"):
            with st.spinner("Fetching standings..."):
                try:
                    standings = api.get_standings()
                    st.json(standings)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab4:
        st.subheader("Rosters")
        if st.button("Fetch Rosters", key="rosters"):
            with st.spinner("Fetching rosters..."):
                rosters = api.get_team_rosters()
                st.json(rosters)
    
    with tab5:
        st.subheader("Scoring Periods")
        if st.button("Fetch Scoring Periods", key="periods"):
            with st.spinner("Fetching scoring periods..."):
                periods = api.get_scoring_periods()
                st.json(periods)
    
    with tab6:
        st.subheader("Transactions")
        limit = st.slider("Number of transactions to fetch", 1, 100, 10)
        if st.button("Fetch Transactions", key="transactions"):
            with st.spinner(f"Fetching {limit} transactions..."):
                transactions = api.get_transactions(limit)
                st.json(transactions)
    
    st.markdown("---")
    st.write("### Debug Information")
    st.write(f"Current directory: {os.getcwd()}")
    if os.path.exists("mock_data"):
        st.write("Mock data directory exists")
        files = os.listdir("mock_data")
        st.write(f"Mock data files: {files}")

if __name__ == "__main__":
    main()