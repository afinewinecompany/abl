import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union, cast
from api_client import FantraxAPI

class FantraxAPIWrapper:
    """
    Wrapper for the Fantrax API to handle league data retrieval and processing.
    """
    def __init__(self, league_id: str = "grx2lginm1v4p5jd"):
        """Initialize the Fantrax API with the league ID."""
        self.league_id = league_id
        self._api = FantraxAPI()  # The league_id is already set in the FantraxAPI class
        self._cache = {}
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_standings(_self) -> pd.DataFrame:
        """Get current standings and convert to DataFrame."""
        try:
            # Get standings data from API
            standings_data = _self._api.get_standings()  # This gets a list of standings data
            
            if not standings_data or not isinstance(standings_data, list):
                return pd.DataFrame()
                
            # Process the standings data into a DataFrame
            processed_standings = []
            
            for i, team in enumerate(standings_data):
                # Handle string values that should be numbers
                try:
                    wins = int(team.get('wins', 0))
                except (ValueError, TypeError):
                    wins = 0
                    
                try:
                    losses = int(team.get('losses', 0))
                except (ValueError, TypeError):
                    losses = 0
                    
                try:
                    ties = int(team.get('ties', 0))
                except (ValueError, TypeError):
                    ties = 0
                    
                try:
                    points_for = float(team.get('pointsFor', 0.0)) if team.get('pointsFor') not in ['-', '', None] else 0.0
                except (ValueError, TypeError):
                    points_for = 0.0
                    
                try:
                    points_against = float(team.get('pointsAgainst', 0.0)) if team.get('pointsAgainst') not in ['-', '', None] else 0.0
                except (ValueError, TypeError):
                    points_against = 0.0
                
                # Calculate win percentage
                total_games = wins + losses + ties
                win_percentage = wins / total_games if total_games > 0 else 0.0
                
                processed_standings.append({
                    'rank': i + 1,
                    'team': team.get('teamName', f'Team {i+1}'),
                    'team_id': team.get('teamId', ''),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'win_percentage': win_percentage,
                    'points_for': points_for,
                    'points_against': points_against,
                    'games_back': 0.0,  # Placeholder
                    'streak': team.get('streakDescription', '')
                })
            
            # Sort by rank
            standings_df = pd.DataFrame(processed_standings).sort_values('rank')
            
            # Calculate games back
            if not standings_df.empty:
                max_wins = standings_df['wins'].max()
                min_losses = standings_df['losses'].min()
                
                # Formula: (max_wins - wins) + (losses - min_losses) / 2
                standings_df['games_back'] = ((max_wins - standings_df['wins']) + 
                                            (standings_df['losses'] - min_losses)) / 2
                
                # First place has 0 games back
                standings_df.loc[standings_df['rank'] == 1, 'games_back'] = 0.0
            
            return standings_df
            
        except Exception as e:
            st.error(f"Failed to fetch standings: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_team_rosters(_self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all team rosters as a dictionary."""
        try:
            rosters = {}
            # Use the team info from get_team_rosters since there's no direct get_teams endpoint
            rosters_data = _self._api.get_team_rosters()
            teams_data = []
            
            # Extract team information from rosters response
            if isinstance(rosters_data, dict) and 'rosters' in rosters_data:
                for team_id, team_info in rosters_data.get('rosters', {}).items():
                    if isinstance(team_info, dict):
                        teams_data.append({
                            'id': team_id,
                            'name': team_info.get('teamName', f'Team {team_id}')
                        })
            else:
                # Fallback for missing data
                teams_data
            
            if not teams_data or not isinstance(teams_data, list):
                return {}
            
            # Process each team's roster
            for team in teams_data:
                team_id = team.get('id', '')
                team_name = team.get('name', 'Unknown Team')
                
                if not team_id:
                    continue
                
                # Get roster for this team from the roster response
                # Since there's no direct get_roster method, extract from the data we already have
                team_roster = []
                if isinstance(rosters_data, dict) and 'rosters' in rosters_data:
                    team_roster_data = rosters_data.get('rosters', {}).get(team_id, {})
                    if isinstance(team_roster_data, dict) and 'rosterItems' in team_roster_data:
                        team_roster = team_roster_data.get('rosterItems', [])
                
                if not team_roster or not isinstance(team_roster, list):
                    rosters[team_name] = []
                    continue
                
                # Process players on this roster
                roster_data = []
                for player in team_roster:
                    # Check if this is a player object
                    if not isinstance(player, dict):
                        continue
                    
                    # Extract player details
                    player_status = player.get('status', 'Unknown')
                    
                    roster_data.append({
                        'player_id': player.get('id', ''),
                        'player_name': player.get('name', 'Unknown Player'),
                        'position': player.get('position', ''),
                        'team': player.get('proTeam', ''),
                        'team_short': player.get('proTeamAbbreviation', ''),
                        'status': player_status,
                        'injured': player.get('injuryStatus', '') != '',
                        'suspended': player.get('suspended', False)
                    })
                
                # Store the processed roster
                rosters[team_name] = roster_data
            
            return rosters
        except Exception as e:
            st.error(f"Failed to fetch team rosters: {str(e)}")
            return {}

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_league_info(_self) -> Dict[str, Any]:
        """Get league information."""
        try:
            # Get league info from API
            league_obj = _self._api.get_league_info()
            
            # Extract league details safely from the API response
            league_info = {
                'name': league_obj.get('name', 'ABL League'),
                'sport': 'Baseball',  # This is MLB by default
                'season': str(league_obj.get('season', '2025')),
                'scoring_type': league_obj.get('scoringSettings', {}).get('scoringPeriod', 'Weekly'),
                'teams_count': league_obj.get('teams', 30),
                'current_week': 1,  # Default to week 1
            }
                
            return league_info
        except Exception as e:
            st.error(f"Failed to fetch league info: {str(e)}")
            return {}

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_transactions(_self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent transactions using the Transaction object structure.
        
        Transaction object fields:
        - id (str): Transaction ID
        - team (Team): Team who made the transaction
        - date (datetime): Transaction date
        - count (str): Number of players in the transaction
        - players (List[Player]): Players in the transaction
        - finalized (bool): Whether all players have been added
        """
        try:
            # Get transactions data from API
            transactions = _self._api.get_transactions(limit)
            
            if not transactions or not isinstance(transactions, list):
                # Return an empty list with a debug message
                st.sidebar.warning("No transactions returned from API.")
                return []
            
            st.sidebar.success(f"Successfully fetched {len(transactions)} transactions from API.")
                
            transactions_data = []
            
            # Format transaction data using the Transaction object structure
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                
                # Process transaction ID
                transaction_id = tx.get('id', '') or tx.get('transactionId', '')
                
                # Generate a random ID if none exists to ensure we have an ID for every transaction
                if not transaction_id:
                    import random
                    transaction_id = f"tx-{random.randint(1000, 9999)}"
                
                # Process transaction date
                date_str = tx.get('dateTime', '') or tx.get('date', '')
                try:
                    # Handle various date formats
                    from datetime import datetime
                    
                    if date_str:
                        # Try different formats
                        for fmt in ["%a %b %d, %Y, %I:%M%p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                            try:
                                date_obj = datetime.strptime(date_str, fmt)
                                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format worked, use the original string
                            formatted_date = date_str
                    else:
                        formatted_date = "Unknown Date"
                except Exception:
                    formatted_date = "Unknown Date"
                
                # Get team information
                team_info = tx.get('team', {})
                team_name = ''
                
                if isinstance(team_info, dict):
                    team_name = team_info.get('name', '')
                
                if not team_name:
                    team_name = tx.get('teamName', 'Unknown Team')
                
                # Get transaction type
                transaction_type = tx.get('type', 'Unknown')
                
                # Get player count - can be string or int
                player_count = tx.get('count', '0')
                
                # Get players list
                players_list = tx.get('players', [])
                
                # If players is not a list but we have player info in the transaction
                if not players_list and 'playerName' in tx:
                    player_name = tx.get('playerName', 'Unknown Player')
                    player_team = tx.get('playerTeam', 'Unknown Team')
                    player_position = tx.get('playerPosition', 'Unknown')
                    
                    # Create a player object
                    player = {
                        'name': player_name,
                        'team': player_team,
                        'position': player_position
                    }
                    
                    players_list = [player]
                
                # Get finalized status
                finalized = tx.get('finalized', True)  # Default to True if not specified
                
                # Create player_name for single-player convenience
                player_name = None
                if players_list and len(players_list) > 0:
                    if isinstance(players_list[0], dict) and 'name' in players_list[0]:
                        player_name = players_list[0]['name']
                
                # Use playerName directly if available and player_name is still None
                if not player_name and 'playerName' in tx:
                    player_name = tx.get('playerName')
                
                tx_data = {
                    'id': transaction_id,
                    'date': formatted_date,
                    'team': team_name,
                    'count': player_count,
                    'players': players_list,
                    'transaction_type': transaction_type,
                    'finalized': finalized
                }
                
                # Only add player_name if we have it
                if player_name:
                    tx_data['player_name'] = player_name
                
                transactions_data.append(tx_data)
            
            st.sidebar.success(f"Processed {len(transactions_data)} transactions.")
            return transactions_data
        except Exception as e:
            st.error(f"Failed to fetch transactions: {str(e)}")
            return []

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_scoring_periods(_self) -> List[Dict[str, Any]]:
        """Get scoring periods information."""
        try:
            # Get scoring periods from API
            periods = _self._api.get_scoring_periods()
            
            if not periods or not isinstance(periods, list):
                return []
                
            periods_data = []
            from datetime import datetime
            
            # Format the scoring periods
            for period in periods:
                if not isinstance(period, dict):
                    continue
                
                # Parse dates if available
                start_date_str = period.get('startDate', '')
                end_date_str = period.get('endDate', '')
                
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d") if start_date_str else "Unknown"
                except ValueError:
                    start_date = start_date_str or "Unknown"
                    
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%Y-%m-%d") if end_date_str else "Unknown"
                except ValueError:
                    end_date = end_date_str or "Unknown"
                
                periods_data.append({
                    'name': period.get('periodName', f"Period {period.get('periodNum', 'Unknown')}"),
                    'week': period.get('periodNum', None),
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_current': period.get('isCurrent', False),
                    'is_complete': period.get('isComplete', False),
                    'is_future': period.get('isFuture', False)
                })
            
            # Sort by week number if available
            periods_data.sort(key=lambda x: (0 if x['week'] is None else int(x['week'])))
            
            return periods_data
        except Exception as e:
            st.error(f"Failed to fetch scoring periods: {str(e)}")
            return []

    @st.cache_data(ttl=600)  # Cache data for 10 minutes (shorter for live data)
    def get_live_scoring(_self, period_id: int = 1, auth_token: str = None) -> Dict[str, Any]:
        """Get live scoring data for a specific period."""
        try:
            # Get live scoring data from API
            live_scoring_data = _self._api.get_live_scoring(period_id, auth_token)
            
            if not live_scoring_data or not isinstance(live_scoring_data, dict):
                st.warning("No live scoring data available from the API.")
                return {}
            
            return live_scoring_data
            
        except Exception as e:
            st.error(f"Failed to fetch live scoring data: {str(e)}")
            return {}
    
    def get_matchups_for_period(_self, period_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matchups for a specific scoring period."""
        try:
            # If no period_id specified, find the current period
            if period_id is None:
                try:
                    periods = _self.get_scoring_periods()
                    for period in periods:
                        if period.get('is_current', False):
                            week = period.get('week')
                            if week is not None:
                                period_id = int(week)
                                break
                    
                    # If still no period found, use the first one
                    if period_id is None and periods:
                        week = periods[0].get('week')
                        if week is not None:
                            period_id = int(week)
                except:
                    period_id = 1  # Fallback to period 1
                
            # Ensure we have a valid period ID
            if period_id is None:
                period_id = 1
            
            # Get matchups from API
            matchups = _self._api.get_matchups(period_id)
            
            if not matchups or not isinstance(matchups, list):
                return []
                
            matchups_data = []
            
            # Process each matchup
            for matchup in matchups:
                if not isinstance(matchup, dict):
                    continue
                
                # Extract team information
                away_team = matchup.get('awayTeam', {}).get('name', 'Unknown Team')
                home_team = matchup.get('homeTeam', {}).get('name', 'Unknown Team')
                
                # Handle scores with error protection
                try:
                    away_score = float(matchup.get('awayScore', 0))
                except (ValueError, TypeError):
                    away_score = 0
                    
                try:
                    home_score = float(matchup.get('homeScore', 0))
                except (ValueError, TypeError):
                    home_score = 0
                    
                # Determine winner/loser
                if away_score > home_score:
                    winner = away_team
                    winner_score = away_score
                    loser = home_team
                    loser_score = home_score
                elif home_score > away_score:
                    winner = home_team
                    winner_score = home_score
                    loser = away_team
                    loser_score = away_score
                else:
                    winner = "Tie"
                    winner_score = away_score
                    loser = "Tie"
                    loser_score = home_score
                
                # Calculate score difference
                score_difference = abs(away_score - home_score)
                
                matchups_data.append({
                    'away_team': away_team,
                    'away_score': away_score,
                    'home_team': home_team,
                    'home_score': home_score,
                    'winner': winner,
                    'winner_score': winner_score,
                    'loser': loser,
                    'loser_score': loser_score,
                    'score_difference': score_difference,
                    'matchup_id': matchup.get('id', ''),
                    'period_id': period_id
                })
            
            return matchups_data
        except Exception as e:
            st.error(f"Failed to fetch matchups: {str(e)}")
            return []

# Initialize the API client 
fantrax_client = FantraxAPIWrapper("grx2lginm1v4p5jd")