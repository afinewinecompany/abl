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
    
    # Create a visually appealing card
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.9) 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(30, 100, 255, 0.1);
            margin-bottom: 1rem;
            box-shadow: 0 0 20px rgba(30, 100, 255, 0.15);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: #ffffff;">{team1} vs {team2}</h3>
                <span style="font-size: 0.9rem; color: #aaaaaa;">Matchup #{matchup["matchupId"]}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: {'#ff3030' if is_team1_winning else '#ffffff'};">
                        {format_score(team1_score)}
                    </div>
                    <div style="font-size: 1.1rem; color: #dddddd;">{team1}</div>
                </div>
                
                <div style="text-align: center; padding: 0 1rem;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #3080ff;">VS</div>
                </div>
                
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: {'#ff3030' if not is_team1_winning else '#ffffff'};">
                        {format_score(team2_score)}
                    </div>
                    <div style="font-size: 1.1rem; color: #dddddd;">{team2}</div>
                </div>
            </div>
            
            <div style="margin-top: 1.5rem;">
                <div style="height: 8px; background: #333333; border-radius: 4px; overflow: hidden;">
                    <div style="
                        height: 100%; 
                        width: {win_probability * 100}%; 
                        background: linear-gradient(90deg, #3080ff, #ff3030); 
                        border-radius: 4px;"
                    ></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.3rem;">
                    <div style="font-size: 0.8rem; color: #888888;">{team1}</div>
                    <div style="font-size: 0.8rem; color: #ff3030; font-weight: 600;">
                        {winning_team} leading by {format_score(abs(team1_score - team2_score))}
                    </div>
                    <div style="font-size: 0.8rem; color: #888888;">{team2}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    
    # Create horizontal bar chart
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
            gridcolor="#333333"
        ),
        coloraxis_showscale=False,
        height=400
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
        
        st.info("Using integrated FantraxAPI for matchup data.")
    
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
        
        for _, matchup in matchups_df.iterrows():
            create_matchup_card(matchup)
    else:
        st.error("No matchups data available. Please try refreshing or check your API connection.")