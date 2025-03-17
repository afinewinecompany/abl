import pandas as pd
from typing import Dict, List, Union
import streamlit as st

class DataProcessor:
    def process_league_info(self, data: Dict) -> Dict:
        """Process league information data"""
        if not data or not isinstance(data, dict):
            return {
                'name': 'N/A',
                'season': 'N/A',
                'sport': 'MLB',
                'scoring_type': 'N/A',
                'teams': 0
            }

        try:
            rosters = data.get('rosters', {})
            league_settings = data.get('leagueSettings', {})

            return {
                'name': data.get('leagueName', 'N/A'),
                'season': str(data.get('season', 'N/A')),
                'sport': 'MLB',
                'scoring_type': league_settings.get('scoringType', 'N/A'),
                'teams': len(rosters) if rosters else 0
            }
        except Exception as e:
            st.error(f"Error processing league info: {str(e)}")
            return {
                'name': 'N/A',
                'season': 'N/A',
                'sport': 'MLB',
                'scoring_type': 'N/A',
                'teams': 0
            }

    def process_rosters(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        roster_list = []

        try:
            rosters = roster_data.get('rosters', {})

            for team_id, team_data in rosters.items():
                team_name = team_data.get('teamName', 'Unknown')
                roster_items = team_data.get('rosterItems', [])

                for player in roster_items:
                    if not isinstance(player, dict):
                        continue

                    player_id = player.get('id')
                    player_details = player_ids.get(player_id, {})

                    status = player.get('status', 'Active')
                    if status.lower() == 'na':
                        status = 'Minors'

                    player_info = {
                        'team': team_name,
                        'player_name': player_details.get('name', player.get('name', 'Unknown')),
                        'position': player.get('position', 'N/A'),
                        'status': status,
                        'salary': player.get('salary', 0.0),
                        'mlb_team': player_details.get('team', 'N/A')
                    }
                    roster_list.append(player_info)

        except Exception as e:
            st.error(f"Error processing roster data: {str(e)}")

        return pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
            columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team']
        )

    def process_standings(self, standings_data: List) -> pd.DataFrame:
        """Process standings data into a DataFrame"""
        standings_list = []

        try:
            if isinstance(standings_data, dict):
                standings_data = standings_data.get('standings', [])

            for team in standings_data:
                if not isinstance(team, dict):
                    continue

                # Parse points string into components (format: "W-L-T")
                points_str = team.get('points', '0-0-0')
                wins, losses, ties = map(int, points_str.split('-'))

                team_stats = {
                    'team_name': team.get('teamName', 'Unknown'),
                    'team_id': team.get('teamId', 'N/A'),
                    'rank': team.get('rank', 0),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'winning_pct': team.get('winPercentage', 0.0),
                    'games_back': team.get('gamesBack', 0.0)
                }
                standings_list.append(team_stats)

        except Exception as e:
            st.error(f"Error processing standings data: {str(e)}")

        return pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
            columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
        )