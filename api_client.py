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
        
        try:
            # Direct URL to the players page
            direct_url = f"https://www.fantrax.com/fantasy/league/{self.league_id}/players"
            st.info(f"Attempting to scrape player data from: {direct_url}")
            
            # Try web scraping approach
            try:
                from bs4 import BeautifulSoup
                import re
                import json
                
                # Make request to the players page
                html_response = self.session.get(
                    direct_url,
                    timeout=30,  # Increase timeout for potential large page
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                    }
                )
                html_response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(html_response.text, 'lxml')
                
                # Look for player data in script tags
                script_tags = soup.find_all("script")
                player_data = []
                
                for script in script_tags:
                    script_content = script.string
                    if script_content and "playerInfo" in script_content:
                        # Try to extract JSON data from script
                        try:
                            # Find JSON object with player data
                            json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script_content)
                            if json_matches:
                                state_data = json.loads(json_matches[0])
                                if "playerInfo" in str(state_data):
                                    # Look for player data in various places
                                    if "playerPool" in state_data and "playerInfo" in state_data["playerPool"]:
                                        player_data = state_data["playerPool"]["playerInfo"]
                                    elif "fantasySports" in state_data:
                                        fantasy = state_data["fantasySports"]
                                        if "playerPool" in fantasy and "playerInfo" in fantasy["playerPool"]:
                                            player_data = fantasy["playerPool"]["playerInfo"]
                        except Exception as json_err:
                            st.warning(f"Error extracting player data from script: {str(json_err)}")
                
                # If we found player data, convert to the expected format
                if player_data:
                    st.success(f"Successfully scraped {len(player_data)} players")
                    return {"players": player_data}
                
                # Try looking for table data
                player_table = soup.find("table", class_="playerTableContents")
                if player_table:
                    players = []
                    rows = player_table.find_all("tr", class_=lambda c: c and "ng-scope" in c)
                    
                    for row in rows:
                        try:
                            player = {}
                            # Extract player name
                            name_cell = row.find("td", class_="playerNameCol")
                            if name_cell:
                                player["name"] = name_cell.get_text(strip=True)
                            
                            # Extract position
                            pos_cell = row.find("td", class_="posCol")
                            if pos_cell:
                                player["position"] = pos_cell.get_text(strip=True)
                            
                            # Extract team
                            team_cell = row.find("td", class_="teamCol")
                            if team_cell:
                                player["team"] = team_cell.get_text(strip=True)
                            
                            # Add player if we have a name
                            if player.get("name"):
                                players.append(player)
                        except Exception as row_err:
                            continue
                    
                    if players:
                        st.success(f"Successfully scraped {len(players)} players from table")
                        return {"players": players}
            except ImportError:
                st.warning("BeautifulSoup or lxml not available for web scraping")
            except Exception as scrape_err:
                st.error(f"Error scraping player data: {str(scrape_err)}")
            
            # If web scraping fails, try the API approaches as fallback
            st.warning("Web scraping failed, trying API endpoints...")
            
            # Log the request for debugging purposes
            st.info("Making request to Fantrax API for player data...")
            
            # Try API approach 1: Direct player pool endpoint
            params = {
                "leagueId": self.league_id,
                "view": "AVAILABLE",
                "pageNumber": page,
                "maxResultsPerPage": max_results,
                "statisticType": "SEASON_PROJECTION_FANTASY",
                "offset": (page - 1) * max_results,
                "limit": max_results,
                "scoring": "HEAD2HEAD",  # This was missing and might be required
                "sortStatId": "-1",  # Default sort
                "sortDirection": "DESC"
            }
            
            # Add filters if provided
            if position:
                params["positionOrGroup"] = position
            if team:
                params["mlbTeam"] = team
            if sort_stat:
                params["sortStat"] = sort_stat
            
            # Use the format found in actual Fantrax requests
            endpoint = "fxpa/league/playerPool"
            response = self.session.get(
                f"https://www.fantrax.com/{endpoint}",
                params=params,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                    "Origin": "https://www.fantrax.com",
                    "Referer": direct_url,
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Check if we have actual player data
            if "players" not in data:
                st.warning("No players found in the API response")
                # Debug information
                st.info(f"Response data keys: {list(data.keys())}")
                
                # Try API approach 2: General AJAX endpoint
                st.info("Trying alternative endpoint...")
                
                ajax_params = {
                    "leagueId": self.league_id,
                    "fetchType": "PLAYERS_POOL",
                    "scoringCategoryType": "SEASON_PROJECTION_FANTASY",
                    "scoringPeriodId": 0,  # current period
                    "seasonType": "REGULAR_SEASON",
                    "view": "AVAILABLE",
                    "lineupType": None,
                    "sortDirection": "DESC",
                    "pageSize": max_results,
                    "pageNumber": page,
                    "filters": {},
                }
                
                if position:
                    ajax_params["filters"]["positionOrGroup"] = position
                if team:
                    ajax_params["filters"]["teamId"] = team
                
                try:
                    ajax_response = self.session.post(
                        "https://www.fantrax.com/fxea/general/loadLeagueData",
                        json=ajax_params,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "Origin": "https://www.fantrax.com",
                            "Referer": direct_url,
                            "X-Requested-With": "XMLHttpRequest",
                        }
                    )
                    ajax_response.raise_for_status()
                    ajax_data = ajax_response.json()
                    
                    # Debug info for alternative endpoint
                    st.info(f"Alternative endpoint keys: {list(ajax_data.keys()) if isinstance(ajax_data, dict) else 'Not a dict'}")
                    
                    # If this contains player data, return it
                    if isinstance(ajax_data, dict) and ajax_data.get("players"):
                        return ajax_data
                    
                    # Try to extract players from the pool data
                    if isinstance(ajax_data, dict) and "poolData" in ajax_data:
                        pool_data = ajax_data["poolData"]
                        if isinstance(pool_data, dict) and "playerInfo" in pool_data:
                            players = pool_data["playerInfo"]
                            if isinstance(players, list) and len(players) > 0:
                                return {"players": players}
                except Exception as ajax_err:
                    st.warning(f"Alternative endpoint failed: {str(ajax_err)}")
                
                # If all attempts fail, return empty players list
                return {"players": []}
                
            return data
            
        except Exception as e:
            st.error(f"Error fetching available players: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            
            # Try final API approach - the simplest API endpoint
            try:
                st.info("Trying final fallback endpoint...")
                
                # This is the most basic endpoint that should work if the user is logged in
                simple_params = {
                    "leagueId": self.league_id,
                    "view": "AVAILABLE",
                }
                
                simple_response = self.session.get(
                    "https://www.fantrax.com/fxpa/stats/MLB/players",
                    params=simple_params,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    }
                )
                simple_response.raise_for_status()
                simple_data = simple_response.json()
                
                # Debug info
                if isinstance(simple_data, dict):
                    st.info(f"Final fallback endpoint keys: {list(simple_data.keys())}")
                    if "players" in simple_data and isinstance(simple_data["players"], list):
                        return simple_data
                
            except Exception as final_err:
                st.warning(f"All API attempts failed: {str(final_err)}")
                
            # Try printing more debug info
            st.info("Please try logging in again or refreshing the page")
            return {"players": []}