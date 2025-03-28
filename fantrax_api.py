import requests
import pandas as pd
import json
import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class FantraxClient:
    def __init__(self, league_id):
        self.league_id = league_id
        self.auth_token = os.getenv("FANTRAX_TOKEN")
        self.base_url = f"https://www.fantrax.com/fantasy/league/{self.league_id}/livescoring?mobileMatchupView=false"
    
    def is_authenticated(self) -> bool:
        """Check if token is available and valid"""
        return bool(self.auth_token)
    
    def get_live_scoring(self, scoring_period):
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login.py first.")
        
        api_url = "https://www.fantrax.com/fxpa/req/league/liveScoring"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "leagueId": self.league_id,
            "scoringPeriod": scoring_period
        }
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching live scoring: {response.status_code}")

    def parse_matchups(self, data):
        matchups = []
        periods = data.get("liveScoringMatchups", [])
        for m in periods:
            matchup = {
                "matchupId": m["id"],
                "team1": m["home"]["team"]["name"],
                "team1Score": m["home"]["score"],
                "team2": m["away"]["team"]["name"],
                "team2Score": m["away"]["score"]
            }
            matchups.append(matchup)
        return pd.DataFrame(matchups)
    
    def get_league_info(self) -> Dict[str, Any]:
        """Get league information"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        api_url = "https://www.fantrax.com/fxea/general/getLeagueInfo"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        params = {
            "leagueId": self.league_id
        }
        
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching league info: {response.status_code}")

    def get_standings(self) -> List[Dict[str, Any]]:
        """Get current standings"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        api_url = "https://www.fantrax.com/fxpa/req/league/standings"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "leagueId": self.league_id
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            standings = []
            
            for team in data.get("teams", []):
                team_data = {
                    "teamId": team.get("id", ""),
                    "teamName": team.get("name", ""),
                    "wins": team.get("wins", 0),
                    "losses": team.get("losses", 0),
                    "ties": team.get("ties", 0),
                    "points": team.get("points", 0.0)
                }
                standings.append(team_data)
                
            return standings
        else:
            raise Exception(f"Error fetching standings: {response.status_code}")

    def get_team_rosters(self) -> Dict[str, Any]:
        """Get team rosters"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        api_url = "https://www.fantrax.com/fxpa/req/rosters"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "leagueId": self.league_id
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching rosters: {response.status_code}")

    def get_scoring_periods(self) -> List[Dict[str, Any]]:
        """Get scoring periods"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        api_url = "https://www.fantrax.com/fxpa/req/league/periodSettings"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "leagueId": self.league_id
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            periods = []
            
            for period in data.get("periods", []):
                period_data = {
                    "id": period.get("id", 0),
                    "startDate": period.get("startDate", ""),
                    "endDate": period.get("endDate", ""),
                    "isCurrent": period.get("isCurrent", False)
                }
                periods.append(period_data)
                
            return periods
        else:
            raise Exception(f"Error fetching scoring periods: {response.status_code}")

    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        api_url = "https://www.fantrax.com/fxpa/req/transactions"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "leagueId": self.league_id,
            "count": limit
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            transactions = []
            
            for tx in data.get("transactions", []):
                tx_data = {
                    "id": tx.get("id", ""),
                    "date": tx.get("date", ""),
                    "type": tx.get("type", ""),
                    "description": tx.get("description", ""),
                    "teamId": tx.get("teamId", ""),
                    "teamName": tx.get("teamName", "")
                }
                transactions.append(tx_data)
                
            return transactions
        else:
            raise Exception(f"Error fetching transactions: {response.status_code}")

    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams"""
        if not self.auth_token:
            raise ValueError("Missing FANTRAX_TOKEN. Please run selenium_login first.")
        
        # Teams can be extracted from standings or roster data
        standings = self.get_standings()
        teams = []
        
        for team in standings:
            team_data = {
                "id": team.get("teamId", ""),
                "name": team.get("teamName", ""),
                "owner": team.get("teamName", "").split(' ')[0]  # Use first part of team name as owner
            }
            teams.append(team_data)
            
        return teams