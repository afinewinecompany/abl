import pandas as pd
from typing import Dict, List, Union
import unicodedata
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def normalize_name(self, name: str) -> str:
        """Normalize player name for comparison"""
        try:
            if not name or pd.isna(name):
                return ""
            name = str(name).lower()
            name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
            if ',' in name:
                last, first = name.split(',', 1)
                name = f"{first.strip()} {last.strip()}"
            name = name.split('(')[0].strip()
            name = name.split(' - ')[0].strip()
            name = name.replace('.', '').strip()
            name = ' '.join(name.split())
            return name
        except Exception as e:
            logger.error(f"Error normalizing name '{name}': {str(e)}")
            return str(name).strip().lower() if name else ""

    def process_rosters(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        try:
            roster_list = []
            seen_players = {}  # Track players globally across all teams

            if not roster_data or not isinstance(roster_data, dict):
                logger.warning("Invalid roster data format, returning empty DataFrame")
                return pd.DataFrame(columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team'])

            rosters = roster_data.get('rosters', {})
            logger.debug(f"Processing {len(rosters)} teams")

            for team_id, team_data in rosters.items():
                team_name = team_data.get('teamName', 'Unknown')
                roster_items = team_data.get('rosterItems', [])

                for player in roster_items:
                    if not isinstance(player, dict):
                        continue

                    player_id = player.get('id')
                    player_details = player_ids.get(player_id, {})

                    player_name = player_details.get('name', player.get('name', 'Unknown')).strip()
                    if not player_name or player_name == 'Unknown':
                        continue

                    normalized_name = self.normalize_name(player_name)
                    if not normalized_name:
                        continue

                    if normalized_name in seen_players:
                        continue

                    status = player.get('status', 'Active')
                    if status.lower() == 'na':
                        status = 'Minors'

                    player_info = {
                        'team': team_name,
                        'player_name': player_name,
                        'position': player.get('position', 'N/A'),
                        'status': status,
                        'salary': player.get('salary', 0.0),
                        'mlb_team': player_details.get('team', 'N/A')
                    }
                    roster_list.append(player_info)
                    seen_players[normalized_name] = True

            df = pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
                columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team']
            )
            logger.debug(f"Processed {len(df)} players")
            return df

        except Exception as e:
            logger.error(f"Error processing roster data: {str(e)}")
            return pd.DataFrame(
                columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team']
            )

    def process_league_info(self, data: Dict) -> Dict:
        """Process league information data"""
        try:
            if not data or not isinstance(data, dict):
                logger.warning("Invalid league info data, returning default values")
                return {
                    'name': 'ABL Season 5',
                    'season': '2025',
                    'sport': 'MLB',
                    'scoring_type': 'Head to Head',
                    'teams': 30,
                    'scoring_period': 'Weekly'
                }

            logger.debug("Processing league info data")
            return {
                'name': data.get('name', 'ABL Season 5'),
                'season': data.get('season', '2025'),
                'sport': data.get('sport', 'MLB'),
                'scoring_type': data.get('scoringType', 'Head to Head'),
                'teams': data.get('teams', 30),
                'scoring_period': data.get('scoringPeriod', 'Weekly')
            }
        except Exception as e:
            logger.error(f"Error processing league info: {str(e)}")
            return {
                'name': 'ABL Season 5',
                'season': '2025',
                'sport': 'MLB',
                'scoring_type': 'Head to Head',
                'teams': 30,
                'scoring_period': 'Weekly'
            }

    def process_standings(self, standings_data: List) -> pd.DataFrame:
        """Process standings data into a DataFrame"""
        try:
            if not isinstance(standings_data, list):
                logger.warning("Invalid standings data format, returning empty DataFrame")
                standings_data = []

            standings_list = []
            logger.debug(f"Processing {len(standings_data)} teams in standings")

            for team in standings_data:
                if not isinstance(team, dict):
                    continue

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

            return pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
            )
        except Exception as e:
            logger.error(f"Error processing standings: {str(e)}")
            return pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
            )