import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import datetime

def format_score(score: float) -> str:
    """Format score with one decimal place"""
    return f"{score:.1f}"

def create_matchup_card(matchup: Dict[str, Any]) -> None:
    """Create a styled card for a single matchup"""
    
    # Extract matchup data - handle both API field formats
    away_team = matchup.get('away_team', matchup.get('awayTeam', {}).get('name', 'Away Team'))
    home_team = matchup.get('home_team', matchup.get('homeTeam', {}).get('name', 'Home Team'))
    away_score = matchup.get('away_score', matchup.get('awayScore', 0.0))
    home_score = matchup.get('home_score', matchup.get('homeScore', 0.0))
    winner = matchup.get('winner', '')
    is_complete = matchup.get('is_complete', False)
    
    # Determine who's winning
    away_winning = away_score > home_score
    home_winning = home_score > away_score
    
    # Card container with border and shadow
    with st.container():
        st.markdown("""
        <style>
        .matchup-card {{
            background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.9) 100%);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            border: 1px solid rgba(30, 100, 255, 0.1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }}
        .team-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .team-row:last-child {{
            border-bottom: none;
        }}
        .team-name {{
            font-size: 18px;
            font-weight: 600;
            flex-grow: 1;
        }}
        .team-score {{
            font-size: 22px;
            font-weight: 700;
            min-width: 60px;
            text-align: right;
        }}
        .winning {{
            color: #3080ff;
        }}
        .losing {{
            color: #ff3030;
        }}
        .tied {{
            color: #ffcc00;
        }}
        .matchup-status {{
            text-align: center;
            font-size: 14px;
            color: #999;
            margin-top: 12px;
            font-style: italic;
        }}
        </style>
        
        <div class="matchup-card">
            <div class="team-row">
                <div class="team-name">{away_team}</div>
                <div class="team-score {winning_class_away}">{away_score:.1f}</div>
            </div>
            <div class="team-row">
                <div class="team-name">{home_team}</div>
                <div class="team-score {winning_class_home}">{home_score:.1f}</div>
            </div>
            <div class="matchup-status">
                {status_text}
            </div>
        </div>
        """.format(
            away_team=away_team,
            home_team=home_team,
            away_score=away_score,
            home_score=home_score,
            winning_class_away="winning" if away_winning else "losing" if home_winning else "tied",
            winning_class_home="winning" if home_winning else "losing" if away_winning else "tied",
            status_text="Final" if is_complete else "In Progress"
        ), unsafe_allow_html=True)

