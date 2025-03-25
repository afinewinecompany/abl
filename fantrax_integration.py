from fantraxapi import FantraxAPI
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

class FantraxAPIWrapper:
    """
    Wrapper for the Fantrax API to handle league data retrieval and processing.
    """
    def __init__(self, league_id: str = "grx2lginm1v4p5jd"):
        """Initialize the Fantrax API with the league ID."""
        self.league_id = league_id
        self._api = FantraxAPI(league_id)
        self._cache = {}
    
    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_standings(_self) -> pd.DataFrame:
        """Get current standings and convert to DataFrame."""
        try:
            # Get standings data from API
            standings_data = _self._api.get_standings()
            
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
            teams_data = _self._api.get_teams()
            
            if not teams_data or not isinstance(teams_data, list):
                return {}
            
            # Process each team's roster
            for team in teams_data:
                team_id = team.get('id', '')
                team_name = team.get('name', 'Unknown Team')
                
                if not team_id:
                    continue
                
                # Get roster for this team
                team_roster = _self._api.get_roster(team_id)
                
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
            
            # Extract league details safely
            league_info = {
                'name': league_obj.get('leagueName', 'ABL League'),
                'sport': league_obj.get('sportType', 'Baseball'),
                'season': league_obj.get('season', '2025'),
                'scoring_type': league_obj.get('scoringStyle', 'H2H'),
                'teams_count': len(_self._api.get_teams() or []),
                'current_week': None,  # Will be set from scoring periods later
            }
            
            # Try to get current period/week
            try:
                scoring_periods = _self._api.get_scoring_periods()
                if isinstance(scoring_periods, list):
                    for period in scoring_periods:
                        if period.get('isCurrent', False):
                            league_info['current_week'] = period.get('periodNum', 'N/A')
                            break
            except:
                pass
                
            return league_info
        except Exception as e:
            st.error(f"Failed to fetch league info: {str(e)}")
            return {}

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_transactions(_self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions."""
        try:
            # Get transactions data from API
            transactions = _self._api.get_transactions(limit)
            
            if not transactions or not isinstance(transactions, list):
                return []
                
            transactions_data = []
            
            # Format transaction data
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                    
                # Try to parse the date string
                date_str = tx.get('dateTime', '')
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
                team_name = tx.get('teamName', 'Unknown Team')
                
                # Process player information
                player_name = tx.get('playerName', 'Unknown Player')
                player_team = tx.get('playerTeam', 'Unknown Team')
                player_position = tx.get('playerPosition', 'Unknown')
                transaction_type = tx.get('type', 'Unknown')
                
                transactions_data.append({
                    'date': formatted_date,
                    'team': team_name,
                    'player_name': player_name,
                    'player_team': player_team,
                    'player_position': player_position,
                    'transaction_type': transaction_type
                })
            
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

    def get_matchups_for_period(_self, period_id: int = None) -> List[Dict[str, Any]]:
        """Get matchups for a specific scoring period."""
        try:
            # If no period_id specified, find the current period
            if period_id is None:
                try:
                    periods = _self.get_scoring_periods()
                    for period in periods:
                        if period.get('is_current', False):
                            period_id = period.get('week')
                            break
                    
                    # If still no period found, use the first one
                    if period_id is None and periods:
                        period_id = periods[0].get('week')
                except:
                    period_id = 1  # Fallback to period 1
            
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