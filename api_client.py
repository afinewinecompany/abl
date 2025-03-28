import os
import pickle
import time
import json
from typing import Dict, List, Any, Union
import traceback
import logging
import pandas as pd
from requests import Session

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the FantraxAPI library
from fantraxapi.fantrax import FantraxAPI as Fantrax
from fantraxapi.exceptions import FantraxException

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
                
                # Create a session with cookies
                session = Session()
                session.cookies.update(cookies)
                
                # Initialize the Fantrax API client with the session
                self.client = Fantrax(league_id=self.league_id, session=session)
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
        # Initialize params as empty dict if None
        if params is None:
            params = {}
            
        if self.mock_mode:
            return self._get_mock_data(endpoint)
            
        if self.client is None:
            # Try to initialize client again
            self.init_fantrax_client()
            if self.client is None:
                logger.error("Fantrax client is not initialized")
                return self._get_mock_data(endpoint)
        
        try:
            # Map our endpoint names to actual FantraxAPI methods
            if endpoint == "getLeagueInfo":
                # We don't have a direct method for league info, so use standings data
                standings = self.client.standings()
                return {'id': self.league_id, 'name': 'Fantrax League'}
            elif endpoint == "getTeamRosters":
                # Extract roster data from teams
                rosters = {}
                for team in self.client.teams:
                    roster_info = self.client.roster_info(team.team_id)
                    player_list = []
                    # Extract player data from roster rows
                    for row in roster_info.rows:
                        if row.player:
                            player_data = {
                                'id': row.player.scorer_id if hasattr(row.player, 'scorer_id') else '',
                                'name': str(row.player),
                                'position': row.pos.short_name if hasattr(row.pos, 'short_name') else '',
                                'status': 'ACTIVE' if row.pos_id != '0' and row.pos_id != '-1' else 'RESERVE',
                                'points': row.fppg if row.fppg else 0.0
                            }
                            player_list.append(player_data)
                    
                    rosters[team.team_id] = {
                        'teamId': team.team_id,
                        'teamName': team.name,
                        'players': player_list
                    }
                return {'rosters': list(rosters.values())}
            elif endpoint == "getStandings":
                # Get standings data
                standings_data = self.client.standings()
                standings_list = []
                
                # The ranks property contains team rankings
                for rank, record in standings_data.ranks.items():
                    team_data = {
                        'teamId': record.team.team_id,
                        'teamName': record.team.name,
                        'wins': record.win,
                        'losses': record.loss,
                        'ties': record.tie if record.tie else 0,
                        'rank': rank,
                        'winPercentage': record.win_percentage if record.win_percentage else 0.0,
                        'points': record.points_for if record.points_for else 0.0
                    }
                    standings_list.append(team_data)
                return standings_list
            elif endpoint == "getScoringPeriods":
                # Get scoring periods
                scoring_periods = self.client.scoring_periods()
                periods_list = []
                for period_id, period in scoring_periods.items():
                    period_data = {
                        'id': period_id,
                        'startDate': str(period.start),
                        'endDate': str(period.end),
                        'isCurrent': period.current
                    }
                    periods_list.append(period_data)
                return periods_list
            elif endpoint == "getMatchups":
                # Get matchups from scoring periods
                period_id = params.get('periodId', 1)
                scoring_periods = self.client.scoring_periods()
                if period_id in scoring_periods:
                    matchups = []
                    for matchup in scoring_periods[period_id].matchups:
                        # Handle both team objects and string names
                        home_team_id = matchup.home.team_id if hasattr(matchup.home, 'team_id') else "0"
                        away_team_id = matchup.away.team_id if hasattr(matchup.away, 'team_id') else "0"
                        
                        # Get team names if available
                        home_name = matchup.home.name if hasattr(matchup.home, 'name') else str(matchup.home)
                        away_name = matchup.away.name if hasattr(matchup.away, 'name') else str(matchup.away)
                        
                        matchup_data = {
                            'periodId': period_id,
                            'homeTeamId': home_team_id,
                            'awayTeamId': away_team_id,
                            'homeTeamName': home_name,
                            'awayTeamName': away_name,
                            'homeScore': matchup.home_score,
                            'awayScore': matchup.away_score
                        }
                        matchups.append(matchup_data)
                    return matchups
                return []
            elif endpoint == "getTransactions":
                # Get transactions
                transactions_data = self.client.transactions(count=params.get('limit', 50))
                transactions_list = []
                for transaction in transactions_data:
                    # Build description from players list and team
                    player_names = [str(p) for p in transaction.players]
                    description = f"{transaction.team.name}: {', '.join(player_names)}"
                    
                    # Try to infer transaction type from players
                    tx_type = "UNKNOWN"
                    if transaction.players and hasattr(transaction.players[0], 'type'):
                        tx_type = transaction.players[0].type
                    
                    transaction_data = {
                        'id': transaction.id,
                        'date': str(transaction.date),
                        'type': tx_type,
                        'description': description,
                        'teamId': transaction.team.team_id,
                        'teamName': transaction.team.name
                    }
                    transactions_list.append(transaction_data)
                return transactions_list
            elif endpoint == "getTeams":
                # Get teams
                teams_list = []
                for team in self.client.teams:
                    team_data = {
                        'id': team.team_id,
                        'name': team.name,
                        'owner': team.name.split(' ')[0]  # Use first part of team name as owner
                    }
                    teams_list.append(team_data)
                return teams_list
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
        result = self._make_request("getPlayerIds")
        return result if isinstance(result, dict) else {}
        
    def get_league_info(self) -> Dict[str, Any]:
        """Fetch league information"""
        result = self._make_request("getLeagueInfo")
        return result if isinstance(result, dict) else {}
        
    def get_team_rosters(self) -> Dict[str, Any]:
        """Fetch team rosters"""
        result = self._make_request("getTeamRosters")
        return result if isinstance(result, dict) else {}
        
    def get_standings(self) -> List[Dict[str, Any]]:
        """Fetch standings data"""
        result = self._make_request("getStandings")
        return result if isinstance(result, list) else []
        
    def get_scoring_periods(self) -> List[Dict[str, Any]]:
        """Fetch scoring periods"""
        result = self._make_request("getScoringPeriods")
        return result if isinstance(result, list) else []
        
    def get_matchups(self, period_id: int = 1) -> List[Dict[str, Any]]:
        """Fetch matchups for a specific period"""
        result = self._make_request("getMatchups", {"periodId": period_id})
        return result if isinstance(result, list) else []
        
    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent transactions"""
        result = self._make_request("getTransactions", {"limit": limit})
        return result if isinstance(result, list) else []
        
    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all teams"""
        result = self._make_request("getTeams")
        return result if isinstance(result, list) else []