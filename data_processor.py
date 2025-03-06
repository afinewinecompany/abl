import pandas as pd
from typing import Dict, List, Union

class DataProcessor:
    def process_league_info(self, data: Union[Dict, List]) -> Dict:
        """Process league information data"""
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        elif not isinstance(data, dict):
            return {
                'name': 'N/A',
                'season': 'N/A',
                'sport': 'MLB',
                'scoring_type': 'N/A',
                'teams': 0
            }

        return {
            'name': data.get('name', 'N/A'),
            'season': data.get('season', 'N/A'),
            'sport': data.get('sport', 'MLB'),
            'scoring_type': data.get('scoringType', 'N/A'),
            'teams': data.get('numTeams', 0)
        }

    def process_rosters(self, roster_data: Union[Dict, List], player_ids: Union[Dict, List]) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        roster_list = []

        # Handle if roster_data is a list
        teams = roster_data.get('teams', []) if isinstance(roster_data, dict) else roster_data

        for team in teams:
            if not isinstance(team, dict):
                continue

            team_name = team.get('name', 'Unknown')
            players = team.get('players', [])

            if isinstance(players, list):
                for player in players:
                    if not isinstance(player, dict):
                        continue

                    player_info = {
                        'team': team_name,
                        'player_name': player.get('name', 'Unknown'),
                        'position': player.get('position', 'N/A'),
                        'team_mlb': player.get('team', 'N/A'),
                        'status': player.get('status', 'Active')
                    }
                    roster_list.append(player_info)

        return pd.DataFrame(roster_list) if roster_list else pd.DataFrame(columns=['team', 'player_name', 'position', 'team_mlb', 'status'])

    def process_standings(self, standings_data: Union[Dict, List]) -> pd.DataFrame:
        """Process standings data into a DataFrame"""
        standings_list = []

        # Handle if standings_data is a list
        teams = standings_data.get('teams', []) if isinstance(standings_data, dict) else standings_data

        for team in teams:
            if not isinstance(team, dict):
                continue

            team_stats = {
                'team_name': team.get('name', 'Unknown'),
                'rank': team.get('rank', 0),
                'points': team.get('points', 0),
                'wins': team.get('wins', 0),
                'losses': team.get('losses', 0),
                'ties': team.get('ties', 0),
                'winning_pct': team.get('winningPercentage', 0.0)
            }
            standings_list.append(team_stats)

        return pd.DataFrame(standings_list) if standings_list else pd.DataFrame(columns=['team_name', 'rank', 'points', 'wins', 'losses', 'ties', 'winning_pct'])