def create_standings_grid(matchups: List[Dict[str, Any]]) -> None:
    """Create a standings grid showing wins/losses between teams"""
    
    # Extract all unique team names, handling both field name formats
    all_teams = set()
    for matchup in matchups:
        away_team = matchup.get('away_team', matchup.get('awayTeam', {}).get('name', ''))
        home_team = matchup.get('home_team', matchup.get('homeTeam', {}).get('name', ''))
        all_teams.add(away_team)
        all_teams.add(home_team)
    
    all_teams = sorted(list(filter(None, all_teams)))  # Remove empty strings
    
    # Create a matrix of matchup results
    matrix = {}
    for team in all_teams:
        matrix[team] = {other_team: "-" for other_team in all_teams}
        matrix[team][team] = "X"  # Diagonal (team vs itself)
    
    # Fill in the matrix with matchup results
    for matchup in matchups:
        away_team = matchup.get('away_team', matchup.get('awayTeam', {}).get('name', ''))
        home_team = matchup.get('home_team', matchup.get('homeTeam', {}).get('name', ''))
        away_score = matchup.get('away_score', matchup.get('awayScore', 0.0))
        home_score = matchup.get('home_score', matchup.get('homeScore', 0.0))
        
        # Skip if teams not found
        if away_team not in all_teams or home_team not in all_teams:
            continue
            
        if away_score > home_score:
            matrix[away_team][home_team] = "W"
            matrix[home_team][away_team] = "L"
        elif home_score > away_score:
            matrix[away_team][home_team] = "L"
            matrix[home_team][away_team] = "W"
        else:
            matrix[away_team][home_team] = "T"
            matrix[home_team][away_team] = "T"
    
    # Convert matrix to a DataFrame for display
    df = pd.DataFrame(matrix)
    
    # Visualize the grid with Plotly
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[""] + all_teams,
            fill_color='#1a1c23',
            font=dict(color='white', size=12),
            align='center'
        ),
        cells=dict(
            values=[all_teams] + [df[team].tolist() for team in all_teams],
            fill_color=[['#1a1c23']] + [['rgba(26, 28, 35, 0.8)'] * len(all_teams)] * len(all_teams),
            font=dict(
                color=[['white']] + [[
                    '#3080ff' if val == 'W' else
                    '#ff3030' if val == 'L' else
                    '#ffcc00' if val == 'T' else
                    '#555555'
                    for val in df[team].tolist()
                ] for team in all_teams],
                size=14
            ),
            align='center'
        )
    )])
    
    # Update layout
    fig.update_layout(
        title="",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_score_distribution_chart(matchups: List[Dict[str, Any]]) -> None:
    """Create a histogram showing score distribution"""
    
    all_scores = []
    for matchup in matchups:
        away_score = matchup.get('away_score', matchup.get('awayScore', 0.0))
        home_score = matchup.get('home_score', matchup.get('homeScore', 0.0))
        all_scores.append(away_score)
        all_scores.append(home_score)
    
    # Create the histogram
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=all_scores,
        nbinsx=15,
        marker_color='#3080ff',
        opacity=0.7,
        hovertemplate="Score: %{x}<br>Count: %{y}<extra></extra>"
    ))
    
    # Calculate mean score
    mean_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Add a vertical line for the mean
    fig.add_vline(
        x=mean_score,
        line_width=2,
        line_dash="dash",
        line_color="#ff3030",
        annotation_text=f"Avg: {mean_score:.1f}",
        annotation_position="top right"
    )
    
    # Update layout
    fig.update_layout(
        title="Score Distribution",
        xaxis_title="Score",
        yaxis_title="Frequency",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_margin_of_victory_chart(matchups: List[Dict[str, Any]]) -> None:
    """Create a bar chart showing margins of victory"""
    
    margins = []
    matchup_labels = []
    colors = []
    
    for matchup in matchups:
        away_team = matchup.get('away_team', matchup.get('awayTeam', {}).get('name', ''))
        home_team = matchup.get('home_team', matchup.get('homeTeam', {}).get('name', ''))
        away_score = matchup.get('away_score', matchup.get('awayScore', 0.0))
        home_score = matchup.get('home_score', matchup.get('homeScore', 0.0))
        
        margin = away_score - home_score
        winner = away_team if margin > 0 else home_team if margin < 0 else "Tie"
        loser = home_team if margin > 0 else away_team if margin < 0 else "Tie"
        
        margins.append(abs(margin))
        matchup_labels.append(f"{winner} vs {loser}")
        colors.append('#3080ff' if margin != 0 else '#ffcc00')
    
    # Sort by margin (highest to lowest)
    sorted_data = sorted(zip(matchup_labels, margins, colors), key=lambda x: x[1], reverse=True)
    matchup_labels, margins, colors = zip(*sorted_data) if sorted_data else ([], [], [])
    
    # Create the bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=matchup_labels,
        y=margins,
        marker_color=colors,
        text=[f"{m:.1f}" for m in margins],
        textposition='auto',
        hovertemplate="Matchup: %{x}<br>Margin: %{y:.1f}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="Margin of Victory",
        xaxis_title="Matchup",
        yaxis_title="Score Difference",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=10, r=10, t=50, b=100)
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)

