import os
import pickle
import time
import json
from typing import Dict, List, Any, Union
import traceback
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the FantraxAPI library
try:
    from fantraxapi import Fantrax
    from fantraxapi.exceptions import FantraxException
except ImportError:
    logger.error("Failed to import FantraxAPI. Please ensure the module is installed.")

class FantraxAPI:
    def __init__(self):
        self.client = None
        self.league_id = os.getenv('LEAGUE_ID', '0dw16pjfkmoc')  # Default to test league if not specified
        self.mock_mode = False  # Default to real API mode
        
        # Try to initialize the client
        self.init_fantrax_client()

    def init_fantrax_client(self):
        """Initialize the official Fantrax API client with authentication"""
        try:
            # Check if cookie file exists
            if os.path.exists("fantraxloggedin.cookie"):
                logger.info("Using existing fantraxloggedin.cookie file")
                cookies = pickle.load(open("fantraxloggedin.cookie", "rb"))
                
                # Initialize the Fantrax API client
                self.client = Fantrax(cookies=cookies)
                logger.info("Fantrax API client initialized successfully")
                self.mock_mode = False
            else:
                logger.warning("No cookie file found. Falling back to mock mode.")
                self.mock_mode = True
        except Exception as e:
            logger.error(f"Error initializing Fantrax client: {str(e)}")
            logger.error(traceback.format_exc())
            self.mock_mode = True
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Make API request with error handling and retries"""
        if self.mock_mode:
            return self._get_mock_data(endpoint)
            
        if self.client is None:
            # Try to initialize client again
            self.init_fantrax_client()
            if self.client is None:
                logger.error("Fantrax client is not initialized")
                return self._get_mock_data(endpoint)
        
        try:
            # For now, just route to the appropriate API method
            if endpoint == "getLeagueInfo":
                return self.client.get_league(self.league_id)
            elif endpoint == "getTeamRosters":
                return self.client.get_league_rosters(self.league_id)
            elif endpoint == "getStandings":
                return self.client.get_league_standings(self.league_id)
            elif endpoint == "getScoringPeriods":
                return self.client.get_scoring_periods(self.league_id)
            elif endpoint == "getMatchups":
                return self.client.get_league_schedule(self.league_id)
            elif endpoint == "getTransactions":
                return self.client.get_league_messages(self.league_id)
            elif endpoint == "getTeams":
                return self.client.get_league_teams(self.league_id)
            else:
                logger.error(f"Unknown endpoint: {endpoint}")
                return self._get_mock_data(endpoint)
                
        except FantraxException as e:
            logger.error(f"Fantrax API error for endpoint {endpoint}: {str(e)}")
            return self._get_mock_data(endpoint)
        except Exception as e:
            logger.error(f"Unexpected error for endpoint {endpoint}: {str(e)}")
            logger.error(traceback.format_exc())
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Return mock data for development when API is unavailable"""
        logger.warning(f"Using mock data for endpoint: {endpoint}")
        
        # Create path to mock data file
        mock_file = f"mock_data/{endpoint}.json"
        
        # Check if the mock data directory exists, if not create it
        if not os.path.exists("mock_data"):
            os.makedirs("mock_data")
            
        # Check if specific mock file exists
        if os.path.exists(mock_file):
            # Return the saved mock data
            try:
                with open(mock_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading mock data: {str(e)}")
        
        # If we got here, either the file doesn't exist or couldn't be loaded
        # Return placeholder mock data
        if endpoint == "getLeagueInfo":
            return {"id": self.league_id, "name": "Mock League", "scoringStyle": "H2H"}
        elif endpoint == "getTeamRosters":
            return {"rosters": [
                {"teamId": "1", "teamName": "Mock Team 1", "players": []},
                {"teamId": "2", "teamName": "Mock Team 2", "players": []}
            ]}
        elif endpoint == "getStandings":
            return [
                {"teamId": "1", "teamName": "Mock Team 1", "wins": 5, "losses": 2, "points": 450.5},
                {"teamId": "2", "teamName": "Mock Team 2", "wins": 3, "losses": 4, "points": 380.2}
            ]
        elif endpoint == "getScoringPeriods":
            return [
                {"id": 1, "startDate": "2025-04-01", "endDate": "2025-04-07", "isCurrent": True},
                {"id": 2, "startDate": "2025-04-08", "endDate": "2025-04-14", "isCurrent": False}
            ]
        elif endpoint == "getMatchups":
            return [
                {"periodId": 1, "homeTeamId": "1", "awayTeamId": "2", "homeScore": 150.5, "awayScore": 130.2}
            ]
        elif endpoint == "getTransactions":
            return [
                {"id": "1", "date": "2025-03-28", "type": "TRADE", "description": "Mock Trade"}
            ]
        elif endpoint == "getTeams":
            return [
                {"id": "1", "name": "Mock Team 1", "owner": "Owner 1"},
                {"id": "2", "name": "Mock Team 2", "owner": "Owner 2"}
            ]
        else:
            return {}
            
    def get_player_ids(self) -> Dict[str, Any]:
        """Fetch player IDs"""
        return self._make_request("getPlayerIds")
        
    def get_league_info(self) -> Dict[str, Any]:
        """Fetch league information"""
        return self._make_request("getLeagueInfo")
        
    def get_team_rosters(self) -> Dict[str, Any]:
        """Fetch team rosters"""
        return self._make_request("getTeamRosters")
        
    def get_standings(self) -> List[Dict[str, Any]]:
        """Fetch standings data"""
        return self._make_request("getStandings")
        
    def get_scoring_periods(self) -> List[Dict[str, Any]]:
        """Fetch scoring periods"""
        return self._make_request("getScoringPeriods")
        
    def get_matchups(self, period_id: int = 1) -> List[Dict[str, Any]]:
        """Fetch matchups for a specific period"""
        return self._make_request("getMatchups", {"periodId": period_id})
        
    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent transactions"""
        return self._make_request("getTransactions", {"limit": limit})
        
    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all teams"""
        return self._make_request("getTeams")