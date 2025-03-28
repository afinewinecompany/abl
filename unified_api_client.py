import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from api_client import FantraxAPI
from fantrax_integration import FantraxAPIWrapper
from data_processor import DataProcessor

class UnifiedAPIClient:
    """
    Unified API client that combines functionality from both the original FantraxAPI
    and the new FantraxAPIWrapper to provide a single consistent interface for all data.
    """
    def __init__(self, league_id: str = "grx2lginm1v4p5jd"):
        """Initialize both API clients with the league ID."""
        self.league_id = league_id
        self._original_api = FantraxAPI()
        self._fantrax_wrapper = FantraxAPIWrapper(league_id)
        self._data_processor = DataProcessor()
        self._cache = {}
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_league_info(_self) -> Dict[str, Any]:
        """Get comprehensive league information from both APIs."""
        try:
            # Get league info from both sources
            original_league_info = _self._original_api.get_league_info()
            fantrax_league_info = _self._fantrax_wrapper.get_league_info()
            
            # Process the original API data
            processed_league_info = _self._data_processor.process_league_info(original_league_info)
            
            # Merge with Fantrax data (Fantrax data takes precedence when keys overlap)
            for key, value in fantrax_league_info.items():
                processed_league_info[key] = value
            
            return processed_league_info
        except Exception as e:
            st.error(f"Failed to fetch league info: {str(e)}")
            return {}
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_standings(_self) -> pd.DataFrame:
        """Get current standings from both APIs."""
        try:
            # Try to get standings from Fantrax first (more reliable)
            fantrax_standings = _self._fantrax_wrapper.get_standings()
            
            if not fantrax_standings.empty:
                # Normalize column names to ensure compatibility
                if 'team' in fantrax_standings.columns and 'team_name' not in fantrax_standings.columns:
                    fantrax_standings['team_name'] = fantrax_standings['team']
                if 'win_percentage' in fantrax_standings.columns and 'winning_pct' not in fantrax_standings.columns:
                    fantrax_standings['winning_pct'] = fantrax_standings['win_percentage']
                # Ensure games_back is present
                if 'games_back' not in fantrax_standings.columns:
                    fantrax_standings['games_back'] = 0.0
                
                return fantrax_standings
            
            # Fall back to original API if Fantrax data is unavailable
            original_standings = _self._original_api.get_standings()
            processed_standings = _self._data_processor.process_standings(original_standings)
            
            # Normalize column names for original API data too
            if 'team_name' not in processed_standings.columns and 'team' in processed_standings.columns:
                processed_standings['team_name'] = processed_standings['team']
            if 'winning_pct' not in processed_standings.columns and 'win_percentage' in processed_standings.columns:
                processed_standings['winning_pct'] = processed_standings['win_percentage']
            
            return processed_standings
        except Exception as e:
            st.error(f"Failed to fetch standings: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_team_rosters(_self) -> pd.DataFrame:
        """Get roster data from both APIs and combine into a single DataFrame."""
        try:
            # First try to get roster data from Fantrax API
            fantrax_rosters = _self._fantrax_wrapper.get_team_rosters()
            roster_df = []
            
            if fantrax_rosters:
                # Convert the dictionary format to DataFrame
                for team_name, players in fantrax_rosters.items():
                    for player in players:
                        player_data = player.copy()
                        player_data['team'] = team_name
                        player_data['team_name'] = team_name  # Ensure team_name exists
                        roster_df.append(player_data)
            
            if roster_df:
                # Convert to DataFrame
                roster_df = pd.DataFrame(roster_df)
                
                # Ensure required columns exist
                required_columns = ['team', 'team_name', 'player_name', 'position', 'status']
                for col in required_columns:
                    if col not in roster_df.columns:
                        if col == 'player_name' and 'name' in roster_df.columns:
                            roster_df['player_name'] = roster_df['name']
                        elif col == 'team_name' and 'team' in roster_df.columns:
                            roster_df['team_name'] = roster_df['team']
                        else:
                            roster_df[col] = 'Unknown'
                
                return roster_df
            
            # If no data from Fantrax, fall back to original API
            roster_data = _self._original_api.get_team_rosters()
            player_ids = _self._original_api.get_player_ids()
            processed_roster_data = _self._data_processor.process_rosters(roster_data, player_ids)
            
            # Ensure team_name exists in the original API data
            if 'team_name' not in processed_roster_data.columns and 'team' in processed_roster_data.columns:
                processed_roster_data['team_name'] = processed_roster_data['team']
            
            return processed_roster_data
        except Exception as e:
            st.error(f"Failed to fetch team rosters: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_transactions(_self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions."""
        try:
            # Get transactions from Fantrax API
            return _self._fantrax_wrapper.get_transactions(limit)
        except Exception as e:
            st.error(f"Failed to fetch transactions: {str(e)}")
            return []
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_scoring_periods(_self) -> List[Dict[str, Any]]:
        """Get scoring periods information."""
        try:
            # Get scoring periods from Fantrax API
            return _self._fantrax_wrapper.get_scoring_periods()
        except Exception as e:
            st.error(f"Failed to fetch scoring periods: {str(e)}")
            return []
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_matchups_for_period(_self, period_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matchups for a specific scoring period."""
        try:
            return _self._fantrax_wrapper.get_matchups_for_period(period_id)
        except Exception as e:
            st.error(f"Failed to fetch matchups: {str(e)}")
            return []
    
    def fetch_all_data(_self) -> Dict[str, Any]:
        """Fetch all data at once and return as a consolidated dictionary."""
        try:
            # Create a placeholder in the sidebar for a loading indicator
            with st.sidebar:
                status_container = st.empty()
                status_container.progress(0)
            
            result = {}
            
            # Fetch and process all data with error handling for each step
            try:
                status_container.progress(20)
                league_info = _self.get_league_info()
                result['league_data'] = league_info
            except Exception as e:
                st.warning(f"Error loading league info: {str(e)}")
                result['league_data'] = {}
            
            try:
                status_container.progress(40)
                standings = _self.get_standings()
                result['standings_data'] = standings
            except Exception as e:
                st.warning(f"Error loading standings: {str(e)}")
                result['standings_data'] = pd.DataFrame()
            
            try:
                status_container.progress(60)
                roster_data = _self.get_team_rosters()
                result['roster_data'] = roster_data
            except Exception as e:
                st.warning(f"Error loading roster data: {str(e)}")
                result['roster_data'] = pd.DataFrame()
            
            try:
                status_container.progress(75)
                transactions = _self.get_transactions()
                result['transactions'] = transactions
            except Exception as e:
                st.warning(f"Error loading transactions: {str(e)}")
                result['transactions'] = []
            
            try:
                status_container.progress(85)
                scoring_periods = _self.get_scoring_periods()
                result['scoring_periods'] = scoring_periods
            except Exception as e:
                st.warning(f"Error loading scoring periods: {str(e)}")
                result['scoring_periods'] = []
            
            try:
                status_container.progress(95)
                current_matchups = _self.get_matchups_for_period()
                result['current_matchups'] = current_matchups
            except Exception as e:
                st.warning(f"Error loading matchups: {str(e)}")
                result['current_matchups'] = []
            
            # Clear the progress bar
            status_container.empty()
            
            # If we have at least some data, return it
            if result.get('roster_data') is not None and not result['roster_data'].empty:
                return result
            
            # As a last resort, try just returning the league data
            if result.get('league_data'):
                return result
                
            # If we have no data at all, return an empty dict so components have something to work with
            if not any(result.values()):
                st.error("No data could be loaded from any source.")
                return {
                    'league_data': {},
                    'standings_data': pd.DataFrame(),
                    'roster_data': pd.DataFrame(),
                    'transactions': [],
                    'scoring_periods': [],
                    'current_matchups': []
                }
                
            return result
        except Exception as e:
            with st.sidebar:
                st.error(f"❌ Error loading data: {str(e)}")
            
            # Return empty dataset as a fallback
            return {
                'league_data': {},
                'standings_data': pd.DataFrame(),
                'roster_data': pd.DataFrame(),
                'transactions': [],
                'scoring_periods': [],
                'current_matchups': []
            }

# Initialize a global instance of the unified client
unified_client = UnifiedAPIClient()