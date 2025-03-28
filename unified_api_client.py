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
                return fantrax_standings
            
            # Fall back to original API if Fantrax data is unavailable
            original_standings = _self._original_api.get_standings()
            return _self._data_processor.process_standings(original_standings)
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
                        roster_df.append(player_data)
            
            if roster_df:
                # Convert to DataFrame
                roster_df = pd.DataFrame(roster_df)
                
                # Ensure required columns exist
                required_columns = ['team', 'player_name', 'position', 'status']
                for col in required_columns:
                    if col not in roster_df.columns:
                        if col == 'player_name' and 'name' in roster_df.columns:
                            roster_df['player_name'] = roster_df['name']
                        else:
                            roster_df[col] = 'Unknown'
                
                return roster_df
            
            # If no data from Fantrax, fall back to original API
            roster_data = _self._original_api.get_team_rosters()
            player_ids = _self._original_api.get_player_ids()
            return _self._data_processor.process_rosters(roster_data, player_ids)
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
    
    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all data at once and return as a consolidated dictionary."""
        try:
            # Create a placeholder in the sidebar for a loading indicator
            with st.sidebar:
                status_container = st.empty()
                status_container.progress(0)
            
            # Fetch and process all data
            status_container.progress(20)
            league_info = self.get_league_info()
            
            status_container.progress(40)
            standings = self.get_standings()
            
            status_container.progress(60)
            roster_data = self.get_team_rosters()
            
            status_container.progress(75)
            transactions = self.get_transactions()
            
            status_container.progress(85)
            scoring_periods = self.get_scoring_periods()
            
            status_container.progress(95)
            current_matchups = self.get_matchups_for_period()
            
            # Clear the progress bar
            status_container.empty()
            
            return {
                'league_data': league_info,
                'standings_data': standings,
                'roster_data': roster_data,
                'transactions': transactions,
                'scoring_periods': scoring_periods,
                'current_matchups': current_matchups
            }
        except Exception as e:
            with st.sidebar:
                st.error(f"❌ Error loading data: {str(e)}")
            return None

# Initialize a global instance of the unified client
unified_client = UnifiedAPIClient()