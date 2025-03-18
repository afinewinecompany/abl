import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict
import pandas as pd

def fetch_api_data():
    """
    Fetch all required data from API and process it.
    Returns processed data or None if an error occurs.
    """
    try:
        # Create a placeholder in the sidebar for status
        with st.sidebar:
            status_container = st.empty()
            status_container.info("Fetching data...")

            # Initialize API client and data processor
            api_client = FantraxAPI()
            data_processor = DataProcessor()

            # Fetch all required data
            league_data = api_client.get_league_info()
            roster_data = api_client.get_team_rosters()
            standings_data = api_client.get_standings()
            player_ids = api_client.get_player_ids()

            # Process data
            processed_league_data = data_processor.process_league_info(league_data)
            processed_roster_data = data_processor.process_rosters(roster_data, player_ids)
            processed_standings_data = data_processor.process_standings(standings_data)

            # Clear the status message
            status_container.empty()

            return {
                'league_data': processed_league_data,
                'roster_data': processed_roster_data,
                'standings_data': processed_standings_data
            }
    except Exception as e:
        with st.sidebar:
            st.error(f"An error occurred while loading data: {str(e)}")
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