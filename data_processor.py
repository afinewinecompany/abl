import pandas as pd
from typing import Dict, List, Union

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

        # Extract from draftSettings or main data
        settings = data.get('draftSettings', {})
        return {
            'name': data.get('leagueName', 'N/A'),
            'season': str(data.get('season', 'N/A')),
            'sport': 'MLB',
            'scoring_type': settings.get('draftType', 'N/A'),
            'teams': len(data.get('matchups', [{}])[0].get('matchupList', []))
        }

    def process_rosters(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        roster_list = []
        rosters = roster_data.get('rosters', {})

        for team_id, team_data in rosters.items():
            team_name = team_data.get('teamName', 'Unknown')
            roster_items = team_data.get('rosterItems', [])

            for player in roster_items:
                if not isinstance(player, dict):
                    continue

                player_info = {
                    'team': team_name,
                    'player_name': player.get('name', 'Unknown'),
                    'position': player.get('position', 'N/A'),
                    'status': player.get('status', 'Active'),
                    'salary': player.get('salary', 0.0)
                }
                roster_list.append(player_info)

        return pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
            columns=['team', 'player_name', 'position', 'status', 'salary']
        )

    def process_standings(self, standings_data: List) -> pd.DataFrame:
        """Process standings data into a DataFrame"""
        standings_list = []

        for team in standings_data:
            if not isinstance(team, dict):
                continue

            team_stats = {
                'team_name': team.get('teamName', 'Unknown'),
                'team_id': team.get('teamId', 'N/A'),
                'rank': team.get('rank', 0),
                'points': team.get('points', '0-0-0'),
                'winning_pct': team.get('winPercentage', 0.0),
                'games_back': team.get('gamesBack', 0.0)
            }
            standings_list.append(team_stats)

        return pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
            columns=['team_name', 'team_id', 'rank', 'points', 'winning_pct', 'games_back']
        )