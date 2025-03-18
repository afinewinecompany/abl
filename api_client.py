import requests
from typing import Dict, Any
import streamlit as st
import time
import logging

logger = logging.getLogger(__name__)

class FantraxAPI:
    def __init__(self):
        self.base_url = "https://www.fantrax.com/fxea/general"
        self.league_id = "grx2lginm1v4p5jd"
        self.max_retries = 3
        self.timeout = 10
        self.retry_delay = 2

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make API request with error handling and retries"""
        attempts = 0
        last_exception = None

        while attempts < self.max_retries:
            try:
                logger.debug(f"Making API request to {endpoint} (attempt {attempts + 1})")
                response = requests.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempts + 1} for {endpoint}")
                last_exception = "Connection timed out. Please try again later."
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempts + 1} for {endpoint}")
                last_exception = "Could not connect to Fantrax. Please check your internet connection."
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 524:
                    logger.error(f"Fantrax API unavailable (524 error) on attempt {attempts + 1}")
                    last_exception = "Fantrax API is currently unavailable. Using cached data."
                    return self._get_mock_data(endpoint)
                else:
                    logger.error(f"HTTP error {e.response.status_code} on attempt {attempts + 1}")
                    last_exception = f"HTTP error: {e.response.status_code}"
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempts + 1}: {str(e)}")
                last_exception = str(e)

            attempts += 1
            if attempts < self.max_retries:
                time.sleep(self.retry_delay)

        logger.error(f"All attempts failed for {endpoint}: {last_exception}")
        return self._get_mock_data(endpoint)

    def _get_mock_data(self, endpoint: str) -> Dict:
        """Return mock data for development when API is unavailable"""
        if endpoint == "getLeagueInfo":
            return {
                "name": "ABL Season 5",
                "season": "2025",
                "sport": "MLB",
                "scoringType": "Head to Head",
                "teams": 30,
                "scoringPeriod": "Weekly"
            }
        elif endpoint == "getTeamRosters":
            return {"rosters": {}}  # Empty rosters as fallback
        elif endpoint == "getStandings":
            return []  # Empty standings as fallback
        elif endpoint == "getPlayerIds":
            return {}  # Empty player IDs as fallback
        return {}

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