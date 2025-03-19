import requests
from typing import Dict, Any, List, Union
import streamlit as st
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class FantraxAPI:
    def __init__(self):
        self.base_url = "https://www.fantrax.com/fxea/general"
        self.league_id = "grx2lginm1v4p5jd"

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
        )

        # Create session with retry strategy
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Union[Dict, List]:
        """Make API request with error handling and retries"""
        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Validate response data
            if data is None:
                raise ValueError(f"No data received from {endpoint}")

            return data
        except requests.exceptions.RequestException as e:
            # Return mock data based on the endpoint
            return self._get_mock_data(endpoint)
        except (ValueError, TypeError) as e:
            # Return mock data if JSON parsing fails or data is invalid
            return self._get_mock_data(endpoint)

    def _get_mock_data(self, endpoint: str) -> Union[Dict, List]:
        """Return mock data for development when API is unavailable"""
        if endpoint == "getLeagueInfo":
            return {
                "draftSettings": {},
                "scoringSettings": {
                    "scoringPeriod": "Weekly"
                },
                "name": "ABL Development",
                "season": "2025",
                "teams": 30,
                "sport": "MLB"
            }
        elif endpoint == "getPlayerIds":
            return {"player1": {"name": "Test Player", "team": "Test Team"}}
        elif endpoint == "getTeamRosters":
            return {
                "rosters": {
                    "team1": {
                        "teamName": "Test Team",
                        "rosterItems": [
                            {
                                "id": "player1",
                                "name": "Test Player",
                                "position": "OF",
                                "status": "Active",
                                "salary": 10
                            }
                        ]
                    }
                }
            }
        elif endpoint == "getStandings":
            return [
                {
                    "teamName": "Test Team",
                    "teamId": "team1",
                    "rank": 1,
                    "points": "10-5-0",
                    "winPercentage": 0.667,
                    "gamesBack": 0.0
                }
            ]
        return {} if endpoint != "getStandings" else []

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

    def get_standings(self) -> List:
        """Fetch standings data"""
        return self._make_request("getStandings", {"leagueId": self.league_id})