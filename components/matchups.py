import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from typing import List, Dict, Any
from api_client import FantraxAPI

def format_score(score: float) -> str:
    """Format the score with 1 decimal place."""
    return f"{score:.1f}"

def calculate_winning_probability(team1_score: float, team2_score: float) -> float:
    """
    Calculate the probability of winning based on current scores.
    This is a simplified model and could be improved with historical data.
    """
    # Basic probability based on score difference
    total_score = team1_score + team2_score
    if total_score == 0:
        return 0.5  # Equal chance if no scoring yet
    return team1_score / total_score

def create_matchup_card(matchup: Dict[str, Any]):
    """Create a card visualization for a single matchup."""
    
    team1 = matchup["team1"]
    team2 = matchup["team2"]
    team1_score = matchup["team1Score"]
    team2_score = matchup["team2Score"]
    
    # Calculate who's winning
    is_team1_winning = team1_score > team2_score
    winning_team = team1 if is_team1_winning else team2
    win_probability = calculate_winning_probability(team1_score, team2_score)
    
    # Create a visually appealing card using native Streamlit components
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"<h3 style='text-align: center; color: {'red' if is_team1_winning else 'white'};'>{format_score(team1_score)}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: white;'>{team1}</p>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<p style='text-align: center; font-weight: bold; color: #3080ff;'>VS</p>", unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"<h3 style='text-align: center; color: {'red' if not is_team1_winning else 'white'};'>{format_score(team2_score)}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: white;'>{team2}</p>", unsafe_allow_html=True)
        
        # Add a progress bar to show win probability
        st.progress(win_probability)
        
        # Show who's leading
        score_diff = abs(team1_score - team2_score)
        st.markdown(f"<p style='text-align: center; color: red; font-weight: bold;'>{winning_team} leading by {format_score(score_diff)}</p>", unsafe_allow_html=True)
        
        # Add a divider
        st.markdown("---")

def create_matchups_summary_chart(matchups_df):
    """Create a summary chart of all matchups."""
    if matchups_df.empty:
        return None
    
    # Prepare data for visualization
    team_scores = []
    
    for _, row in matchups_df.iterrows():
        team_scores.append({
            "team": row["team1"],
            "score": row["team1Score"]
        })
        team_scores.append({
            "team": row["team2"],
            "score": row["team2Score"]
        })
    
    scores_df = pd.DataFrame(team_scores)
    scores_df = scores_df.sort_values("score", ascending=False)
    
    # Create horizontal bar chart with adjustable height based on number of teams
    team_count = len(scores_df)
    chart_height = max(400, team_count * 25)  # 25px per team, minimum 400px
    
    fig = px.bar(
        scores_df,
        x="score",
        y="team",
        orientation="h",
        text="score",
        color="score",
        color_continuous_scale=["#3080ff", "#ff3030"],
        labels={"score": "Fantasy Points", "team": ""}
    )
    
    fig.update_layout(
        title="Team Scores Comparison",
        font=dict(family="Arial", size=14, color="#dddddd"),
        paper_bgcolor="#1a1c23",
        plot_bgcolor="#1a1c23",
        margin=dict(l=10, r=10, t=60, b=10),
        xaxis=dict(
            gridcolor="#333333",
            title=dict(text="Fantasy Points"),
            title_font=dict(size=14, color="#dddddd"),
        ),
        yaxis=dict(
            gridcolor="#333333",
            automargin=True,  # Ensure team names are fully visible
        ),
        coloraxis_showscale=False,
        height=chart_height
    )
    
    fig.update_traces(
        texttemplate="%{x:.1f}",
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f} pts<extra></extra>",
        marker=dict(line=dict(width=1, color="#1a1c23"))
    )
    
    return fig

def render():
    """Render the matchups page."""
    st.title("⚔️ Current Matchups")
    
    with st.expander("🔄 Refresh Options", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            scoring_period = st.number_input("Scoring Period", min_value=1, value=1, step=1)
        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        st.info("Using real matchup data from the Fantrax API.")
    
    # Show a loading spinner while fetching data
    with st.spinner("Fetching matchup data..."):
        # Get matchups data
        @st.cache_data(ttl=300)  # Cache for 5 minutes
        def get_matchups_data(period):
            try:
                api = FantraxAPI()
                live_data = api.get_live_scoring(period)
                
                # Parse the matchups data into a DataFrame
                matchups = []
                for idx, matchup in enumerate(live_data.get("liveScoringMatchups", [])):
                    home_team = matchup.get("home", {}).get("team", {}).get("name", f"Team {idx*2+1}")
                    away_team = matchup.get("away", {}).get("team", {}).get("name", f"Team {idx*2+2}")
                    home_score = matchup.get("home", {}).get("score", 0)
                    away_score = matchup.get("away", {}).get("score", 0)
                    
                    matchups.append({
                        "matchupId": idx + 1,
                        "team1": home_team,
                        "team2": away_team,
                        "team1Score": home_score,
                        "team2Score": away_score
                    })
                
                return pd.DataFrame(matchups)
            except Exception as e:
                st.error(f"Error fetching matchups: {str(e)}")
                return pd.DataFrame()
        
        matchups_df = get_matchups_data(scoring_period)
    
    if not matchups_df.empty:
        # Display summary chart
        st.subheader("📊 Matchups Overview")
        summary_chart = create_matchups_summary_chart(matchups_df)
        if summary_chart:
            st.plotly_chart(summary_chart, use_container_width=True)
        
        st.subheader("🏆 Individual Matchups")
        
        # Add pagination for matchups
        matchups_per_page = 5
        total_matchups = len(matchups_df)
        total_pages = (total_matchups + matchups_per_page - 1) // matchups_per_page  # Ceiling division
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            current_page = st.slider("Select Page", 1, max(1, total_pages), 1)
        
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * matchups_per_page
        end_idx = min(start_idx + matchups_per_page, total_matchups)
        
        # Display matchups for current page
        for idx in range(start_idx, end_idx):
            create_matchup_card(matchups_df.iloc[idx])
    else:
        st.error("No matchups data available. Please try refreshing or check your API connection.")