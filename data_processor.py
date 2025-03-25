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
        """Process standings data into a DataFrame"""
        try:
            if not standings_data or not isinstance(standings_data, list):
                return pd.DataFrame(
                    columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
                )

            standings_list = []

            for team in standings_data:
                if not isinstance(team, dict):
                    continue

                # Default to '0-0-0' if points not found
                points_str = team.get('points', '0-0-0')
                try:
                    wins, losses, ties = map(int, points_str.split('-'))
                except (ValueError, AttributeError):
                    wins, losses, ties = 0, 0, 0

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

            df = pd.DataFrame(standings_list) if standings_list else pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
            )

            # Ensure rank is numeric and sort by it
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce').fillna(0).astype(int)
            df = df.sort_values('rank', ascending=True).reset_index(drop=True)

            return df

        except Exception as e:
            st.error(f"Error processing standings: {str(e)}")
            return pd.DataFrame(
                columns=['team_name', 'team_id', 'rank', 'wins', 'losses', 'ties', 'winning_pct', 'games_back']
            )
            
    def process_available_players(self, players_data: Dict) -> pd.DataFrame:
        """Process available players data into a DataFrame"""
        try:
            if not players_data or not isinstance(players_data, dict):
                st.warning("No valid player data received")
                return pd.DataFrame(
                    columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'stats']
                )
            
            # Get players list
            players_list = []
            players = players_data.get('players', [])
            
            if not players:
                st.warning("No players found in the data")
                # Debug information only shown if there's an issue
                st.info(f"Available data keys: {list(players_data.keys())}")
                return pd.DataFrame(
                    columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'stats']
                )
            
            for player in players:
                if not isinstance(player, dict):
                    continue
                    
                # Extract player details - adapting to Fantrax's specific structure
                player_id = player.get('id', player.get('playerId', ''))
                player_name = player.get('name', player.get('playerName', 'Unknown'))
                
                # For position - try multiple possible keys
                position = 'N/A'
                position_keys = ['position', 'pos', 'primaryPosition']
                for key in position_keys:
                    if key in player:
                        position = player[key]
                        break
                
                # Similar approach for team
                mlb_team = 'N/A'
                team_keys = ['team', 'mlbTeam', 'proTeamAbbreviation']
                for key in team_keys:
                    if key in player:
                        mlb_team = player[key]
                        break
                
                # And status
                status = 'Active'
                status_keys = ['status', 'playerStatus', 'rosterStatus']
                for key in status_keys:
                    if key in player:
                        status_val = player[key]
                        # Handle different status formats
                        if status_val and isinstance(status_val, str):
                            if status_val.lower() in ['active', 'a']:
                                status = 'Active'
                            elif status_val.lower() in ['injured', 'il', 'i']:
                                status = 'IL'
                            elif status_val.lower() in ['na', 'n', 'minors']:
                                status = 'Minors'
                            else:
                                status = status_val
                        break
                
                # Process eligibility - could be in different formats
                eligible_positions = []
                
                # Check for eligibility array
                if 'eligibility' in player and isinstance(player['eligibility'], list):
                    eligible_positions = []
                    for pos in player['eligibility']:
                        if isinstance(pos, dict) and 'shortName' in pos:
                            eligible_positions.append(pos['shortName'])
                        elif isinstance(pos, str):
                            eligible_positions.append(pos)
                # Check for positions array - both string array and object array formats
                elif 'positions' in player and isinstance(player['positions'], list):
                    eligible_positions = []
                    for pos in player['positions']:
                        if isinstance(pos, str):
                            eligible_positions.append(pos)
                        elif isinstance(pos, dict) and 'shortName' in pos:
                            eligible_positions.append(pos['shortName'])
                        elif isinstance(pos, dict) and 'name' in pos:
                            eligible_positions.append(pos['name'])
                
                # Stats processing - handle different formats
                stats = {}
                
                # Check if stats is directly in player object
                if 'stats' in player:
                    player_stats = player['stats']
                    
                    # Could be dict with hitting/pitching keys
                    if isinstance(player_stats, dict):
                        # First check for hitting/pitching structure
                        if 'hitting' in player_stats:
                            hitting = player_stats['hitting']
                            if isinstance(hitting, dict):
                                for stat_name, stat_value in hitting.items():
                                    stats[f'hit_{stat_name}'] = stat_value
                        
                        if 'pitching' in player_stats:
                            pitching = player_stats['pitching']
                            if isinstance(pitching, dict):
                                for stat_name, stat_value in pitching.items():
                                    stats[f'pit_{stat_name}'] = stat_value
                                    
                        # If not that structure, might be direct stat keys
                        for stat_name, stat_value in player_stats.items():
                            if stat_name not in ['hitting', 'pitching'] and not stat_name.startswith('hit_') and not stat_name.startswith('pit_'):
                                # Determine if hitting or pitching stat
                                if stat_name in ['AVG', 'HR', 'RBI', 'R', 'SB', 'OBP', 'OPS', 'H', '2B', '3B', 'BB', 'PA', 'AB']:
                                    stats[f'hit_{stat_name}'] = stat_value
                                elif stat_name in ['ERA', 'WHIP', 'W', 'SV', 'SO', 'QS', 'IP', 'H', 'ER', 'HLD', 'BB']:
                                    stats[f'pit_{stat_name}'] = stat_value
                                else:
                                    stats[stat_name] = stat_value
                
                # Process any stats directly in player object (common in Fantrax)
                stat_keys = ['AVG', 'HR', 'RBI', 'R', 'SB', 'OBP', 'OPS', 'ERA', 'WHIP', 'W', 'SV', 'SO', 'QS']
                for key in stat_keys:
                    if key in player and key not in stats:
                        # Determine category
                        if key in ['AVG', 'HR', 'RBI', 'R', 'SB', 'OBP', 'OPS']:
                            stats[f'hit_{key}'] = player[key]
                        elif key in ['ERA', 'WHIP', 'W', 'SV', 'SO', 'QS']:
                            stats[f'pit_{key}'] = player[key]
                        else:
                            stats[key] = player[key]
                
                player_info = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': position,
                    'mlb_team': mlb_team,
                    'status': status,
                    'eligible_positions': eligible_positions,
                    'stats': stats
                }
                
                players_list.append(player_info)
                
            # Create DataFrame
            df = pd.DataFrame(players_list) if players_list else pd.DataFrame(
                columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'eligible_positions', 'stats']
            )
            
            # Only show success message if we have a small number of players (likely debugging)
            if len(df) < 10:
                st.success(f"Successfully processed {len(df)} players")
            return df
            
        except Exception as e:
            st.error(f"Error processing available players: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return pd.DataFrame(
                columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'eligible_positions', 'stats']
            )