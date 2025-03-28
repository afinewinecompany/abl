import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json

def get_current_scoring_period(scoring_periods: List[Dict[str, Any]]) -> int:
    """Get the current scoring period ID"""
    if not scoring_periods:
        return 1
        
    for period in scoring_periods:
        if period.get('is_current', False):
            week = period.get('week')
            if week is not None:
                return int(week)
                
    # If no current period found, return the first one
    if scoring_periods and 'week' in scoring_periods[0]:
        return int(scoring_periods[0]['week'])
    
    # Default to period 1
    return 1

def process_live_scoring_data(live_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the live scoring data to extract relevant information
    """
    if not live_data:
        return {
            'teams': [],
            'players': [],
            'matchups': []
        }
    
    # Extract teams data
    teams_data = []
    if 'teams' in live_data and isinstance(live_data['teams'], list):
        for team in live_data['teams']:
            if not isinstance(team, dict):
                continue
                
            team_id = team.get('id', '')
            team_name = team.get('name', 'Unknown Team')
            team_score = team.get('score', 0)
            
            teams_data.append({
                'team_id': team_id,
                'team_name': team_name,
                'team_score': team_score
            })
    
    # Extract players data with team association
    players_data = []
    if 'players' in live_data and isinstance(live_data['players'], list):
        for player in live_data['players']:
            if not isinstance(player, dict):
                continue
                
            player_id = player.get('id', '')
            player_name = player.get('name', 'Unknown Player')
            player_team_id = player.get('teamId', '')
            player_score = player.get('score', 0)
            player_position = player.get('position', '')
            player_mlb_team = player.get('mlbTeam', '')
            player_status = player.get('status', '')
            
            # Get player stats if available
            player_stats = {}
            if 'stats' in player and isinstance(player['stats'], dict):
                player_stats = player['stats']
            
            # Find team name for this player
            team_name = 'Unknown Team'
            for team in teams_data:
                if team['team_id'] == player_team_id:
                    team_name = team['team_name']
                    break
            
            players_data.append({
                'player_id': player_id,
                'player_name': player_name,
                'team_id': player_team_id,
                'team_name': team_name,
                'score': player_score,
                'position': player_position,
                'mlb_team': player_mlb_team,
                'status': player_status,
                'stats': player_stats
            })
    
    # Extract matchups data
    matchups_data = []
    if 'matchups' in live_data and isinstance(live_data['matchups'], list):
        for matchup in live_data['matchups']:
            if not isinstance(matchup, dict):
                continue
                
            matchup_id = matchup.get('id', '')
            away_team_id = matchup.get('awayTeamId', '')
            home_team_id = matchup.get('homeTeamId', '')
            
            # Find team names and scores
            away_team_name = 'Unknown Team'
            away_team_score = 0
            home_team_name = 'Unknown Team'
            home_team_score = 0
            
            for team in teams_data:
                if team['team_id'] == away_team_id:
                    away_team_name = team['team_name']
                    away_team_score = team['team_score']
                elif team['team_id'] == home_team_id:
                    home_team_name = team['team_name']
                    home_team_score = team['team_score']
            
            matchups_data.append({
                'matchup_id': matchup_id,
                'away_team_id': away_team_id,
                'away_team_name': away_team_name,
                'away_team_score': away_team_score,
                'home_team_id': home_team_id,
                'home_team_name': home_team_name,
                'home_team_score': home_team_score
            })
    
    return {
        'teams': teams_data,
        'players': players_data,
        'matchups': matchups_data
    }

def render_team_vs_team(matchup: Dict[str, Any], all_players: List[Dict[str, Any]]):
    """Render a team vs team matchup card"""
    # Get team names and scores
    away_team_name = matchup.get('away_team_name', 'Away Team')
    away_team_score = matchup.get('away_team_score', 0)
    home_team_name = matchup.get('home_team_name', 'Home Team')
    home_team_score = matchup.get('home_team_score', 0)
    
    # Get team IDs
    away_team_id = matchup.get('away_team_id', '')
    home_team_id = matchup.get('home_team_id', '')
    
    # Filter players for both teams
    away_team_players = [p for p in all_players if p.get('team_id') == away_team_id]
    home_team_players = [p for p in all_players if p.get('team_id') == home_team_id]
    
    # Sort players by score (descending)
    away_team_players = sorted(away_team_players, key=lambda x: x.get('score', 0), reverse=True)
    home_team_players = sorted(home_team_players, key=lambda x: x.get('score', 0), reverse=True)
    
    # Create columns for team comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(away_team_name)
        st.metric("Score", f"{away_team_score:.1f}")
        
        # Show top scoring players
        st.write("**Top Scorers:**")
        for i, player in enumerate(away_team_players[:5]):  # Show top 5 players
            player_name = player.get('player_name', 'Unknown')
            player_score = player.get('score', 0)
            st.write(f"{i+1}. {player_name}: {player_score:.1f} pts")
    
    with col2:
        st.subheader(home_team_name)
        st.metric("Score", f"{home_team_score:.1f}")
        
        # Show top scoring players
        st.write("**Top Scorers:**")
        for i, player in enumerate(home_team_players[:5]):  # Show top 5 players
            player_name = player.get('player_name', 'Unknown')
            player_score = player.get('score', 0)
            st.write(f"{i+1}. {player_name}: {player_score:.1f} pts")
    
    # Add a visual score comparison
    fig = go.Figure()
    
    # Add score bars
    fig.add_trace(go.Bar(
        x=[away_team_score],
        y=[away_team_name],
        orientation='h',
        name=away_team_name,
        marker=dict(color='#ff9e00'),
        text=f"{away_team_score:.1f}",
        textposition='outside',
        width=0.5
    ))
    
    fig.add_trace(go.Bar(
        x=[home_team_score],
        y=[home_team_name],
        orientation='h',
        name=home_team_name,
        marker=dict(color='#00b4ff'),
        text=f"{home_team_score:.1f}",
        textposition='outside',
        width=0.5
    ))
    
    # Customize layout
    fig.update_layout(
        title="Matchup Score Comparison",
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Points",
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a divider
    st.markdown("---")

def render_player_table(players: List[Dict[str, Any]], team_filter: str = None):
    """Render a table of players with their scores"""
    if not players:
        st.info("No player data available.")
        return
    
    # Filter by team if specified
    if team_filter:
        players = [p for p in players if p.get('team_name') == team_filter]
    
    # Create DataFrame for display
    df = pd.DataFrame(players)
    
    # Select and rename columns
    if 'player_name' in df.columns and 'score' in df.columns:
        display_df = df[['player_name', 'position', 'mlb_team', 'score', 'team_name']]
        display_df = display_df.rename(columns={
            'player_name': 'Player',
            'position': 'Pos',
            'mlb_team': 'MLB Team',
            'score': 'Points',
            'team_name': 'Fantasy Team'
        })
        
        # Sort by points (high to low)
        display_df = display_df.sort_values('Points', ascending=False)
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("Player data is missing required fields.")

def create_leaderboard_chart(players: List[Dict[str, Any]], limit: int = 20):
    """Create a leaderboard chart of top scoring players"""
    if not players:
        st.info("No player data available for leaderboard.")
        return
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(players)
    if 'score' not in df.columns or 'player_name' not in df.columns:
        st.warning("Player data is missing required fields for leaderboard.")
        return
    
    # Sort and get top players
    df = df.sort_values('score', ascending=False).head(limit)
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['player_name'],
        x=df['score'],
        orientation='h',
        marker=dict(
            color=df['score'],
            colorscale='Viridis'
        ),
        text=df['score'].apply(lambda x: f"{x:.1f}"),
        textposition='outside'
    ))
    
    # Customize layout
    fig.update_layout(
        title=f"Top {limit} Players by Points",
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Points",
        yaxis=dict(
            title="Player",
            autorange="reversed"  # Highest value at the top
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render(data: Dict[str, Any]):
    """Render matchups section with live scoring data"""
    
    # Extract data
    live_scoring_data = data.get('live_scoring', {})
    scoring_periods = data.get('scoring_periods', [])
    current_matchups = data.get('current_matchups', [])
    
    st.title("Live Matchups")
    
    # Get current scoring period
    current_period = get_current_scoring_period(scoring_periods)
    
    # Process live scoring data
    processed_data = process_live_scoring_data(live_scoring_data)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Matchups", "Player Leaderboard", "All Players"])
    
    with tab1:
        st.header(f"Week {current_period} Matchups")
        
        # Check if we have matchup data
        if processed_data['matchups']:
            # Display each matchup
            for matchup in processed_data['matchups']:
                render_team_vs_team(matchup, processed_data['players'])
        else:
            # Fallback to less detailed matchup data if live scoring doesn't have matchups
            st.info("Detailed live scoring data not available. Showing basic matchup information.")
            
            if current_matchups:
                for matchup in current_matchups:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(matchup.get('away_team', 'Away Team'))
                        st.metric("Score", f"{matchup.get('away_score', 0):.1f}")
                    with col2:
                        st.subheader(matchup.get('home_team', 'Home Team'))
                        st.metric("Score", f"{matchup.get('home_score', 0):.1f}")
                    st.markdown("---")
            else:
                st.warning("No matchup data available for the current scoring period.")
    
    with tab2:
        st.header("Player Leaderboard")
        create_leaderboard_chart(processed_data['players'])
    
    with tab3:
        st.header("All Players")
        
        # Add team filter
        team_options = ['All Teams'] + [team['team_name'] for team in processed_data['teams']]
        selected_team = st.selectbox("Filter by Team", team_options)
        
        # Display player table
        if selected_team == 'All Teams':
            render_player_table(processed_data['players'])
        else:
            render_player_table(processed_data['players'], selected_team)