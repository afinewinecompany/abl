import requests
from typing import Dict, Any, Optional
import streamlit as st
import time
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
            
        # Debug the session cookies
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.session.cookies.items()])
        st.info(f"Current cookie count: {len(self.session.cookies.items())}")
        
        try:
            # First make sure cookies and authentication are fresh
            self.apply_user_auth()
            
            # Direct request to load the main players page to ensure cookies are set correctly
            main_url = f"https://www.fantrax.com/fantasy/league/{self.league_id}/players"
            st.info(f"Making initial request to: {main_url}")
            
            main_response = self.session.get(
                main_url,
                timeout=30,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
            )
            main_response.raise_for_status()
            
            # Headers needed for API requests
            api_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": main_url,
                "Origin": "https://www.fantrax.com",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # Use the most direct approach based on real Fantrax API
            st.info("Making player pool request to Fantrax API...")
            
            # This is the correct endpoint format based on latest Fantrax API
            player_url = "https://www.fantrax.com/fxpa/req"
            
            # Build the payload for the player request
            player_params = {
                "msgs": [{
                    "method": "getLeaguePlayersDetails",
                    "data": {
                        "leagueId": self.league_id,
                        "view": "AVAILABLE",  # or "ALL" to see all players
                        "pageNumber": page,
                        "maxResultsPerPage": max_results
                    },
                    "uri": "/league/player-pool"
                }]
            }

            # Make the request
            player_response = self.session.post(
                player_url,
                json=player_params,
                headers=api_headers,
                timeout=30
            )
            
            # Debug response status
            st.info(f"Player API response status: {player_response.status_code}")
            
            # If response failed, try the general league data approach
            if player_response.status_code != 200:
                st.warning(f"Player request failed with status {player_response.status_code}, trying alternative...")
                
                general_url = "https://www.fantrax.com/fxea/req"
                general_params = {
                    "msgs": [{
                        "method": "loadLeagueData",
                        "data": {
                            "leagueId": self.league_id,
                            "fetchType": "PLAYERS_POOL",
                            "view": "AVAILABLE",
                            "pageNumber": 1,
                            "pageSize": max_results
                        },
                        "uri": "/general"
                    }]
                }
                
                general_response = self.session.post(
                    general_url,
                    json=general_params,
                    headers=api_headers,
                    timeout=30
                )
                
                st.info(f"Alternative API response status: {general_response.status_code}")
                
                if general_response.status_code == 200:
                    try:
                        general_data = general_response.json()
                        st.info(f"Alternative response keys: {list(general_data.keys()) if isinstance(general_data, dict) else 'Not a dict'}")
                        
                        # Try to extract players from different possible structures
                        if isinstance(general_data, dict):
                            if "msgs" in general_data and len(general_data["msgs"]) > 0:
                                msg_data = general_data["msgs"][0]
                                if "data" in msg_data and "players" in msg_data["data"]:
                                    return {"players": msg_data["data"]["players"]}
                                elif "data" in msg_data and "poolData" in msg_data["data"]:
                                    pool_data = msg_data["data"]["poolData"]
                                    if "playerInfo" in pool_data:
                                        return {"players": pool_data["playerInfo"]}
                    except Exception as gen_err:
                        st.error(f"Error parsing alternative response: {str(gen_err)}")
                
                # If all API attempts fail, try web scraping as last resort
                try:
                    from bs4 import BeautifulSoup
                    import re
                    
                    st.info("Attempting to scrape player data directly...")
                    
                    # Parse the HTML content from the main response
                    soup = BeautifulSoup(main_response.text, 'lxml')
                    
                    # Look for player data in the page
                    script_tags = soup.find_all("script")
                    for script in script_tags:
                        if script.string and "window.__INITIAL_STATE__" in str(script.string):
                            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', str(script.string))
                            if state_match:
                                try:
                                    state_json = json.loads(state_match.group(1))
                                    
                                    # Try to find player data in the state
                                    if "fantasySports" in state_json:
                                        fantasy = state_json["fantasySports"]
                                        if "playerPool" in fantasy and "playerInfo" in fantasy["playerPool"]:
                                            players = fantasy["playerPool"]["playerInfo"]
                                            return {"players": players}
                                except Exception as state_err:
                                    st.error(f"Error parsing state JSON: {str(state_err)}")
                                
                    # If we got here, try looking for players in a table
                    player_table = soup.find("table", class_="playerTableContents")
                    if player_table:
                        players_list = []
                        rows = player_table.find_all("tr")
                        
                        for row in rows:
                            if "player-row" in str(row.get("class", "")):
                                try:
                                    player = {}
                                    # Get player name
                                    name_cell = row.find("td", class_=lambda c: c and "playerName" in c)
                                    if name_cell:
                                        player["name"] = name_cell.get_text(strip=True)
                                    
                                    # Get position
                                    pos_cell = row.find("td", class_=lambda c: c and "position" in c)
                                    if pos_cell:
                                        player["position"] = pos_cell.get_text(strip=True)
                                    
                                    # Get team
                                    team_cell = row.find("td", class_=lambda c: c and "team" in c)
                                    if team_cell:
                                        player["team"] = team_cell.get_text(strip=True)
                                    
                                    if player.get("name"):
                                        players_list.append(player)
                                except Exception:
                                    continue
                                    
                        if players_list:
                            st.success(f"Extracted {len(players_list)} players from table")
                            return {"players": players_list}
                
                except ImportError:
                    st.warning("BeautifulSoup or lxml not available")
                except Exception as scrape_err:
                    st.error(f"Error during scraping: {str(scrape_err)}")
                
                st.error("All attempts to fetch player data failed")
                return {"players": []}
            
            # Process successful response
            try:
                player_data = player_response.json()
                
                # Debug response structure
                st.info(f"Response structure: {list(player_data.keys()) if isinstance(player_data, dict) else 'Not a dict'}")
                
                # Extract players based on response structure
                if isinstance(player_data, dict):
                    # Try to find players in the response structure
                    if "msgs" in player_data and len(player_data["msgs"]) > 0:
                        msg_data = player_data["msgs"][0]
                        if "data" in msg_data:
                            data = msg_data["data"]
                            
                            # Check for players in different possible structures
                            if "players" in data:
                                players = data["players"]
                                return {"players": players}
                            elif "playerInfo" in data:
                                players = data["playerInfo"]
                                return {"players": players}
                            elif "playersInfo" in data:
                                players = data["playersInfo"]
                                return {"players": players}
                    
                    # Direct structure with players key
                    if "players" in player_data:
                        return player_data
                
                # If we reached here and didn't return, we couldn't find players
                st.warning("Couldn't find players in the response structure")
                return {"players": []}
                
            except Exception as parse_err:
                st.error(f"Error parsing player response: {str(parse_err)}")
                return {"players": []}
                
        except Exception as e:
            st.error(f"Error fetching available players: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return {"players": []}