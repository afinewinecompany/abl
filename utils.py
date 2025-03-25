import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict
import pandas as pd
# Import the new Fantrax API wrapper
from fantrax_integration import fantrax_client

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

@st.cache_data
def fetch_fantrax_data():
    """
    Fetch all required data from the Fantrax API using the new integration.
    Returns processed data or None if an error occurs.
    """
    try:
        # Create a placeholder in the sidebar for a single loading indicator
        with st.sidebar:
            status_container = st.empty()
            status_container.progress(0)
            
            # Fetch league info
            status_container.progress(20)
            league_info = fantrax_client.get_league_info()
            
            # Fetch standings
            status_container.progress(40)
            standings = fantrax_client.get_standings()
            
            # Fetch team rosters
            status_container.progress(60)
            rosters = fantrax_client.get_team_rosters()
            
            # Fetch transactions
            status_container.progress(80)
            transactions = fantrax_client.get_transactions(limit=20)
            
            # Fetch scoring periods and current matchups
            status_container.progress(90)
            scoring_periods = fantrax_client.get_scoring_periods()
            current_matchups = fantrax_client.get_matchups_for_period(0)  # Current period
            
            # Clear the progress bar
            status_container.empty()
            
            # Convert roster dictionary to DataFrame format for compatibility with existing code
            roster_df = []
            for team_name, players in rosters.items():
                for player in players:
                    player['team'] = team_name
                    roster_df.append(player)
            
            if roster_df:
                roster_df = pd.DataFrame(roster_df)
            else:
                roster_df = pd.DataFrame()
            
            return {
                'league_data': league_info,
                'standings_data': standings,
                'roster_data': roster_df,
                'transactions': transactions,
                'scoring_periods': scoring_periods,
                'current_matchups': current_matchups
            }
    except Exception as e:
        with st.sidebar:
            st.error(f"❌ Error loading Fantrax data: {str(e)}")
        return None