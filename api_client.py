import requests
from typing import Dict, List, Any, Union
import streamlit as st
import time
import datetime
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
            st.sidebar.info(f"Making API request to {endpoint}...")
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=15  # Extended timeout
            )
            response.raise_for_status()
            
            # Get the response content
            response_text = response.text
            
            # Check if response is likely HTML instead of JSON (common error)
            if response_text.strip().startswith(('<html', '<!DOCTYPE html')):
                st.warning(f"Received HTML response from {endpoint} instead of JSON")
                return self._get_mock_data(endpoint)
                
            # Try to parse as JSON
            try:
                data = response.json()
                
                # Check if the response contains an 'error' key, which indicates API error
                if isinstance(data, dict) and 'error' in data:
                    error_msg = data.get('error', 'Unknown API error')
                    st.sidebar.error(f"API Error in {endpoint}: {error_msg}")
                    st.sidebar.warning(f"Dictionary keys: {list(data.keys())}")
                    # Log detailed information for debugging
                    st.sidebar.info(f"Full response: {data}")
                    return self._get_mock_data(endpoint)
                
                # Success!
                if isinstance(data, (dict, list)):
                    return data
                else:
                    st.warning(f"Unexpected data type from {endpoint}: {type(data)}")
                    # If we got a string or other non-dict/list, return mock data
                    return self._get_mock_data(endpoint)
                    
            except ValueError as json_error:
                st.error(f"Failed to parse JSON from {endpoint}: {str(json_error)}")
                # Show a sample of the response for debugging
                if len(response_text) > 100:
                    st.sidebar.info(f"Response preview: {response_text[:100]}...")
                else:
                    st.sidebar.info(f"Response: {response_text}")
                return self._get_mock_data(endpoint)
                
        except requests.exceptions.RequestException as e:
            st.warning(f"API request to {endpoint} failed: {str(e)}")
            return self._get_mock_data(endpoint)
        except Exception as e:
            st.error(f"Unexpected error in API request to {endpoint}: {str(e)}")
            import traceback
            st.sidebar.error(f"API request error traceback: {traceback.format_exc()}")
            return self._get_mock_data(endpoint)

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
        """Fetch standings data directly from the API for power rankings calculation"""
        try:
            st.sidebar.info("Fetching standings data from Fantrax API...")
            response = self.session.get(
                "https://www.fantrax.com/fxea/general/getStandings",
                params={"leagueId": self.league_id},
                timeout=20  # Extended timeout
            )
            response.raise_for_status()
            
            # Try to parse the JSON response
            try:
                response_data = response.json()
                
                # Check the response structure and extract standings if needed
                if isinstance(response_data, dict) and 'standings' in response_data:
                    # API returned a dictionary with a 'standings' key containing the actual data
                    standings_data = response_data['standings']
                    st.sidebar.success(f"Received standings data: {len(standings_data)} teams found")
                    return standings_data
                elif isinstance(response_data, list):
                    # API returned a list directly (expected format)
                    st.sidebar.success(f"Received standings data: {len(response_data)} teams found")
                    return response_data
                else:
                    # Unknown format - log it for debugging
                    st.sidebar.warning(f"Unexpected API response format: {type(response_data)}")
                    if isinstance(response_data, dict):
                        st.sidebar.info(f"Response keys: {list(response_data.keys())}")
                    
                    # Return what we got, let the processor handle it
                    return response_data
            except ValueError as e:
                st.error(f"Failed to parse JSON response from standings API: {str(e)}")
                st.warning("Response was not valid JSON - using mock data instead")
                return self._get_mock_data("getStandings")
        except requests.exceptions.RequestException as e:
            st.warning(f"Standings API request failed: {str(e)}")
            st.info("Using mock data for development purposes")
            return self._get_mock_data("getStandings")
        except Exception as e:
            st.error(f"Unexpected error fetching standings: {str(e)}")
            import traceback
            st.sidebar.error(f"Traceback: {traceback.format_exc()}")
            return self._get_mock_data("getStandings")
        
    def get_scoring_periods(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Fetch scoring periods
        
        Returns:
            Either a dictionary containing scoring periods data or a list of scoring period dictionaries,
            depending on the API response format.
        """
        # Since the API endpoint is returning errors, we'll use a different approach
        # and skip making the request entirely
        
        st.sidebar.info("Using league info to determine scoring periods...")
        
        # Get league info which contains basic season information
        league_info = self.get_league_info()
        
        if isinstance(league_info, dict) and 'season' in league_info:
            season = league_info.get('season', '2025')
            
            # Create a manually constructed scoring periods representation
            # This is more reliable than making API calls that consistently fail
            current_year = int(season)
            
            # MLB season typically runs April to October
            start_month = 4  # April
            start_day = 1
            
            # Create weekly scoring periods for the baseball season (approximately 26 weeks)
            periods = []
            for week in range(1, 27):
                # Calculate start and end dates for this week
                start_date = datetime.datetime(current_year, start_month, start_day) + datetime.timedelta(days=(week-1)*7)
                end_date = start_date + datetime.timedelta(days=6)
                
                # Determine if this is the current period
                now = datetime.datetime.now()
                is_current = start_date <= now <= end_date
                is_completed = now > end_date
                
                # Format dates in standard format
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')
                
                periods.append({
                    'periodName': f'Week {week}',
                    'periodNum': week,
                    'id': week,
                    'startDate': start_str,
                    'endDate': end_str,
                    'isActive': is_current,
                    'isCurrent': is_current,
                    'isCompleted': is_completed,
                    'isFuture': now < start_date
                })
            
            # Return a dictionary with the periods list
            return {
                'periods': periods,
                'currentPeriod': next((p for p in periods if p.get('isActive')), periods[0])
            }
        
        # If we couldn't get league info or construct periods, fall back to mock data
        st.sidebar.warning("Unable to construct scoring periods. Using default data.")
        return self._get_mock_data("getScoringPeriods")
        
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