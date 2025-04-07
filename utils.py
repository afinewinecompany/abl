import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict, List
import pandas as pd
import os

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
        'mean': df[column].mean() if not df[column].empty else 0,
        'median': df[column].median() if not df[column].empty else 0,
        'max': df[column].max() if not df[column].empty else 0,
        'min': df[column].min() if not df[column].empty else 0
    }

def save_power_rankings_data(data: dict, file_path: str = 'data/team_season_stats.csv') -> bool:
    """
    Save power rankings data to a CSV file
    
    Args:
        data: Dictionary containing team data with 'fptsf' (or 'total_points') and 'weeks_played'
        file_path: Path to save the CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert dictionary to DataFrame for easy CSV writing
        rows = []
        for team_name, team_data in data.items():
            # Use fptsf key if available, otherwise fall back to total_points
            points = team_data.get('fptsf', team_data.get('total_points', 0))
            
            rows.append({
                'team': team_name,
                'fptsf': points,
                'weeks_played': team_data.get('weeks_played', 0)
            })
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False)
            return True
        
        return False
    except Exception as e:
        st.error(f"Error saving power rankings data: {str(e)}")
        return False

def load_power_rankings_data(file_path: str = 'data/team_season_stats.csv') -> dict:
    """
    Load power rankings data from a CSV file
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        dict: Dictionary containing team data
    """
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to dictionary format expected by the app
            data = {}
            for _, row in df.iterrows():
                # Check which format of data we have (fptsf or total_points)
                if 'fptsf' in row:
                    points_key = 'fptsf'
                else:
                    points_key = 'total_points'
                
                data[row['team']] = {
                    'fptsf': float(row[points_key]),
                    'total_points': float(row[points_key]),  # Keep both for compatibility
                    'weeks_played': int(row['weeks_played'])
                }
            
            return data
        
        return {}
    except Exception as e:
        st.error(f"Error loading power rankings data: {str(e)}")
        return {}

def save_weekly_results(data: list, file_path: str = 'data/weekly_results.csv') -> bool:
    """
    Save weekly results data to a CSV file
    
    Args:
        data: List of weekly results dictionaries
        file_path: Path to save the CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if data:
            # Convert to expected format (team, week number, record)
            rows = []
            for item in data:
                # Check if the data is already in the expected format
                if 'record' in item:
                    # Keep the existing record format
                    rows.append({
                        'team': item['team'],
                        'week number': item.get('week', item.get('week number', 0)),
                        'record': item['record']
                    })
                else:
                    # Convert Win/Loss to a record format (e.g., "3-0-0")
                    result = item.get('result', '')
                    if result == 'Win':
                        record = '1-0-0'
                    elif result == 'Loss':
                        record = '0-1-0'
                    else:
                        record = '0-0-0'
                    
                    rows.append({
                        'team': item['team'],
                        'week number': item.get('week', 0),
                        'record': record
                    })
            
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False)
            return True
        
        return False
    except Exception as e:
        st.error(f"Error saving weekly results data: {str(e)}")
        return False

def load_weekly_results(file_path: str = 'data/weekly_results.csv') -> list:
    """
    Load weekly results data from a CSV file
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        list: List of weekly results dictionaries with 'team', 'week', and 'result' (Win/Loss)
    """
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Process the data
            results = []
            for _, row in df.iterrows():
                team = row['team']
                
                # Handle 'week number' or 'week' column
                week_col = 'week number' if 'week number' in df.columns else 'week'
                week = int(row[week_col])
                
                # Process record format (e.g. "3-0-0") into Win/Loss
                if 'record' in df.columns:
                    record = row['record'].split('-')
                    wins = int(record[0]) if len(record) > 0 else 0
                    losses = int(record[1]) if len(record) > 1 else 0
                    
                    # Determine Win/Loss status
                    result = 'Win' if wins > losses else 'Loss' if losses > wins else 'Tie'
                else:
                    # If we have the old format with 'result' directly
                    result = row.get('result', 'Unknown')
                
                results.append({
                    'team': team,
                    'week': week,
                    'result': result,
                    'record': row.get('record', f"{1 if result == 'Win' else 0}-{1 if result == 'Loss' else 0}-{1 if result == 'Tie' else 0}")
                })
            
            return results
        
        return []
    except Exception as e:
        st.error(f"Error loading weekly results data: {str(e)}")
        return []

