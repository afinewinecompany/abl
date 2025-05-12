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
            # Only display info on sidebar if requested
            st.sidebar.info(f"Attempting API request to {endpoint}...")
            
            # Set appropriate headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=headers,
                timeout=20  # Extended timeout
            )
            
            # Get the response content
            response_text = response.text
            
            # Check if response is likely HTML instead of JSON (common error)
            if response_text.strip().startswith(('<html', '<!DOCTYPE html')):
                # Provide a single clear warning in the main UI area
                st.warning(f"🚨 API Connectivity Issue: The Fantrax API returned HTML instead of JSON. Using fallback data for {endpoint}.")
                
                # Add explanatory message in the sidebar with possible solutions
                st.sidebar.error(f"🔍 API Error Details: {endpoint}")
                st.sidebar.info("""
                Possible causes:
                - Fantrax API may have changed
                - Authentication may be required
                - API rate limits might be in effect
                - Session cookies might be needed
                """)
                
                # Return mock data for this request
                return self._get_mock_data(endpoint)
                
            # Try to parse as JSON
            try:
                # Attempt to parse the JSON response
                data = response.json()
                
                # Check if the response contains an 'error' key, which indicates API error
                if isinstance(data, dict) and 'error' in data:
                    error_msg = data.get('error', 'Unknown API error')
                    st.sidebar.error(f"API Error in {endpoint}: {error_msg}")
                    
                    # Return mock data for this specific error
                    return self._get_mock_data(endpoint)
                
                # Success!
                if isinstance(data, (dict, list)):
                    st.sidebar.success(f"✅ API request to {endpoint} successful")
                    return data
                else:
                    st.warning(f"Unexpected data type from {endpoint}: {type(data)}")
                    # Return mock data for unexpected response type
                    return self._get_mock_data(endpoint)
                    
            except ValueError as json_error:
                # JSON parsing error - display a clear error message
                st.warning(f"Failed to parse JSON response from {endpoint}: {str(json_error)}")
                
                # Return mock data
                return self._get_mock_data(endpoint)
                
        except requests.exceptions.RequestException as e:
            # Network or HTTP error 
            st.warning(f"API connection to {endpoint} failed: {str(e)}")
            st.sidebar.info("Using fallback data while API connection issues persist")
            return self._get_mock_data(endpoint)
        except Exception as e:
            # General error handling
            st.error(f"Unexpected error in API request to {endpoint}: {str(e)}")
            import traceback
            st.sidebar.error(f"API error details: {str(e)}")
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
            
            # Set appropriate headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(
                "https://www.fantrax.com/fxea/general/getStandings",
                params={"leagueId": self.league_id},
                headers=headers,
                timeout=20  # Extended timeout
            )
            
            # Get the response content
            response_text = response.text
            
            # Check if response is likely HTML instead of JSON (common error)
            if response_text.strip().startswith(('<html', '<!DOCTYPE html')):
                # Provide a clear warning in the main UI area
                st.warning("🚨 API Connectivity Issue: The Fantrax API returned HTML instead of JSON for standings data. Using fallback data.")
                
                # Add explanatory message in the sidebar
                st.sidebar.error("🔍 API Error Details: getStandings")
                st.sidebar.info("""
                Possible causes:
                - Fantrax API may have changed
                - Authentication may be required
                - API rate limits might be in effect
                - Session cookies might be needed
                """)
                
                # Return mock data
                return self._get_mock_data("getStandings")
            
            # Try to parse the JSON response
            try:
                response_data = response.json()
                
                # Check the response structure and extract standings if needed
                if isinstance(response_data, dict) and 'standings' in response_data:
                    # API returned a dictionary with a 'standings' key containing the actual data
                    standings_data = response_data['standings']
                    st.sidebar.success(f"✅ Received standings data: {len(standings_data)} teams found")
                    return standings_data
                elif isinstance(response_data, list):
                    # API returned a list directly (expected format)
                    st.sidebar.success(f"✅ Received standings data: {len(response_data)} teams found")
                    return response_data
                else:
                    # Unknown format - log it for debugging
                    st.sidebar.warning(f"⚠️ Unexpected API response format: {type(response_data)}")
                    if isinstance(response_data, dict):
                        st.sidebar.info(f"Response keys: {list(response_data.keys())}")
                    
                    # Return mock data when the format is unexpected
                    return self._get_mock_data("getStandings")
            except ValueError as e:
                # JSON parsing error
                st.warning(f"Failed to parse JSON response from standings API: {str(e)}")
                
                # Return mock data
                return self._get_mock_data("getStandings")
        except requests.exceptions.RequestException as e:
            # Network or HTTP error
            st.warning(f"Standings API request failed: {str(e)}")
            st.sidebar.info("Using fallback data while API connection issues persist")
            return self._get_mock_data("getStandings")
        except Exception as e:
            # General error handling
            st.error(f"Unexpected error fetching standings: {str(e)}")
            st.sidebar.error(f"API error details: {str(e)}")
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