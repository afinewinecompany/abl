import requests
from typing import Dict, Any, Optional
import streamlit as st
import time
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class FantraxAPI:
    def __init__(self):
        self.base_url = "https://www.fantrax.com/fxea"
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
        
        # Apply user auth if available
        self.apply_user_auth()
    
    def apply_user_auth(self):
        """Apply user authentication to the session if available"""
        if st.session_state.get("fantrax_logged_in", False):
            auth_data = st.session_state.get("fantrax_auth", {})
            if auth_data:
                # Apply cookies
                cookies = auth_data.get("cookies", {})
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)
                
                # Apply headers
                headers = auth_data.get("headers", {})
                self.session.headers.update(headers)
    
    def is_authenticated(self) -> bool:
        """Check if the current session is authenticated"""
        return st.session_state.get("fantrax_logged_in", False)

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, method="GET", data=None) -> Dict:
        """Make API request with error handling and retries"""
        url = f"{self.base_url}/{endpoint}"
        
        # Ensure we're using the latest auth data
        self.apply_user_auth()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url,
                    params=params,
                    timeout=10
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url,
                    params=params,
                    json=data,
                    timeout=10
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.warning(f"API request to {endpoint} failed: {str(e)}")
            # Return mock data based on the endpoint
            return self._get_mock_data(endpoint)
        except ValueError as e:
            st.error(f"Failed to parse JSON response from {endpoint}: {str(e)}")
            return self._get_mock_data(endpoint)

    def _get_mock_data(self, endpoint: str) -> Dict:
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
        return {}

    def get_player_ids(self) -> Dict:
        """Fetch player IDs"""
        return self._make_request("general/getPlayerIds", {"sport": "MLB"})

    def get_league_info(self) -> Dict:
        """Fetch league information"""
        return self._make_request("general/getLeagueInfo", {"leagueId": self.league_id})

    def get_team_rosters(self) -> Dict:
        """Fetch team rosters"""
        return self._make_request("general/getTeamRosters", 
                              {"leagueId": self.league_id, "period": "1"})

    def get_standings(self) -> Dict:
        """Fetch standings data"""
        return self._make_request("general/getStandings", {"leagueId": self.league_id})
        
    def get_available_players(self, 
                             position: str = None, 
                             team: str = None, 
                             sort_stat: str = None,
                             page: int = 1,
                             max_results: int = 50) -> Dict:
        """
        Fetch available players from the league
        
        Args:
            position: Filter by position code (e.g., "SP", "OF", "C")
            team: Filter by team code (e.g., "LAD", "NYY")
            sort_stat: Sort by stat category
            page: Page number for pagination
            max_results: Maximum number of results per page
            
        Returns:
            Dictionary containing available players data
        """
        # Require authentication
        if not self.is_authenticated():
            st.warning("You must be logged in to view available players")
            return {"players": []}
        
        params = {
            "leagueId": self.league_id,
            "view": "AVAILABLE",  # Available players view
            "pageNumber": page,
            "maxResultsPerPage": max_results
        }
        
        # Add filters if provided
        if position:
            params["positionOrGroup"] = position
        if team:
            params["mlbTeam"] = team
        if sort_stat:
            params["sortStat"] = sort_stat
            
        # This endpoint is slightly different than others
        return self._make_request("league/players", params)