def render(matchups_data: List[Dict[str, Any]]):
    """
    Render the matchups page with various visualizations
    
    Args:
        matchups_data: List of matchup dictionaries
    """
    # Page title and description
    st.header("🏆 Weekly Matchups")
    st.markdown("""
    View current and past matchups, including scores and visualizations.
    """)
    
    # Debug info about the matchup data
    st.write(f"Number of matchups: {len(matchups_data)}")
    if matchups_data and len(matchups_data) > 0:
        # Show example of a matchup entry for debugging
        with st.expander("Debug: Sample Matchup Data"):
            st.write(matchups_data[0])
    
    # Show error if no data
    if not matchups_data:
        st.error("No matchup data available.")
        return
        
    # Clean up matchup data if received in camelCase format from API
    # Convert all matchups to unified format with consistent keys
    processed_matchups = []
    for matchup in matchups_data:
        processed_matchup = {
            'away_team': matchup.get('away_team', matchup.get('awayTeam', {}).get('name', 'Unknown')),
            'home_team': matchup.get('home_team', matchup.get('homeTeam', {}).get('name', 'Unknown')),
            'away_score': matchup.get('away_score', matchup.get('awayScore', 0.0)),
            'home_score': matchup.get('home_score', matchup.get('homeScore', 0.0)),
            'week': matchup.get('week', matchup.get('periodId', 'current')),
            'is_complete': matchup.get('is_complete', False)
        }
        # Add winner and score difference keys
        if processed_matchup['away_score'] > processed_matchup['home_score']:
            processed_matchup['winner'] = processed_matchup['away_team']
            processed_matchup['score_difference'] = processed_matchup['away_score'] - processed_matchup['home_score']
        elif processed_matchup['home_score'] > processed_matchup['away_score']:
            processed_matchup['winner'] = processed_matchup['home_team']
            processed_matchup['score_difference'] = processed_matchup['home_score'] - processed_matchup['away_score']
        else:
            processed_matchup['winner'] = 'Tie'
            processed_matchup['score_difference'] = 0.0
            
        processed_matchups.append(processed_matchup)
    
    # Replace original data with processed data
    matchups_data = processed_matchups
    
    # Week selector - only use if there are multiple weeks
    available_weeks = sorted(list(set(
        [m.get('week', 'current') for m in matchups_data if 'week' in m]
    )))
    
    if available_weeks and len(available_weeks) > 1:
        if all(isinstance(w, int) or (isinstance(w, str) and w.isdigit()) for w in available_weeks):
            available_weeks = sorted([int(w) for w in available_weeks])
        
        selected_week = st.selectbox(
            "Select Week",
            available_weeks,
            index=0
        )
        
        # Filter matchups for selected week
        if selected_week:
            matchups_data = [m for m in matchups_data if str(m.get('week', '')) == str(selected_week)]
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs([
        "Current Matchups",
        "Statistics",
        "Standings Grid"
    ])
    
    with tab1:
        st.subheader("Current Week Matchups")
        
        # Arrange matchups in a grid
        cols = st.columns(2)
        for i, matchup in enumerate(matchups_data):
            with cols[i % 2]:
                create_matchup_card(matchup)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Score Distribution")
            create_score_distribution_chart(matchups_data)
        
        with col2:
            st.subheader("Margins of Victory")
            create_margin_of_victory_chart(matchups_data)
        
        # Show detailed matchup table
        st.subheader("Matchup Details")
        
        # Convert to DataFrame for display
        matchups_df = pd.DataFrame(matchups_data)
        
        # Convert any date columns if needed
        
        # Select columns to display
        if not matchups_df.empty and 'away_team' in matchups_df.columns:
            display_cols = [
                'away_team', 'away_score', 
                'home_team', 'home_score',
                'winner', 'score_difference'
            ]
            
            display_cols = [col for col in display_cols if col in matchups_df.columns]
            
            # Format the table
            st.dataframe(
                matchups_df[display_cols],
                column_config={
                    "away_team": "Away Team",
                    "away_score": st.column_config.NumberColumn("Away Score", format="%.1f"),
                    "home_team": "Home Team",
                    "home_score": st.column_config.NumberColumn("Home Score", format="%.1f"),
                    "winner": "Winner",
                    "score_difference": st.column_config.NumberColumn("Margin", format="%.1f")
                },
                hide_index=True
            )
    
    with tab3:
        st.subheader("Team vs. Team Results")
        st.markdown("""
        This grid shows the head-to-head results between teams.
        - **W**: Win
        - **L**: Loss
        - **T**: Tie
        - **X**: Team vs. itself
        - **-**: No matchup played
        """)
        
        create_standings_grid(matchups_data)