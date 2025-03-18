import streamlit as st
from api_client import FantraxAPI
from data_processor import DataProcessor
from typing import Any, Dict
import pandas as pd
import time
import unicodedata

@st.cache_data
def fetch_api_data(_status_container=None):
    """
    Fetch all required data from API and process it.
    Returns processed data or None if an error occurs.
    """
    try:
        # Initialize API client and data processor
        api_client = FantraxAPI()
        data_processor = DataProcessor()

        def update_status(message):
            """Helper to update status with animation"""
            if _status_container:
                _status_container.markdown(
                    f'<div class="status-container visible">{message}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(0.1)  # Small delay for visual feedback

        # Fetch all required data with status updates
        update_status("⌛ Initializing data fetch...")

        update_status("📊 Loading league information...")
        league_data = api_client.get_league_info()

        update_status("👥 Loading team rosters...")
        roster_data = api_client.get_team_rosters()

        update_status("🏆 Loading standings...")
        standings_data = api_client.get_standings()

        update_status("🎯 Loading player details...")
        player_ids = api_client.get_player_ids()

        # Process data
        update_status("⚙️ Processing data...")
        processed_league_data = data_processor.process_league_info(league_data)
        processed_roster_data = data_processor.process_rosters(roster_data, player_ids)
        processed_standings_data = data_processor.process_standings(standings_data)

        # Clear status container
        if _status_container:
            _status_container.markdown(
                '<div class="status-container">Data loaded successfully!</div>',
                unsafe_allow_html=True
            )
            time.sleep(1)  # Show success message briefly
            _status_container.empty()

        return {
            'league_data': processed_league_data,
            'roster_data': processed_roster_data,
            'standings_data': processed_standings_data
        }
    except Exception as e:
        if _status_container:
            _status_container.markdown(
                f'<div class="status-container visible">❌ Error: {str(e)}</div>',
                unsafe_allow_html=True
            )
            time.sleep(3)  # Show error message for longer
        return None

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        # Return empty string for None or empty values
        if name is None or name == '' or isinstance(name, float):
            return ""

        # Convert to string and normalize
        name_str = str(name).strip().lower()

        # Handle empty string after stripping
        if not name_str:
            return ""

        # Normalize unicode characters
        name_str = unicodedata.normalize('NFKD', name_str).encode('ASCII', 'ignore').decode('ASCII')

        # Handle comma-separated names (Last, First)
        if ',' in name_str:
            last, first = name_str.split(',', 1)
            name_str = f"{first.strip()} {last.strip()}"

        # Remove parenthetical content and metadata
        name_str = name_str.split('(')[0].strip()
        name_str = name_str.split(' - ')[0].strip()

        # Clean up periods and extra spaces
        name_str = name_str.replace('.', '').strip()
        name_str = ' '.join(name_str.split())

        return name_str
    except Exception as e:
        st.error(f"Error normalizing name '{name}': {str(e)}")
        return str(name).strip() if name else ""

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