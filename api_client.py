import requests
from typing import Dict, Any
import streamlit as st

class FantraxAPI:
    def __init__(self):
        self.base_url = "https://www.fantrax.com/fxea/general"
        self.league_id = "grx2lginm1v4p5jd"

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make API request with error handling"""
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
        except ValueError as e:
            st.error(f"Failed to parse JSON response: {str(e)}")
            raise Exception(f"Failed to parse JSON response: {str(e)}")

    def get_player_ids(self) -> Dict:
        """Fetch player IDs"""
        return self._make_request("getPlayerIds", {"sport": "MLB"})

    def get_league_info(self) -> Dict:
        """Fetch league information"""
        return self._make_request("getLeagueInfo", {"leagueId": self.league_id})

    def get_team_rosters(self) -> Dict:
        """Fetch team rosters"""
        return self._make_request("getTeamRosters", 
                                {"leagueId": self.league_id, "period": "1"})

    def get_standings(self) -> Dict:
        """Fetch standings data"""
        return self._make_request("getStandings", {"leagueId": self.league_id})