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
                # Only show warning if this isn't first load (silent fail on first load)
                if 'loaded_once' in st.session_state and st.session_state.loaded_once:
                    st.warning("No valid player data received from Fantrax API")
                return pd.DataFrame(
                    columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'stats']
                )
            
            # Mark that we've tried to load once
            st.session_state.loaded_once = True
            
            # Get players list - check multiple potential structures
            players_list = []
            players = []
            
            # Try to find players in different places in the response
            if 'players' in players_data:
                players = players_data['players']
            elif 'msgs' in players_data and len(players_data['msgs']) > 0:
                msg = players_data['msgs'][0]
                if 'data' in msg:
                    data = msg['data']
                    if 'players' in data:
                        players = data['players'] 
                    elif 'playerInfo' in data:
                        players = data['playerInfo']
                    elif 'poolData' in data and isinstance(data['poolData'], dict):
                        pool_data = data['poolData']
                        if 'playerInfo' in pool_data:
                            players = pool_data['playerInfo']
            
            if not players:
                st.error("Could not find player data in the Fantrax API response")
                # Show detailed debug info
                st.info(f"API response structure: {str(players_data.keys())}")
                
                # Try to examine the response to give more helpful error info
                if 'error' in players_data:
                    st.error(f"API error: {players_data['error']}")
                elif 'msg' in players_data:
                    st.error(f"API message: {players_data['msg']}")
                elif 'msgs' in players_data and len(players_data['msgs']) > 0:
                    for msg in players_data['msgs']:
                        if 'error' in msg:
                            st.error(f"API error in message: {msg['error']}")
                
                return pd.DataFrame(
                    columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'stats']
                )
            
            # Process each player
            for player in players:
                if not isinstance(player, dict):
                    continue
                    
                # Extract player details - handle multiple potential structures
                player_id = player.get('id', player.get('playerId', ''))
                
                # Name could be in several locations - prioritize 'name' field
                player_name = None
                
                # IMPORTANT: Direct check for 'name' field since that's the exact header we need
                if 'name' in player and player['name']:
                    player_name = player['name']
                else:
                    # Fall back to other possible name fields
                    name_keys = ['playerName', 'fullName', 'firstName', 'lastName']
                    for key in name_keys:
                        if key in player and player[key]:
                            if key == 'firstName' and 'lastName' in player:
                                # If we have separate first/last name fields
                                player_name = f"{player['firstName']} {player['lastName']}"
                                break
                            elif key != 'firstName' and key != 'lastName':
                                player_name = player[key]
                                break
                
                # Debug print for player name field
                if st.session_state.get('debug_mode', False):
                    st.write(f"Player object keys: {list(player.keys())}")
                    if 'name' in player:
                        st.write(f"Found 'name' field: {player['name']}")
                
                # If we still don't have a name, skip this player
                if not player_name:
                    continue
                
                # For position - check multiple possible keys
                position = 'N/A'
                position_keys = ['position', 'pos', 'primaryPosition', 'defaultPositionId']
                for key in position_keys:
                    if key in player and player[key]:
                        position_val = player[key]
                        # Handle position IDs (convert to readable position)
                        if key == 'defaultPositionId' and isinstance(position_val, (int, str)):
                            # Map position IDs to readable positions
                            position_map = {
                                '1': 'SP', '2': 'C', '3': '1B', '4': '2B', '5': '3B', '6': 'SS',
                                '7': 'OF', '8': 'OF', '9': 'OF', '10': 'DH', '11': 'RP'
                            }
                            position = position_map.get(str(position_val), str(position_val))
                        else:
                            position = str(position_val)
                        break
                
                # For MLB team - check multiple possible keys
                mlb_team = 'N/A'
                team_keys = ['team', 'mlbTeam', 'proTeamAbbreviation', 'teamAbbrev', 'proTeam']
                for key in team_keys:
                    if key in player and player[key]:
                        team_val = player[key]
                        # Handle team IDs (convert to abbreviations)
                        if key == 'proTeam' and isinstance(team_val, (int, str)) and str(team_val).isdigit():
                            # Map team IDs to abbreviations
                            team_map = {
                                '1': 'BAL', '2': 'BOS', '3': 'LAA', '4': 'CWS', '5': 'CLE', '6': 'DET',
                                '7': 'KC', '8': 'MIL', '9': 'MIN', '10': 'NYY', '11': 'OAK', '12': 'SEA',
                                '13': 'TEX', '14': 'TOR', '15': 'ATL', '16': 'CHC', '17': 'CIN',
                                '18': 'HOU', '19': 'LAD', '20': 'WSH', '21': 'NYM', '22': 'PHI',
                                '23': 'PIT', '24': 'STL', '25': 'SD', '26': 'SF', '27': 'COL',
                                '28': 'MIA', '29': 'ARI', '30': 'TB'
                            }
                            mlb_team = team_map.get(str(team_val), 'N/A')
                        else:
                            mlb_team = str(team_val)
                        break
                
                # For player status - check multiple possible keys
                status = 'Active'
                status_keys = ['status', 'playerStatus', 'rosterStatus', 'injuryStatus']
                for key in status_keys:
                    if key in player and player[key]:
                        status_val = player[key]
                        # Handle different status formats
                        if isinstance(status_val, str):
                            status_val = status_val.lower()
                            if status_val in ['active', 'a']:
                                status = 'Active'
                            elif any(s in status_val for s in ['injured', 'il', 'i', 'dl']):
                                status = 'IL'
                            elif any(s in status_val for s in ['na', 'n', 'minors', 'minor']):
                                status = 'Minors'
                            else:
                                status = player[key]
                            break
                
                # Process eligibility - could be in different formats
                eligible_positions = []
                
                # Check for eligibility array
                if 'eligibility' in player and isinstance(player['eligibility'], list):
                    for pos in player['eligibility']:
                        if isinstance(pos, dict) and 'shortName' in pos:
                            eligible_positions.append(pos['shortName'])
                        elif isinstance(pos, str):
                            eligible_positions.append(pos)
                # Check for positions array
                elif 'positions' in player and isinstance(player['positions'], list):
                    for pos in player['positions']:
                        if isinstance(pos, str):
                            eligible_positions.append(pos)
                        elif isinstance(pos, dict) and 'shortName' in pos:
                            eligible_positions.append(pos['shortName'])
                        elif isinstance(pos, dict) and 'name' in pos:
                            eligible_positions.append(pos['name'])
                
                # Stats processing - handle different formats
                stats = {}
                
                # Check stats in player object - direct approach first
                if 'stats' in player and player['stats']:
                    player_stats = player['stats']
                    
                    if isinstance(player_stats, dict):
                        # First check for hitting/pitching structure
                        if 'hitting' in player_stats and player_stats['hitting']:
                            hitting = player_stats['hitting']
                            if isinstance(hitting, dict):
                                for stat_name, stat_value in hitting.items():
                                    stats[f'hit_{stat_name}'] = stat_value
                        
                        if 'pitching' in player_stats and player_stats['pitching']:
                            pitching = player_stats['pitching']
                            if isinstance(pitching, dict):
                                for stat_name, stat_value in pitching.items():
                                    stats[f'pit_{stat_name}'] = stat_value
                                    
                        # Direct stat keys
                        for stat_name, stat_value in player_stats.items():
                            if (stat_name not in ['hitting', 'pitching'] and 
                                not stat_name.startswith('hit_') and 
                                not stat_name.startswith('pit_')):
                                # Determine if hitting or pitching stat
                                if stat_name in ['AVG', 'HR', 'RBI', 'R', 'SB', 'OBP', 'OPS',
                                               'H', '2B', '3B', 'BB', 'PA', 'AB']:
                                    stats[f'hit_{stat_name}'] = stat_value
                                elif stat_name in ['ERA', 'WHIP', 'W', 'SV', 'SO', 'QS', 
                                                 'IP', 'H', 'ER', 'HLD', 'BB']:
                                    stats[f'pit_{stat_name}'] = stat_value
                                else:
                                    stats[stat_name] = stat_value
                
                # Try to find stats directly in player object
                stat_keys = {
                    'hitting': ['AVG', 'HR', 'RBI', 'R', 'SB', 'OBP', 'OPS', 'H', '2B', '3B', 'BB', 'PA', 'AB'],
                    'pitching': ['ERA', 'WHIP', 'W', 'SV', 'SO', 'QS', 'IP', 'ER', 'HLD', 'BB']
                }
                
                # Check for hitting stats
                for stat in stat_keys['hitting']:
                    if stat in player and player[stat] is not None:
                        stats[f'hit_{stat}'] = player[stat]
                
                # Check for pitching stats
                for stat in stat_keys['pitching']:
                    if stat in player and player[stat] is not None:
                        stats[f'pit_{stat}'] = player[stat]
                
                # Create player record
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
            
            # Success message - only show if we have a reasonable number of players
            player_count = len(df)
            if player_count > 0:
                if player_count < 100:
                    st.success(f"Successfully loaded {player_count} players from Fantrax!")
                else:
                    st.success(f"Successfully loaded {player_count} players!")
            
            return df
            
        except Exception as e:
            st.error(f"Error processing available players: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return pd.DataFrame(
                columns=['player_id', 'player_name', 'position', 'mlb_team', 'status', 'eligible_positions', 'stats']
            )