import requests
from typing import Dict, List, Any, Union
import streamlit as st
import time
import os
import json
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

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
            st.warning(f"API request to {endpoint} failed, using mock data")
            # Return mock data based on the endpoint
            return self._get_mock_data(endpoint)
        except ValueError as e:
            st.error(f"Failed to parse JSON response from {endpoint}: {str(e)}")
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
            # Mock matchups data with consistent snake_case keys
            return [
                {
                    "id": "match1",
                    "away_team": "Away Team",
                    "home_team": "Home Team",
                    "away_score": 95.5,
                    "home_score": 87.2,
                    "winner": "Away Team",
                    "score_difference": 8.3,
                    "is_complete": False,
                    "week": "current"
                },
                {
                    "id": "match2",
                    "away_team": "Visitors",
                    "home_team": "Hosts",
                    "away_score": 78.4,
                    "home_score": 102.6,
                    "winner": "Hosts",
                    "score_difference": 24.2,
                    "is_complete": False,
                    "week": "current"
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
        
    def get_selenium_matchups(self, week: int = None) -> List[Dict[str, Any]]:
        """
        Fetch matchup data from Fantrax using Selenium.
        
        Args:
            week (int, optional): The week number to fetch matchups for. Defaults to the current week.
            
        Returns:
            List[Dict[str, Any]]: A list of matchup data dictionaries.
        """
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set up user agent to mimic a browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional options to fix "background" error
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        
        # Get credentials from environment variables
        username = os.getenv("FANTRAX_USERNAME")
        password = os.getenv("FANTRAX_PASSWORD")
        league_id = os.getenv("FANTRAX_LEAGUE_ID", self.league_id)
        
        if not username or not password:
            st.error("Fantrax login credentials are missing. Please check the .env file.")
            return self._get_mock_data("getMatchups")
            
        # Initialize WebDriver
        try:
            # Use direct path for Chrome driver in Replit environment
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as driver_error:
                st.warning(f"Error initializing Chrome driver: {str(driver_error)}")
                return self._get_mock_data("getMatchups")
            
            # Set up the cache file path
            cache_dir = os.path.join(os.getcwd(), "cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"matchups_week_{week if week else 'current'}.json")
            
            # Check if cache exists and is less than 6 hours old
            if os.path.exists(cache_file):
                cache_time = os.path.getmtime(cache_file)
                current_time = datetime.now().timestamp()
                # If cache is less than 6 hours old (21600 seconds)
                if current_time - cache_time < 21600:
                    with open(cache_file, 'r') as f:
                        st.info("Loading matchup data from cache.")
                        return json.load(f)
            
            st.info("Fetching matchup data from Fantrax... This may take a moment.")
            
            # Login flow
            driver.get("https://www.fantrax.com/login")
            
            # Wait for the login form to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mat-input-0"))
            )
            
            # Enter username
            username_field = driver.find_element(By.ID, "mat-input-0")
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = driver.find_element(By.ID, "mat-input-1")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete (dashboard to load)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard-page"))
            )
            
            # Navigate to the matchups page
            matchups_url = f"https://www.fantrax.com/fantasy/league/{league_id}/livescoring?mobileMatchupView=false"
            if week:
                matchups_url += f"&timeframeId={week}"
                
            driver.get(matchups_url)
            
            # Wait for the matchups to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ng-star-inserted"))
            )
            
            # Give some extra time for the page to render completely
            time.sleep(3)
            
            # Find all matchup containers
            matchup_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'matchupContainer')]")
            
            # Extract matchup data
            matchups = []
            
            for container in matchup_containers:
                try:
                    # Get team names
                    teams = container.find_elements(By.XPATH, ".//div[contains(@class, 'teamName')]")
                    if len(teams) < 2:
                        continue
                        
                    away_team = teams[0].text.strip()
                    home_team = teams[1].text.strip()
                    
                    # Get scores
                    scores = container.find_elements(By.XPATH, ".//div[contains(@class, 'teamScore')]")
                    if len(scores) < 2:
                        continue
                        
                    away_score_text = scores[0].text.strip()
                    home_score_text = scores[1].text.strip()
                    
                    # Parse scores with error handling
                    try:
                        away_score = float(away_score_text) if away_score_text else 0.0
                    except ValueError:
                        away_score = 0.0
                        
                    try:
                        home_score = float(home_score_text) if home_score_text else 0.0
                    except ValueError:
                        home_score = 0.0
                    
                    # Determine winner
                    winner = away_team if away_score > home_score else home_team if home_score > away_score else "Tie"
                    
                    # Calculate score difference
                    score_difference = abs(away_score - home_score)
                    
                    matchups.append({
                        "id": f"{away_team.lower().replace(' ', '_')}_vs_{home_team.lower().replace(' ', '_')}",
                        "away_team": away_team,
                        "home_team": home_team,
                        "away_score": away_score,
                        "home_score": home_score,
                        "winner": winner if away_score != home_score else "Tie",
                        "score_difference": score_difference,
                        "is_complete": False,  # Determine based on week status
                        "week": week if week else "current"
                    })
                    
                except Exception as e:
                    st.warning(f"Error parsing matchup: {str(e)}")
                    continue
            
            # Cache the matchup data
            with open(cache_file, 'w') as f:
                json.dump(matchups, f)
                
            return matchups
                
        except Exception as e:
            st.error(f"Error fetching matchups from Fantrax: {str(e)}")
            return self._get_mock_data("getMatchups")
        finally:
            if 'driver' in locals():
                driver.quit()