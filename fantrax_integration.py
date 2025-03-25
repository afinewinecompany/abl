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
            standings = _self._api.standings()
            standings_data = []
            
            for rank, record in standings.ranks.items():
                standings_data.append({
                    'rank': rank,
                    'team': record.team.name,
                    'team_id': record.team.team_id,
                    'wins': record.win,
                    'losses': record.loss,
                    'ties': record.tie,
                    'win_percentage': record.win_percentage,
                    'points_for': record.points_for,
                    'points_against': record.points_against if hasattr(record, 'points_against') else None,
                    'games_back': record.games_back if hasattr(record, 'games_back') else None,
                    'streak': record.streak
                })
            
            return pd.DataFrame(standings_data)
        except Exception as e:
            st.error(f"Failed to fetch standings: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_team_rosters(_self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all team rosters as a dictionary."""
        try:
            rosters = {}
            teams = _self._api.teams

            for team_id, team in teams.items():
                team_roster = _self._api.roster(team_id)
                roster_data = []
                
                # Process active players
                for scorer_id in team_roster.active:
                    player = team_roster.active[scorer_id]
                    roster_data.append({
                        'player_id': player.id,
                        'player_name': player.name,
                        'position': player.pos_short_name,
                        'team': player.team_name,
                        'team_short': player.team_short_name,
                        'status': 'Active',
                        'injured': player.injured,
                        'suspended': player.suspended
                    })
                
                # Process injured players
                for scorer_id in team_roster.injured:
                    player = team_roster.injured[scorer_id]
                    roster_data.append({
                        'player_id': player.id,
                        'player_name': player.name,
                        'position': player.pos_short_name,
                        'team': player.team_name,
                        'team_short': player.team_short_name,
                        'status': 'Injured',
                        'injured': True,
                        'suspended': player.suspended
                    })
                
                rosters[team.name] = roster_data
            
            return rosters
        except Exception as e:
            st.error(f"Failed to fetch team rosters: {str(e)}")
            return {}

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_league_info(_self) -> Dict[str, Any]:
        """Get league information."""
        try:
            league_info = {
                'name': _self._api.name,
                'sport': _self._api.sport,
                'season': _self._api.season,
                'scoring_type': _self._api.scoring_type,
                'teams_count': len(_self._api.teams),
                'current_week': _self._api.current_period.week if hasattr(_self._api.current_period, 'week') else None,
            }
            return league_info
        except Exception as e:
            st.error(f"Failed to fetch league info: {str(e)}")
            return {}

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_transactions(_self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions."""
        try:
            transactions = _self._api.transactions(limit)
            transactions_data = []
            
            for tx in transactions:
                for player in tx.players:
                    transactions_data.append({
                        'date': tx.date.strftime("%Y-%m-%d %H:%M"),
                        'team': tx.team.name,
                        'player_name': player.name,
                        'player_team': player.team_name,
                        'player_position': player.pos_short_name,
                        'transaction_type': player.type if hasattr(player, 'type') else 'Unknown'
                    })
            
            return transactions_data
        except Exception as e:
            st.error(f"Failed to fetch transactions: {str(e)}")
            return []

    @st.cache_data(ttl=3600)  # Cache data for 1 hour
    def get_scoring_periods(_self) -> List[Dict[str, Any]]:
        """Get scoring periods information."""
        try:
            periods = _self._api.scoring_periods
            periods_data = []
            
            for period in periods:
                periods_data.append({
                    'name': period.name,
                    'week': period.week if hasattr(period, 'week') else None,
                    'start_date': period.start.strftime("%Y-%m-%d"),
                    'end_date': period.end.strftime("%Y-%m-%d"),
                    'is_current': period.current,
                    'is_complete': period.complete,
                    'is_future': period.future
                })
            
            return periods_data
        except Exception as e:
            st.error(f"Failed to fetch scoring periods: {str(e)}")
            return []

    def get_matchups_for_period(_self, period_index: int = 0) -> List[Dict[str, Any]]:
        """Get matchups for a specific scoring period."""
        try:
            periods = _self._api.scoring_periods
            if 0 <= period_index < len(periods):
                period = periods[period_index]
                matchups_data = []
                
                for matchup in period.matchups:
                    winner, winner_score, loser, loser_score = matchup.winner()
                    matchups_data.append({
                        'away_team': matchup.away if isinstance(matchup.away, str) else matchup.away.name,
                        'away_score': matchup.away_score,
                        'home_team': matchup.home if isinstance(matchup.home, str) else matchup.home.name,
                        'home_score': matchup.home_score,
                        'winner': winner.name if winner else "Tie",
                        'winner_score': winner_score if winner_score else matchup.away_score,
                        'loser': loser.name if loser else "Tie",
                        'loser_score': loser_score if loser_score else matchup.home_score,
                        'score_difference': matchup.difference()
                    })
                
                return matchups_data
            return []
        except Exception as e:
            st.error(f"Failed to fetch matchups: {str(e)}")
            return []

# Initialize the API client 
fantrax_client = FantraxAPIWrapper("grx2lginm1v4p5jd")