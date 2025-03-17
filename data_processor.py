import pandas as pd
from typing import Dict, List, Union
import unicodedata

class DataProcessor:
    def normalize_name(self, name: str) -> str:
        """Normalize player name for comparison"""
        try:
            name = name.lower()
            name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
            if ',' in name:
                last, first = name.split(',', 1)
                name = f"{first.strip()} {last.strip()}"
            name = name.split('(')[0].strip()
            name = name.split(' - ')[0].strip()
            name = name.replace('.', '').strip()
            name = ' '.join(name.split())
            return name
        except:
            return name.strip().lower()

    def process_roster_data(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        roster_list = []
        seen_players = {}  # Track players globally across all teams
        rosters = roster_data.get('rosters', {})

        for team_id, team_data in rosters.items():
            team_name = team_data.get('teamName', 'Unknown')
            roster_items = team_data.get('rosterItems', [])

            for player in roster_items:
                if not isinstance(player, dict):
                    continue

                player_id = player.get('id')
                player_details = player_ids.get(player_id, {})

                # Normalize player name for consistent comparison
                player_name = player_details.get('name', player.get('name', 'Unknown')).strip()
                if not player_name or player_name == 'Unknown':
                    continue

                # Create normalized key for comparison
                normalized_name = self.normalize_name(player_name)

                # Skip if we've already seen this player
                if normalized_name in seen_players:
                    continue

                # Get original status and only convert NA to Minors
                status = player.get('status', 'Active')
                if status.lower() == 'na':
                    status = 'Minors'

                player_info = {
                    'team': team_name,
                    'player_name': player_name,
                    'position': player.get('position', 'N/A'),
                    'status': status,
                    'salary': player.get('salary', 0.0),
                    'mlb_team': player_details.get('team', 'N/A'),
                    'normalized_name': normalized_name  # Add normalized name for consistency
                }
                roster_list.append(player_info)
                seen_players[normalized_name] = True

        # Create DataFrame and ensure no duplicates
        df = pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
            columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team', 'normalized_name']
        )

        # Drop duplicates keeping the first occurrence
        df = df.drop_duplicates(subset=['normalized_name'], keep='first')

        # Remove the normalized_name column as it's no longer needed
        df = df.drop(columns=['normalized_name'])

        return df

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