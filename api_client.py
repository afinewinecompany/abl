import requests
from typing import Dict, Any, Optional
import streamlit as st
import time
import json
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

class FantraxAPI:
    def __init__(self):
        self.base_url = "https://www.fantrax.com/fxea"
        # Get league ID from .env file or use default
        self.league_id = os.getenv("FANTRAX_LEAGUE_ID", "grx2lginm1v4p5jd")

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
                # Create a completely fresh session
                self.session = requests.Session()
                
                # We'll set timeouts individually on requests
                
                # Apply retry strategy
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=0.5,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST"]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self.session.mount("http://", adapter)
                self.session.mount("https://", adapter)
                
                # Apply cookies to session
                cookies = auth_data.get("cookies", {})
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)
                
                # Add important headers required by Fantrax
                self.session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Origin": "https://www.fantrax.com",
                    "Referer": f"https://www.fantrax.com/fantasy/league/{self.league_id}/players",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                })
                
                # Apply any custom headers from auth data
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
                             max_results: int = 100) -> Dict:
        """
        Fetch available players from the league using a simpler, more direct approach
        
        Args:
            position: Filter by position code (e.g., "SP", "OF", "C")
            team: Filter by team code (e.g., "LAD", "NYY")
            sort_stat: Sort by stat category
            page: Page number for pagination
            max_results: Maximum number of results per page
            
        Returns:
            Dictionary containing available players data
        """
        if not self.is_authenticated():
            st.error("User is not authenticated with Fantrax. Please log in first.")
            return {"players": []}
        
        try:
            # Apply authentication to ensure we have valid cookies
            self.apply_user_auth()
            
            # Debug info about session
            if st.session_state.get('debug_mode', False):
                st.info(f"Authentication status: {self.is_authenticated()}")
                st.info(f"Using league ID: {self.league_id}")
                st.info(f"Cookie count: {len(self.session.cookies.items())}")
            
            # Set common headers for all requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": "https://www.fantrax.com",
                "Referer": f"https://www.fantrax.com/fantasy/league/{self.league_id}/players",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            # APPROACH 1: Direct API call using the latest Fantrax API endpoint structure
            url = "https://www.fantrax.com/fxpa/req"
            
            # Updated payload based on the latest Fantrax API structure
            payload = {
                "msgs": [{
                    "method": "getPlayersListForPool",  # Updated method name
                    "data": {
                        "leagueId": self.league_id,
                        "poolId": None,
                        "view": "AVAILABLE",
                        "skipNews": True,
                        "statsType": "1",  # Stats type 1 = Latest season
                        "scoringPeriod": None,
                        "scoringInterval": None,
                        "pageNumber": page,
                        "maxResultsPerPage": max_results,
                        "positionOrTeamOrCategory": position,
                        "sortType": sort_stat or "RANK",
                        "filterInactivePlayers": False,
                        "teamId": team
                    },
                    "uri": "/playerPool/players"  # Updated URI path
                }]
            }
            
            if st.session_state.get('debug_mode', False):
                st.info("📡 Sending request to Fantrax API for available players...")
            
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if st.session_state.get('debug_mode', False):
                    st.success(f"✅ API request successful with status {response.status_code}")
                    
                    # Debug response structure
                    if isinstance(data, dict) and "msgs" in data and data["msgs"]:
                        st.info(f"Response 'msgs' count: {len(data['msgs'])}")
                        if data["msgs"] and "data" in data["msgs"][0]:
                            msg_data = data["msgs"][0]
                            st.info(f"First message keys: {list(msg_data.keys())}")
                            if "data" in msg_data:
                                st.info(f"Data keys: {list(msg_data['data'].keys())}")
                                
                                # Look for players or playerPool data
                                data_obj = msg_data["data"]
                                if "players" in data_obj and isinstance(data_obj["players"], list):
                                    player_count = len(data_obj["players"])
                                    st.success(f"Found {player_count} players in response!")
                                    
                                    # Show sample player data
                                    if player_count > 0:
                                        sample_player = data_obj["players"][0]
                                        st.info(f"Sample player keys: {list(sample_player.keys())}")
                                        
                                        # Check if name field exists
                                        if "name" in sample_player:
                                            st.success(f"Sample player name: {sample_player['name']}")
                
                # Extract players based on API response structure
                if isinstance(data, dict) and "msgs" in data and data["msgs"]:
                    msg = data["msgs"][0]
                    if "data" in msg and "players" in msg["data"]:
                        players = msg["data"]["players"]
                        if isinstance(players, list):
                            if st.session_state.get('debug_mode', False):
                                st.success(f"Successfully extracted {len(players)} players from API response")
                            return {"players": players}
                
                # If we couldn't find players in the expected structure, try a different path
                if st.session_state.get('debug_mode', False):
                    st.warning("Couldn't find players in the expected response structure")
                    # Return raw data structure for inspection
                    st.info(f"Raw response keys: {list(data.keys() if isinstance(data, dict) else [])}")
                
                # FALLBACK 1: Check for players in a different structure
                if isinstance(data, dict) and "msgs" in data and data["msgs"]:
                    msg = data["msgs"][0]
                    if "data" in msg:
                        data_obj = msg["data"]
                        # Try different possible player containers
                        player_containers = ["players", "playerInfo", "playersInfo", "playersList", "poolPlayers"]
                        for container in player_containers:
                            if container in data_obj and isinstance(data_obj[container], list):
                                return {"players": data_obj[container]}
                
                # FALLBACK 2: Alternative structure (pool data)
                if isinstance(data, dict) and "msgs" in data and data["msgs"]:
                    msg = data["msgs"][0]
                    if "data" in msg and "poolData" in msg["data"]:
                        pool_data = msg["data"]["poolData"]
                        player_containers = ["playerInfo", "players", "items"]
                        for container in player_containers:
                            if container in pool_data and isinstance(pool_data[container], list):
                                return {"players": pool_data[container]}
            else:
                # API request failed
                if st.session_state.get('debug_mode', False):
                    st.error(f"API request failed with status {response.status_code}")
                    st.error(f"Response text: {response.text[:500]}...")
                
                # APPROACH 2: Try alternative API endpoint as backup
                alternative_url = "https://www.fantrax.com/fxea/req"
                alternative_payload = {
                    "msgs": [{
                        "method": "getLeaguePlayersInfo",
                        "data": {
                            "leagueId": self.league_id,
                            "playerPool": "AVAILABLE"
                        },
                        "uri": "/general"
                    }]
                }
                
                if st.session_state.get('debug_mode', False):
                    st.info("Trying alternative API endpoint...")
                
                alt_response = self.session.post(
                    alternative_url, 
                    json=alternative_payload, 
                    headers=headers, 
                    timeout=30
                )
                
                if alt_response.status_code == 200:
                    alt_data = alt_response.json()
                    
                    # Try to extract players from alternative response
                    if isinstance(alt_data, dict) and "msgs" in alt_data and alt_data["msgs"]:
                        alt_msg = alt_data["msgs"][0]
                        if "data" in alt_msg and "players" in alt_msg["data"]:
                            alt_players = alt_msg["data"]["players"]
                            if isinstance(alt_players, list):
                                return {"players": alt_players}
            
            # If all API attempts fail, try directly accessing the players page
            if st.session_state.get('debug_mode', False):
                st.info("Attempting direct access to players page...")
            
            direct_url = f"https://www.fantrax.com/fantasy/league/{self.league_id}/players;view=AVAILABLE"
            direct_response = self.session.get(direct_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }, timeout=30)
            
            if direct_response.status_code == 200:
                try:
                    from bs4 import BeautifulSoup
                    import re
                    
                    # Parse HTML content
                    soup = BeautifulSoup(direct_response.text, 'html.parser')
                    
                    # Look for player data in script tags
                    script_data = None
                    for script in soup.find_all('script'):
                        if script.string and 'window.__INITIAL_STATE__' in script.string:
                            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                            if match:
                                script_data = match.group(1)
                                break
                    
                    if script_data:
                        state_data = json.loads(script_data)
                        
                        # Find player data in state
                        if 'fantasySports' in state_data:
                            fantasy = state_data['fantasySports']
                            if 'playerPool' in fantasy and 'playerInfo' in fantasy['playerPool']:
                                players = fantasy['playerPool']['playerInfo']
                                return {"players": players}
                    
                    # If we can't extract from scripts, try table parsing
                    player_table = soup.find('table', {'class': 'player-table'})
                    if player_table:
                        players_list = []
                        for row in player_table.find_all('tr', {'class': lambda c: c and 'player-row' in c}):
                            try:
                                player = {}
                                name_cell = row.find('td', {'class': lambda c: c and 'player-name' in c})
                                if name_cell:
                                    player['name'] = name_cell.get_text(strip=True)
                                    
                                pos_cell = row.find('td', {'class': lambda c: c and 'position' in c})
                                if pos_cell:
                                    player['position'] = pos_cell.get_text(strip=True)
                                    
                                team_cell = row.find('td', {'class': lambda c: c and 'team' in c})
                                if team_cell:
                                    player['team'] = team_cell.get_text(strip=True)
                                    
                                if player.get('name'):
                                    players_list.append(player)
                            except Exception:
                                continue
                        
                        if players_list:
                            return {"players": players_list}
                
                except ImportError:
                    st.error("BeautifulSoup not available")
                except Exception as e:
                    st.error(f"Error during scraping: {str(e)}")
            
            # If all attempts fail, return empty result
            return {"players": []}
        
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.error(f"Error fetching available players: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            return {"players": []}