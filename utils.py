import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict
import pandas as pd

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_api_data():
    """
    Fetch all required data from API and process it.
    Returns processed data or None if an error occurs.
    """
    try:
        # Create a placeholder in the sidebar for a single loading indicator
        status_container = None
        try:
            with st.sidebar:
                status_container = st.empty()
                status_container.progress(0)
        except:
            print("Running outside of Streamlit context")
        
        # Initialize API client and data processor
        api_client = FantraxAPI()
        data_processor = DataProcessor()

        # Fetch and process all data with a single progress indicator
        if status_container:
            status_container.progress(20)
            
        league_data = api_client.get_league_info()
        processed_league_data = data_processor.process_league_info(league_data)

        if status_container:
            status_container.progress(40)
            
        roster_data = api_client.get_team_rosters()
        processed_roster_data = data_processor.process_rosters(roster_data, api_client.get_player_ids())

        if status_container:
            status_container.progress(60)
            
        standings_data = api_client.get_standings()
        processed_standings_data = data_processor.process_standings(standings_data)

        # Fetch matchup data using Selenium
        if status_container:
            status_container.progress(80)
            
        try:
            # Safe method to get matchups data
            matchups_data = api_client.get_selenium_matchups()
        except Exception as matchup_error:
            print(f"Error fetching matchups: {str(matchup_error)}")
            # Return mock data if Selenium fails
            matchups_data = api_client._get_mock_data("getMatchups")
        
        # Clear the progress bar
        if status_container:
            status_container.empty()

        result = {
            'league_data': processed_league_data,
            'roster_data': processed_roster_data,
            'standings_data': processed_standings_data,
            'matchups_data': matchups_data
        }
        
        # Debug output
        print(f"Data fetch complete. Keys: {list(result.keys())}")
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error loading data: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            with st.sidebar:
                st.error(error_msg)
        except:
            pass
        return None

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.3f}%"

def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return data.get(key, default)

def calculate_stats(df: pd.DataFrame, column: str) -> Dict[str, float]:
    """Calculate basic statistics for a DataFrame column"""
    return {
        'mean': df[column].mean(),
        'median': df[column].median(),
        'max': df[column].max(),
        'min': df[column].min()
    }

