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

        matchups = data.get('matchups', [])
        first_matchup = matchups[0] if matchups else {}
        matchup_list = first_matchup.get('matchupList', [])

        settings = data.get('draftSettings', {})
        scoring_settings = data.get('scoringSettings', {})

        return {
            'name': "ABL Season 5",  # Hardcoded league name
            'season': "2025",  # Current season
            'sport': 'MLB',
            'scoring_type': "Head to Head",  # League format
            'teams': 30,  # Fixed number of teams
            'scoring_period': scoring_settings.get('scoringPeriod', 'Weekly')
        }

    def process_rosters(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        roster_list = []

        # Process rosters from API response
        period = roster_data.get('period', 1)
        rosters = roster_data.get('rosters', {})

        for team_id, team_data in rosters.items():
            team_name = team_data.get('teamName', 'Unknown')
            roster_items = team_data.get('rosterItems', [])

            for item in roster_items:
                if not isinstance(item, dict):
                    continue

                player_id = item.get('id')
                player_info = player_ids.get(player_id, {})

                # Get contract details
                contract = item.get('contract', {})

                player_record = {
                    'team': team_name,
                    'player_name': player_info.get('name', 'Unknown'),
                    'position': item.get('position', player_info.get('position', 'N/A')),
                    'status': item.get('status', 'Active'),
                    'salary': float(item.get('salary', 0.0)),
                    'mlb_team': player_info.get('team', 'N/A'),
                    'contract_year': contract.get('name', 'N/A') if contract else 'N/A'
                }
                roster_list.append(player_record)

        # Create DataFrame and clean up data
        result_df = pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
            columns=['team', 'player_name', 'position', 'mlb_team', 'status', 'salary', 'contract_year']
        )

        # Clean up player names (remove any unnecessary characters)
        result_df['player_name'] = result_df['player_name'].str.strip()

        return result_df

    def process_standings(self, standings_data: List) -> pd.DataFrame:
        """Process standings data into a DataFrame"""
        standings_list = []

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

        return pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
            columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
        )