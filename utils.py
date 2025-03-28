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
            
            # Fetch current matchups with error handling and multiple fallbacks
            status_container.progress(95)
            try:
                # First attempt: Try to fetch current period matchups
                current_matchups = fantrax_client.get_matchups_for_period()
                
                # Validate the matchups format
                if not current_matchups or not isinstance(current_matchups, list) or len(current_matchups) == 0:
                    # Second attempt: Try to fetch period 1 matchups (Week 1)
                    st.warning("No matchups found for current period, trying Week 1...")
                    current_matchups = fantrax_client.get_matchups_for_period(1)
                    
                # Final validation with detailed warning
                if not current_matchups or not isinstance(current_matchups, list) or len(current_matchups) == 0:
                    st.warning("No matchups found in any period. The matchups tab may not display correctly.")
            except Exception as e:
                st.warning(f"Warning: Could not fetch matchups: {str(e)}")
                current_matchups = []
                
            # Ensure matchups are in the correct format regardless of source
            formatted_matchups = []
            if current_matchups and isinstance(current_matchups, list):
                for matchup in current_matchups:
                    if isinstance(matchup, dict):
                        # Check if matchup has the minimum required fields
                        has_away_team = 'away_team' in matchup or 'awayTeam' in matchup
                        has_home_team = 'home_team' in matchup or 'homeTeam' in matchup
                        
                        if has_away_team and has_home_team:
                            # Extract basic fields, using fallbacks if needed
                            away_team = matchup.get('away_team', matchup.get('awayTeam', {}).get('name', 'Unknown Team'))
                            home_team = matchup.get('home_team', matchup.get('homeTeam', {}).get('name', 'Unknown Team'))
                            
                            # Handle scores with fallbacks
                            try:
                                away_score = float(matchup.get('away_score', matchup.get('awayScore', 0)))
                            except (TypeError, ValueError):
                                away_score = 0
                                
                            try:
                                home_score = float(matchup.get('home_score', matchup.get('homeScore', 0)))
                            except (TypeError, ValueError):
                                home_score = 0
                            
                            # Determine winner/loser
                            if away_score > home_score:
                                winner = away_team
                                loser = home_team
                            elif home_score > away_score:
                                winner = home_team
                                loser = away_team
                            else:
                                winner = "Tie"
                                loser = "Tie"
                            
                            # Create properly formatted matchup
                            formatted_matchup = {
                                'away_team': away_team,
                                'away_score': away_score,
                                'home_team': home_team,
                                'home_score': home_score,
                                'winner': winner,
                                'loser': loser,
                                'score_difference': abs(away_score - home_score),
                                'period_id': matchup.get('period_id', 1),
                                'matchup_id': matchup.get('id', str(len(formatted_matchups)))
                            }
                            formatted_matchups.append(formatted_matchup)
                
                current_matchups = formatted_matchups  # Replace with properly formatted matchups
            
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
                'source': 'fantrax'
            }
    except Exception as e:
        with st.sidebar:
            st.error(f"❌ Error loading Fantrax data: {str(e)}")
        return None