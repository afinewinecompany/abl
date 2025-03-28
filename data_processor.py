import pandas as pd
from typing import Dict, List, Union
import unicodedata
import streamlit as st

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
            st.error(f"Error normalizing name '{name}': {str(e)}")
            return str(name).strip().lower() if name else ""

    def process_rosters(self, roster_data: Dict, player_ids: Dict) -> pd.DataFrame:
        """Process roster data and combine with player information"""
        try:
            roster_list = []
            seen_players = {}  # Track players globally across all teams

            if not roster_data or not isinstance(roster_data, dict):
                st.error("Invalid roster data format")
                return pd.DataFrame(columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team'])

            rosters = roster_data.get('rosters', {})

            for team_id, team_data in rosters.items():
                team_name = team_data.get('teamName', 'Unknown')
                roster_items = team_data.get('rosterItems', [])

                for player in roster_items:
                    if not isinstance(player, dict):
                        continue

                    player_id = player.get('id')
                    player_details = player_ids.get(player_id, {})

                    # Get player name and normalize
                    player_name = player_details.get('name', player.get('name', 'Unknown')).strip()
                    if not player_name or player_name == 'Unknown':
                        continue

                    normalized_name = self.normalize_name(player_name)
                    if not normalized_name:
                        continue

                    # Skip if we've already seen this player
                    if normalized_name in seen_players:
                        continue

                    # Process status
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

            # Create DataFrame
            df = pd.DataFrame(roster_list) if roster_list else pd.DataFrame(
                columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team']
            )

            return df

        except Exception as e:
            st.error(f"Error processing roster data: {str(e)}")
            return pd.DataFrame(
                columns=['team', 'player_name', 'position', 'status', 'salary', 'mlb_team']
            )

    def process_league_info(self, data: Dict) -> Dict:
        """Process league information data"""
        try:
            if not data or not isinstance(data, dict):
                return {
                    'name': 'N/A',
                    'season': 'N/A',
                    'sport': 'MLB',
                    'scoring_type': 'N/A',
                    'teams': 0,
                    'scoring_period': 'N/A'
                }

            settings = data.get('draftSettings', {})
            scoring_settings = data.get('scoringSettings', {})

            return {
                'name': data.get('name', "ABL Season 5"),
                'season': data.get('season', "2025"),
                'sport': data.get('sport', 'MLB'),
                'scoring_type': data.get('scoringType', "Head to Head"),
                'teams': data.get('teams', 30),
                'scoring_period': scoring_settings.get('scoringPeriod', 'Weekly')
            }
        except Exception as e:
            st.error(f"Error processing league info: {str(e)}")
            return {
                'name': 'N/A',
                'season': 'N/A',
                'sport': 'MLB',
                'scoring_type': 'N/A',
                'teams': 0,
                'scoring_period': 'N/A'
            }

    def process_standings(self, standings_data: List) -> pd.DataFrame:
        """
        Process standings data into a DataFrame with enhanced fields for power rankings
        """
        try:
            if not standings_data or not isinstance(standings_data, list):
                return pd.DataFrame(
                    columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                             'games_back', 'points_for', 'points_against', 'streak', 'last_10']
                )

            standings_list = []

            for team in standings_data:
                if not isinstance(team, dict):
                    continue

                # Parse record from points string (format: "W-L-T")
                points_str = team.get('points', '0-0-0')
                try:
                    wins, losses, ties = map(int, points_str.split('-'))
                except (ValueError, AttributeError):
                    wins, losses, ties = 0, 0, 0
                
                # Extract the direction (W/L) and number from streak
                streak_desc = team.get('streakDescription', '')
                streak_direction = streak_desc[0] if streak_desc else ''
                streak_count = int(streak_desc[1:]) if len(streak_desc) > 1 and streak_desc[1:].isdigit() else 0
                
                # Calculate points for and against if available
                points_for = team.get('pointsFor', 0.0)
                points_against = team.get('pointsAgainst', 0.0)
                
                # Create enhanced team stats dictionary
                team_stats = {
                    'team_name': team.get('teamName', 'Unknown'),
                    'team_id': team.get('teamId', 'N/A'),
                    'rank': team.get('rank', 0),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'winning_pct': team.get('winPercentage', 0.0),
                    'games_back': team.get('gamesBack', 0.0),
                    'points_for': float(points_for if points_for else 0.0),
                    'points_against': float(points_against if points_against else 0.0),
                    'streak_direction': streak_direction,
                    'streak_count': streak_count,
                    'streak': streak_desc
                }
                standings_list.append(team_stats)

            df = pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                         'games_back', 'points_for', 'points_against', 'streak', 'streak_direction', 'streak_count']
            )

            # Calculate additional metrics for power rankings
            if not df.empty:
                # Total games played
                df['games_played'] = df['wins'] + df['losses'] + df['ties']
                
                # Points per game
                df['points_per_game'] = df.apply(
                    lambda row: row['points_for'] / row['games_played'] if row['games_played'] > 0 else 0, 
                    axis=1
                )
                
                # Initialize total_points and weeks_played for power rankings calculation
                df['total_points'] = df['points_for']
                df['weeks_played'] = df['games_played'].apply(lambda x: max(x, 1))  # Avoid division by zero
            
            # Ensure rank is numeric and sort by it
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce').fillna(0).astype(int)
            df = df.sort_values('rank', ascending=True).reset_index(drop=True)

            return df

        except Exception as e:
            st.error(f"Error processing standings: {str(e)}")
            return pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                         'games_back', 'points_for', 'points_against', 'streak']
            )