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
            
            # Fetch league info with error handling
            status_container.progress(20)
            try:
                league_info = fantrax_client.get_league_info()
            except Exception as e:
                st.warning(f"Warning: Could not fetch league info: {str(e)}")
                league_info = {}
            
            # Fetch standings with error handling
            status_container.progress(40)
            try:
                standings = fantrax_client.get_standings()
            except Exception as e:
                st.warning(f"Warning: Could not fetch standings: {str(e)}")
                standings = pd.DataFrame()
            
            # Fetch team rosters with error handling
            status_container.progress(60)
            try:
                rosters = fantrax_client.get_team_rosters()
            except Exception as e:
                st.warning(f"Warning: Could not fetch team rosters: {str(e)}")
                rosters = {}
            
            # Fetch transactions with error handling
            status_container.progress(75)
            try:
                transactions = fantrax_client.get_transactions(limit=20)
                st.sidebar.info(f"Found {len(transactions)} transactions")
                
                # Debug the first transaction if available
                if transactions and len(transactions) > 0:
                    st.sidebar.info(f"First transaction keys: {list(transactions[0].keys())}")
                    
            except Exception as e:
                st.sidebar.error(f"Warning: Could not fetch transactions: {str(e)}")
                transactions = []
            
            # Fetch scoring periods with error handling
            status_container.progress(85)
            try:
                scoring_periods = fantrax_client.get_scoring_periods()
            except Exception as e:
                st.warning(f"Warning: Could not fetch scoring periods: {str(e)}")
                scoring_periods = []
            
            # Fetch current matchups with error handling
            status_container.progress(90)
            try:
                current_matchups = fantrax_client.get_matchups_for_period()
            except Exception as e:
                st.warning(f"Warning: Could not fetch matchups: {str(e)}")
                current_matchups = []
            
            # Fetch live scoring data with error handling
            status_container.progress(95)
            try:
                live_scoring = fantrax_client.get_live_scoring()
                st.sidebar.success("Successfully fetched live scoring data.")
            except Exception as e:
                st.warning(f"Warning: Could not fetch live scoring data: {str(e)}")
                live_scoring = {}
            
            # Clear the progress bar
            status_container.empty()
            
            # Convert roster dictionary to DataFrame format for compatibility with existing code
            roster_df = []
            for team_name, players in rosters.items():
                for player in players:
                    player_data = player.copy()  # Make a copy to avoid modifying the original
                    player_data['team'] = team_name
                    roster_df.append(player_data)
            
            if roster_df:
                # Ensure roster data has the required columns
                roster_df = pd.DataFrame(roster_df)
                required_columns = ['team', 'player_name', 'position', 'team', 'status']
                for col in required_columns:
                    if col not in roster_df.columns:
                        if col == 'player_name' and 'name' in roster_df.columns:
                            roster_df['player_name'] = roster_df['name']
                        else:
                            roster_df[col] = 'Unknown'
            else:
                roster_df = pd.DataFrame()
            
            return {
                'league_data': league_info,
                'standings_data': standings,
                'roster_data': roster_df,
                'transactions': transactions,
                'scoring_periods': scoring_periods,
                'current_matchups': current_matchups,
                'live_scoring': live_scoring,
                'source': 'fantrax'
            }
    except Exception as e:
        with st.sidebar:
            st.error(f"❌ Error loading Fantrax data: {str(e)}")
        return None