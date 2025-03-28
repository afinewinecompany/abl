import requests
from typing import Dict, List, Any, Union
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

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Make API request with error handling and retries"""
        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request to {endpoint} failed: {str(e)}")
            # Return empty data instead of mock data
            if endpoint in ["getMatchups", "getTransactions", "getStandings", "getScoringPeriods"]:
                return []
            else:
                return {}
        except ValueError as e:
            st.error(f"Failed to parse JSON response from {endpoint}: {str(e)}")
            # Return empty data instead of mock data
            if endpoint in ["getMatchups", "getTransactions", "getStandings", "getScoringPeriods"]:
                return []
            else:
                return {}

    def _get_mock_data(self, endpoint: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
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
                    "wins": 10,
                    "losses": 5,
                    "ties": 0,
                    "winPercentage": 0.667,
                    "pointsFor": 100.5,
                    "pointsAgainst": 80.2,
                    "gamesBack": 0.0,
                    "streakDescription": "W3"
                }
            ]
        elif endpoint == "getScoringPeriods":
            # Mock scoring periods data
            return [
                {
                    "periodName": "Week 1",
                    "periodNum": 1,
                    "startDate": "2025-04-01",
                    "endDate": "2025-04-07",
                    "isCurrent": True,
                    "isComplete": False,
                    "isFuture": False
                },
                {
                    "periodName": "Week 2",
                    "periodNum": 2,
                    "startDate": "2025-04-08",
                    "endDate": "2025-04-14",
                    "isCurrent": False,
                    "isComplete": False,
                    "isFuture": True
                }
            ]
        elif endpoint == "getMatchups":
            # Mock matchups data
            return [
                {
                    "id": "match1",
                    "awayTeam": {"name": "Away Team"},
                    "homeTeam": {"name": "Home Team"},
                    "awayScore": 95.5,
                    "homeScore": 87.2
                },
                {
                    "id": "match2",
                    "awayTeam": {"name": "Visitors"},
                    "homeTeam": {"name": "Hosts"},
                    "awayScore": 78.4,
                    "homeScore": 102.6
                }
            ]
        elif endpoint == "getTransactions":
            # Mock transactions data with all required fields for Transaction object structure
            return [
                {
                    "id": "tx1",
                    "dateTime": "Apr 5, 2025, 2:30PM",
                    "teamName": "Savvy Squad",
                    "playerName": "John Smith",
                    "playerTeam": "LAD",
                    "playerPosition": "SP",
                    "type": "ADD",
                    "count": 1,
                    "players": [
                        {"name": "John Smith", "team": "LAD", "position": "SP"}
                    ],
                    "finalized": True
                },
                {
                    "id": "tx2",
                    "dateTime": "Apr 3, 2025, 10:15AM",
                    "teamName": "Power Hitters",
                    "playerName": "Mike Johnson",
                    "playerTeam": "NYY",
                    "playerPosition": "1B",
                    "type": "DROP",
                    "count": 1,
                    "players": [
                        {"name": "Mike Johnson", "team": "NYY", "position": "1B"}
                    ],
                    "finalized": True
                },
                {
                    "id": "tx3",
                    "dateTime": "Apr 8, 2025, 3:45PM",
                    "teamName": "Draft Kings",
                    "playerName": "Alex Rodriguez",
                    "playerTeam": "BOS",
                    "playerPosition": "3B",
                    "type": "TRADE",
                    "count": 2,
                    "players": [
                        {"name": "Alex Rodriguez", "team": "BOS", "position": "3B"},
                        {"name": "David Martinez", "team": "CHC", "position": "OF"}
                    ],
                    "finalized": True
                },
                {
                    "id": "tx4",
                    "dateTime": "Apr 10, 2025, 9:00AM",
                    "teamName": "Batting Champs",
                    "playerName": "Chris Johnson",
                    "playerTeam": "ATL",
                    "playerPosition": "RP",
                    "type": "CLAIM",
                    "count": 1,
                    "players": [
                        {"name": "Chris Johnson", "team": "ATL", "position": "RP"}
                    ],
                    "finalized": False
                }
            ]
        return {}

    def get_player_ids(self) -> Dict[str, Any]:
        """Fetch player IDs"""
        return self._make_request("getPlayerIds", {"sport": "MLB"})

    def get_league_info(self) -> Dict[str, Any]:
        """Fetch league information"""
        return self._make_request("getLeagueInfo", {"leagueId": self.league_id})

    def get_team_rosters(self) -> Dict[str, Any]:
        """Fetch team rosters"""
        return self._make_request("getTeamRosters", 
                              {"leagueId": self.league_id, "period": "1"})

    def get_standings(self) -> List[Dict[str, Any]]:
        """Fetch standings data"""
        return self._make_request("getStandings", {"leagueId": self.league_id})
        
    def get_scoring_periods(self) -> List[Dict[str, Any]]:
        """Fetch scoring periods"""
        return self._make_request("getScoringPeriods", {"leagueId": self.league_id})
        
    def get_matchups(self, period_id: int = 1) -> List[Dict[str, Any]]:
        """Fetch matchups for a specific period"""
        return self._make_request("getMatchups", 
                               {"leagueId": self.league_id, "scoringPeriod": period_id})
        
    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent transactions"""
        return self._make_request("getTransactions", 
                               {"leagueId": self.league_id, "limit": limit})
                               
    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all teams"""
        # Extract from team rosters instead of direct endpoint
        roster_data = self.get_team_rosters()
        teams = []
        
        if isinstance(roster_data, dict) and 'rosters' in roster_data:
            for team_id, team_info in roster_data.get('rosters', {}).items():
                if isinstance(team_info, dict):
                    teams.append({
                        'id': team_id,
                        'name': team_info.get('teamName', f'Team {team_id}')
                    })
        
        return teams
        
    def get_live_scoring(self, scoring_period: int = 1) -> Dict[str, Any]:
        """
        Fetch live scoring data for a specific period.
        Makes a direct API request to get matchups data.
        """
        try:
            # Get matchups data from the API for the specified period
            matchups_data = self.get_matchups(period_id=scoring_period)
            
            # Log the raw response type for debugging
            st.write(f"API Response Type: {type(matchups_data)}")
            
            # Process matchup data - could be a list or a dictionary
            matchup_items = []
            
            # If we received a dictionary, extract the matchups
            if isinstance(matchups_data, dict):
                # Check for common dictionary structures that might contain matchups
                if "matchups" in matchups_data:
                    matchup_items = matchups_data.get("matchups", [])
                    st.write("Found matchups key in response")
                elif "data" in matchups_data:
                    matchup_items = matchups_data.get("data", [])
                    st.write("Found data key in response")
                elif "items" in matchups_data:
                    matchup_items = matchups_data.get("items", [])
                    st.write("Found items key in response")
                else:
                    # If we can't find a known key, log all the keys for debugging
                    st.write(f"Available keys in response: {list(matchups_data.keys())}")
                    
                    # Try to extract any list that might contain matchups
                    for key, value in matchups_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            matchup_items = value
                            st.write(f"Using list from key: {key}")
                            break
            elif isinstance(matchups_data, list):
                # If it's already a list, use it directly
                matchup_items = matchups_data
            else:
                st.warning(f"Unexpected matchups data type: {type(matchups_data)}")
                return {"liveScoringMatchups": []}
            
            # Transform the matchups data to the expected format
            formatted_matchups = []
            
            if not isinstance(matchup_items, list):
                st.warning(f"Expected list of matchups, got {type(matchup_items)}")
                return {"liveScoringMatchups": []}
                
            for idx, matchup in enumerate(matchup_items):
                # Check if the matchup is a dictionary
                if not isinstance(matchup, dict):
                    continue
                
                # Log the keys in the first matchup for debugging
                if idx == 0:
                    st.write(f"Matchup keys: {list(matchup.keys())}")
                    
                # Extract team data safely
                home_team = matchup.get("homeTeam", {})
                away_team = matchup.get("awayTeam", {})
                
                # Check if home_team and away_team are dictionaries
                if not isinstance(home_team, dict) or not isinstance(away_team, dict):
                    continue
                
                formatted_matchups.append({
                    "id": matchup.get("id", f"m{idx+1}"),
                    "home": {
                        "team": {"name": home_team.get("name", f"Home Team {idx+1}")},
                        "score": matchup.get("homeScore", 0)
                    },
                    "away": {
                        "team": {"name": away_team.get("name", f"Away Team {idx+1}")},
                        "score": matchup.get("awayScore", 0)
                    }
                })
            
            # Log that we're using real data
            st.write(f"Using real data with {len(formatted_matchups)} matchups")
            
            return {"liveScoringMatchups": formatted_matchups}
        except Exception as e:
            st.warning(f"Error fetching live scoring: {str(e)}")
            return {"liveScoringMatchups": []}