import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict, List
import pandas as pd
import os
import pickle
import json

@st.cache_data
def fetch_api_data():
    """
    Fetch all required data from API and process it.
    Returns processed data or None if an error occurs.
    """
    try:
        # Create a placeholder in the sidebar for a single loading indicator
        with st.sidebar:
            status_container = st.empty()
            status_container.progress(0)

            # Initialize API client and data processor
            api_client = FantraxAPI()
            data_processor = DataProcessor()

            # Fetch and process all data with a single progress indicator
            status_container.progress(25)
            league_data = api_client.get_league_info()
            processed_league_data = data_processor.process_league_info(league_data)

            status_container.progress(50)
            roster_data = api_client.get_team_rosters()
            processed_roster_data = data_processor.process_rosters(roster_data, api_client.get_player_ids())

            status_container.progress(75)
            standings_data = api_client.get_standings()
            processed_standings_data = data_processor.process_standings(standings_data)

            # Clear the progress bar
            status_container.empty()

            return {
                'league_data': processed_league_data,
                'roster_data': processed_roster_data,
                'standings_data': processed_standings_data
            }
    except Exception as e:
        with st.sidebar:
            st.error(f"❌ Error loading data: {str(e)}")
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

def save_power_rankings_data(points_data: pd.DataFrame = None, weekly_results: List[Dict] = None):
    """
    Save power rankings data to disk for permanent storage.
    
    Args:
        points_data: DataFrame containing team points data
        weekly_results: List of dictionaries containing weekly results
    """
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save team points data if provided
    if points_data is not None and not points_data.empty:
        points_data.to_csv('data/power_rankings_points.csv', index=False)
    
    # Save weekly results data if provided
    if weekly_results is not None and len(weekly_results) > 0:
        with open('data/power_rankings_weekly.json', 'w') as f:
            json.dump(weekly_results, f)

def load_power_rankings_data() -> Dict:
    """
    Load power rankings data from disk.
    
    Returns:
        Dictionary containing power rankings data
    """
    result = {
        'points_data': None,
        'weekly_results': []
    }
    
    # Load team points data if file exists
    if os.path.exists('data/power_rankings_points.csv'):
        try:
            result['points_data'] = pd.read_csv('data/power_rankings_points.csv')
        except Exception as e:
            st.warning(f"Error loading power rankings points data: {str(e)}")
    
    # Load weekly results data if file exists
    if os.path.exists('data/power_rankings_weekly.json'):
        try:
            with open('data/power_rankings_weekly.json', 'r') as f:
                result['weekly_results'] = json.load(f)
        except Exception as e:
            st.warning(f"Error loading power rankings weekly data: {str(e)}")
    
    return result

def clear_power_rankings_data():
    """Delete all saved power rankings data"""
    if os.path.exists('data/power_rankings_points.csv'):
        os.remove('data/power_rankings_points.csv')
    
    if os.path.exists('data/power_rankings_weekly.json'):
        os.remove('data/power_rankings_weekly.json')

