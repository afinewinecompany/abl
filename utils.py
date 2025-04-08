import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict, List
import pandas as pd
import os
import datetime
from pathlib import Path

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
            
            # Fetch scoring periods to determine current period
            try:
                scoring_periods = api_client.get_scoring_periods()
                current_period = 1  # Default to period 1
                
                # Check if scoring_periods is properly formatted (should be a list of dicts)
                if isinstance(scoring_periods, list):
                    for period in scoring_periods:
                        # Make sure each period is a dictionary
                        if isinstance(period, dict):
                            if period.get('isActive', False) and not period.get('isCompleted', False):
                                current_period = period.get('id', 1)
                                break
                        else:
                            st.sidebar.warning(f"Unexpected period format: {type(period)}")
                elif isinstance(scoring_periods, str):
                    st.sidebar.warning(f"Received string instead of scoring periods data: {scoring_periods[:50]}...")
                else:
                    st.sidebar.warning(f"Unexpected scoring_periods format: {type(scoring_periods)}")
            except Exception as period_error:
                st.sidebar.warning(f"Error processing scoring periods: {str(period_error)}")
                current_period = 1  # Fallback to period 1

            # Clear the progress bar
            status_container.empty()

            return {
                'league_data': processed_league_data,
                'roster_data': processed_roster_data,
                'standings_data': processed_standings_data,
                'current_period': current_period
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
                
                # Process record format (e.g. "3-0-0") into actual record components
                if 'record' in df.columns:
                    record_parts = row['record'].split('-')
                    wins = int(record_parts[0]) if len(record_parts) > 0 else 0
                    losses = int(record_parts[1]) if len(record_parts) > 1 else 0
                    draws = int(record_parts[2]) if len(record_parts) > 2 else 0
                    
                    # Store the actual record components
                    result = {
                        'wins': wins,
                        'losses': losses,
                        'draws': draws,
                        'status': 'Win' if wins > losses else 'Loss' if losses > wins else 'Tie'
                    }
                else:
                    # If we have the old format with 'result' directly
                    old_result = row.get('result', 'Unknown')
                    # Create a record structure for compatibility
                    result = {
                        'wins': 1 if old_result == 'Win' else 0,
                        'losses': 1 if old_result == 'Loss' else 0,
                        'draws': 1 if old_result == 'Tie' else 0,
                        'status': old_result
                    }
                
                # Add the proper structured data to the results
                results.append({
                    'team': team,
                    'week': week,
                    'result': result['status'],  # For backward compatibility
                    'record': row.get('record', f"{result['wins']}-{result['losses']}-{result['draws']}"),
                    'weekly_wins': result['wins'],
                    'weekly_losses': result['losses'],
                    'weekly_draws': result['draws']
                })
            
            return results
        
        return []
    except Exception as e:
        st.error(f"Error loading weekly results data: {str(e)}")
        return []

def save_rankings_history(rankings_df: pd.DataFrame, ranking_type: str = "power") -> bool:
    """
    Save a snapshot of team rankings to a historical record CSV file
    
    Args:
        rankings_df: DataFrame containing the rankings data
        ranking_type: Type of ranking ('power' or 'ddi')
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory structure if it doesn't exist
        history_dir = Path('data/history')
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file path based on ranking type
        if ranking_type.lower() == 'power':
            file_path = history_dir / 'power_rankings_history.csv'
            required_columns = ['team_name', 'power_score', 'raw_power_score']
        else:  # DDI rankings
            file_path = history_dir / 'ddi_rankings_history.csv'
            required_columns = ['Team', 'DDI Score', 'Power Score', 'Prospect Score', 
                               'Historical Score', 'Playoff Score']
        
        # Verify required columns exist in the DataFrame
        missing_columns = [col for col in required_columns if col not in rankings_df.columns]
        if missing_columns:
            st.error(f"Missing required columns in rankings data: {missing_columns}")
            return False
        
        # Add date column to the data
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        rankings_df = rankings_df.copy()
        rankings_df['date'] = current_date
        
        # Add a rank column if not already present
        if 'rank' not in rankings_df.columns:
            # Add ordinal ranking (1, 2, 3, etc.)
            rankings_df['rank'] = range(1, len(rankings_df) + 1)
        
        # If file exists, append; otherwise create new
        if file_path.exists():
            # Load existing data
            existing_df = pd.read_csv(file_path)
            
            # Check if we already have data for today
            today_data = existing_df[existing_df['date'] == current_date]
            if not today_data.empty:
                # Remove today's data and append new data
                existing_df = existing_df[existing_df['date'] != current_date]
            
            # Append new data
            combined_df = pd.concat([existing_df, rankings_df])
            combined_df.to_csv(file_path, index=False)
        else:
            # Create new file
            rankings_df.to_csv(file_path, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving rankings history: {str(e)}")
        return False

def load_rankings_history(team_name: str = None, ranking_type: str = "power") -> pd.DataFrame:
    """
    Load historical rankings data, optionally filtered by team
    
    Args:
        team_name: Optional team name to filter results
        ranking_type: Type of ranking ('power' or 'ddi')
    
    Returns:
        DataFrame: Historical rankings data
    """
    try:
        # Determine file path based on ranking type
        history_dir = Path('data/history')
        if ranking_type.lower() == 'power':
            file_path = history_dir / 'power_rankings_history.csv'
            team_col = 'team_name'
        else:  # DDI rankings
            file_path = history_dir / 'ddi_rankings_history.csv'
            team_col = 'Team'
        
        # Check if file exists
        if not file_path.exists():
            return pd.DataFrame()  # Return empty DataFrame if no history exists
        
        # Load data
        df = pd.read_csv(file_path)
        
        # Convert date column to datetime for easier manipulation
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date, then by rank
        df = df.sort_values(['date', 'rank'])
        
        # Filter by team if specified
        if team_name is not None:
            df = df[df[team_col] == team_name]
        
        return df
    except Exception as e:
        st.error(f"Error loading rankings history: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_ranking_trend_chart(team_name: str, ranking_type: str = "power") -> pd.DataFrame:
    """
    Create a chart showing a team's ranking trend over time
    
    Args:
        team_name: Name of the team to show trend for
        ranking_type: Type of ranking ('power' or 'ddi')
    
    Returns:
        DataFrame: Processed data ready for plotting
    """
    try:
        # Load team's historical data
        df = load_rankings_history(team_name, ranking_type)
        
        if df.empty:
            return df  # Return empty DataFrame if no history exists
        
        # Determine score column based on ranking type
        if ranking_type.lower() == 'power':
            score_col = 'power_score'
        else:  # DDI rankings
            score_col = 'DDI Score'
        
        # Process data for plotting - keep date and score columns
        plot_df = df[['date', score_col, 'rank']].copy()
        
        # Ensure dates are sorted
        plot_df = plot_df.sort_values('date')
        
        return plot_df
    except Exception as e:
        st.error(f"Error creating ranking trend chart: {str(e)}")
        return pd.DataFrame()

def should_take_weekly_snapshot() -> bool:
    """
    Determine if we should take a weekly snapshot of rankings
    Returns True if today is Sunday or if no snapshot exists yet
    """
    try:
        # Check if today is Sunday (weekday 6 is Sunday)
        is_sunday = datetime.datetime.now().weekday() == 6
        
        # Check if history directories/files exist
        power_history = Path('data/history/power_rankings_history.csv')
        ddi_history = Path('data/history/ddi_rankings_history.csv')
        
        # Return True if it's Sunday or if no history exists yet
        return is_sunday or not (power_history.exists() and ddi_history.exists())
    except Exception:
        # If there's an error, default to False to be safe
        return False

