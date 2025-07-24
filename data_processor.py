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
            st.sidebar.info(f"Processing roster data for {len(rosters)} teams")
            
            # Debug: Show team names being processed
            team_names = [team_data.get('teamName', 'Unknown') for team_data in rosters.values()]
            st.sidebar.info(f"Teams found: {', '.join(team_names[:5])}{'...' if len(team_names) > 5 else ''}")

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
            
            st.sidebar.success(f"Processed {len(df)} total players across all teams")
            if len(df) > 0:
                unique_teams = df['team'].nunique()
                st.sidebar.info(f"Data contains {unique_teams} unique teams with roster assignments")

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
            # Debug raw standings data
            st.sidebar.info("Processing API standings data...")
            
            if not standings_data:
                st.sidebar.error("No standings data received from API")
                return pd.DataFrame(
                    columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                             'games_back', 'points_for', 'points_against', 'streak', 'fptsf']
                )
                
            # Handle non-list data
            if not isinstance(standings_data, list):
                st.sidebar.error(f"Unexpected standings data format: {type(standings_data)}")
                # If it's a dict with a 'standings' key, try to extract that
                if isinstance(standings_data, dict) and 'standings' in standings_data:
                    standings_data = standings_data.get('standings', [])
                    st.sidebar.info(f"Extracted standings from dictionary: found {len(standings_data)} teams")
                # If it's still not a list, create an empty DataFrame
                if not isinstance(standings_data, list):
                    return pd.DataFrame(
                        columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                                'games_back', 'points_for', 'points_against', 'streak', 'fptsf']
                    )

            standings_list = []

            for i, team in enumerate(standings_data):
                # Skip non-dictionary team data
                if not isinstance(team, dict):
                    continue
                
                # Extract team name - handle different key formats from API
                team_name = team.get('teamName', team.get('team_name', 'Unknown'))
                if team_name == 'Unknown' and 'name' in team:
                    team_name = team.get('name', 'Unknown')
                
                # Debug the first few team records to understand structure
                if i < 2:
                    st.sidebar.success(f"Processing team data for: {team_name}")
                    if 'points' in team:
                        st.sidebar.info(f"Points format: {team.get('points', 'Not available')}")
                    if 'pointsFor' in team:
                        st.sidebar.info(f"Points For: {team.get('pointsFor', 0)}")
                    if 'fptsf' in team:
                        st.sidebar.info(f"FPTSF: {team.get('fptsf', 0)}")
                
                # Try to parse record - different formats possible
                wins, losses, ties = 0, 0, 0
                
                # Format 1: 'points' string as "W-L-T"
                if 'points' in team:
                    points_str = str(team.get('points', '0-0-0'))
                    try:
                        parts = points_str.split('-')
                        if len(parts) >= 3:
                            wins = int(parts[0])
                            losses = int(parts[1])
                            ties = int(parts[2])
                    except (ValueError, AttributeError, IndexError):
                        # If parsing fails, try other methods
                        pass
                
                # Format 2: Separate wins/losses/ties fields
                if wins == 0 and losses == 0 and ties == 0:
                    wins = int(team.get('wins', 0))
                    losses = int(team.get('losses', 0))
                    ties = int(team.get('ties', 0))
                
                # Calculate win percentage if not provided
                win_pct = team.get('winPercentage', 0.0)
                if win_pct == 0.0 and (wins + losses + ties > 0):
                    win_pct = (wins + (ties * 0.5)) / (wins + losses + ties)
                
                # Handle streak info
                streak_desc = str(team.get('streakDescription', team.get('streak', '')))
                streak_direction = streak_desc[0] if streak_desc and len(streak_desc) > 0 else ''
                streak_count = 0
                if len(streak_desc) > 1 and streak_desc[1:].isdigit():
                    try:
                        streak_count = int(streak_desc[1:])
                    except (ValueError, IndexError):
                        streak_count = 0
                
                # Handle various points formats
                points_for = 0.0
                # Try multiple possible keys for points
                for key in ['pointsFor', 'points_for', 'fpts', 'fptsf']:
                    if key in team:
                        try:
                            value = team.get(key, 0)
                            if value:
                                points_for = float(value)
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Points against
                points_against = 0.0
                for key in ['pointsAgainst', 'points_against', 'fptsa']:
                    if key in team:
                        try:
                            value = team.get(key, 0)
                            if value:
                                points_against = float(value)
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Create enhanced team stats dictionary with all possible data points
                team_stats = {
                    'team_name': team_name,
                    'team_id': team.get('teamId', team.get('team_id', 'N/A')),
                    'rank': int(team.get('rank', i+1)),  # Fall back to index+1 if no rank
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'winning_pct': float(win_pct),
                    'games_back': float(team.get('gamesBack', 0.0)),
                    'points_for': points_for,
                    'points_against': points_against,
                    'streak_direction': streak_direction,
                    'streak_count': streak_count,
                    'streak': streak_desc,
                    # Add Fantasy Points Scored For - critical for power rankings
                    'fptsf': float(team.get('fptsf', points_for))
                }
                standings_list.append(team_stats)

            # Create DataFrame from processed data
            if not standings_list:
                st.sidebar.warning("No valid team data found in standings response")
                return pd.DataFrame(
                    columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                            'games_back', 'points_for', 'points_against', 'streak', 'fptsf']
                )
            
            df = pd.DataFrame(standings_list)

            # Calculate additional metrics for power rankings
            if not df.empty:
                # Total games played
                df['games_played'] = df['wins'] + df['losses'] + df['ties']
                
                # Points per game (safely handle division by zero)
                df['points_per_game'] = df.apply(
                    lambda row: row['points_for'] / max(row['games_played'], 1), 
                    axis=1
                )
                
                # Initialize total_points and weeks_played for power rankings calculation
                df['total_points'] = df['points_for']
                df['weeks_played'] = df['games_played'].apply(lambda x: max(x, 1))  # Avoid division by zero
                
                # Make sure we have a 'fptsf' column even if it wasn't in the data
                if 'fptsf' not in df.columns:
                    df['fptsf'] = df['points_for']
                
                # Success message if we have team data
                st.sidebar.success(f"Successfully processed standings data for {len(df)} teams")
            
            # Ensure rank is numeric and sort by it
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce').fillna(0).astype(int)
            df = df.sort_values('rank', ascending=True).reset_index(drop=True)

            return df

        except Exception as e:
            st.error(f"Error processing standings: {str(e)}")
            import traceback
            st.sidebar.error(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 
                        'games_back', 'points_for', 'points_against', 'streak', 'fptsf']
            )