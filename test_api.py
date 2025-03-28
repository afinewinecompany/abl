import streamlit as st
import os
from api_client import FantraxAPI

def main():
    st.set_page_config(page_title="Fantrax API Test", layout="wide")
    
    st.title("🏆 Fantrax API Integration Test")
    
    # Initialize the API client
    api = FantraxAPI()
    
    # Display authentication status
    if os.path.exists("fantraxloggedin.cookie"):
        st.success("✅ Fantrax authentication cookie found")
    else:
        st.warning("⚠️ Fantrax authentication cookie not found")
        st.info("Please configure authentication in the main app")
    
    # Display API status
    st.markdown("### API Client Status")
    st.write(f"Mock Mode: {api.mock_mode}")
    st.write(f"League ID: {api.league_id}")
    
    # Create columns for API tests
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### League Info")
        if st.button("Test League Info", key="league"):
            with st.spinner("Fetching league info..."):
                info = api.get_league_info()
                st.json(info)
                
        st.markdown("### Teams")
        if st.button("Test Teams", key="teams"):
            with st.spinner("Fetching teams..."):
                teams = api.get_teams()
                st.json(teams)
    
    with col2:
        st.markdown("### Standings")
        if st.button("Test Standings", key="standings"):
            with st.spinner("Fetching standings..."):
                standings = api.get_standings()
                st.json(standings)
                
        st.markdown("### Rosters")
        if st.button("Test Rosters", key="rosters"):
            with st.spinner("Fetching rosters..."):
                rosters = api.get_team_rosters()
                st.json(rosters)
    
    st.markdown("---")
    
    # Add mock data info
    st.markdown("### Mock Data Info")
    if os.path.exists("mock_data"):
        mock_files = os.listdir("mock_data")
        if mock_files:
            st.write(f"Found {len(mock_files)} mock data files:")
            for file in mock_files:
                st.write(f"- {file}")
        else:
            st.write("No mock data files found")
    else:
        st.write("Mock data directory not found")
    
    # Add instructions for testing with real data
    st.markdown("---")
    st.markdown("### Using Real Fantrax API Data")
    st.markdown("""
    To use real data from Fantrax, follow these steps:
    
    1. Go to the main application
    2. Click "Configure Fantrax Authentication" in the sidebar
    3. Follow the instructions to generate and upload a cookie file
    4. Refresh this page and test the API endpoints again
    """)

if __name__ == "__main__":
    main()