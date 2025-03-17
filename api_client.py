import requests
from typing import Dict, Any
import streamlit as st

class FantraxAPI:
    def __init__(self, league_id: str = None):
        self.base_url = "https://www.fantrax.com/fxea/general"
        self.league_id = league_id

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make API request with error handling"""
        try:
            if params is None:
                params = {}

            # Add required parameters
            if endpoint in ['getLeagueInfo', 'getTeamRosters', 'getStandings']:
                if not self.league_id:
                    raise ValueError("League ID is required")
                params['leagueId'] = self.league_id

            if endpoint == 'getPlayerIds':
                params['sport'] = 'MLB'

            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid league ID or data format: {str(e)}")

    def get_player_ids(self) -> Dict:
        """Fetch player IDs"""
        return self._make_request("getPlayerIds")

    def get_league_info(self) -> Dict:
        """Fetch league information"""
        return self._make_request("getLeagueInfo")

    def get_team_rosters(self) -> Dict:
        """Fetch team rosters"""
        return self._make_request("getTeamRosters", {"period": "1"})

    def get_standings(self) -> Dict:
        """Fetch standings data"""
        return self._make_request("getStandings")