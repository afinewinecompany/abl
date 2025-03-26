import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Union, Tuple
import os
import numpy as np

# Define weighting factors
POWER_RANK_WEIGHT = 0.40  # 40% of the score based on current power ranking
PROSPECT_WEIGHT = 0.30    # 30% of the score based on prospect strength
HISTORY_WEIGHT = 0.20     # 20% of the score based on historical performance
PLAYOFF_WEIGHT = 0.10     # 10% of the score based on playoff performance

# Historical weights (more recent years weighted more heavily)
HISTORY_WEIGHTS = {
    "2024": 0.40,  # 40% of historical score from most recent year
    "2023": 0.30,  # 30% of historical score from previous year
    "2022": 0.20,  # 20% of historical score from 2 years ago
    "2021": 0.10,  # 10% of historical score from 3 years ago
}

# Playoff finish weights
PLAYOFF_POINTS = {
    "1st": 45,  # Points for championship
    "2nd": 30,  # Points for runner-up
    "3rd": 15,  # Points for third place
}

# Historical playoff finishes
PLAYOFF_HISTORY = {
    "2021": {"1st": "Pittsburgh Pirates", "2nd": "Detroit Tigers", "3rd": "Philadelphia Phillies"},
    "2022": {"1st": "Pittsburgh Pirates", "2nd": "Cleveland Guardians", "3rd": "Texas Rangers"},
    "2023": {"1st": "Kansas City Royals", "2nd": "Los Angeles Dodgers", "3rd": "New York Yankees"},
    "2024": {"1st": "Detroit Tigers", "2nd": "Pittsburgh Pirates", "3rd": "Los Angeles Dodgers"}
}

def load_historical_data() -> Dict[str, pd.DataFrame]:
    """Load historical season data from CSV files"""
    history_data = {}
    
    # Check if the historical data files exist
    for year in ["2021", "2022", "2023", "2024"]:
        csv_path = f"attached_assets/abl history - {year}.csv"
        if os.path.exists(csv_path):
            history_data[year] = pd.read_csv(csv_path)
    
    return history_data

def calculate_playoff_score(team_name: str) -> float:
    """Calculate a team's playoff performance score based on playoff history"""
    
    total_playoff_score = 0.0
    
    # Handle special cases for team name variations in historical data
    search_names = [team_name]
    if team_name == "Athletics" or team_name == "Las Vegas Athletics":
        search_names = ["Oakland Athletics", "Las Vegas Athletics"]
    
    # Process each year in playoff history
    for year, places in PLAYOFF_HISTORY.items():
        year_weight = HISTORY_WEIGHTS.get(year, 0.0)
        
        # Check if this team appears in playoff results
        playoff_result = None
        for place, playoff_team in places.items():
            # Handle Athletics name variations
            if playoff_team == "Oakland Athletics" and year == "2024" and "Las Vegas Athletics" in search_names:
                playoff_team = "Las Vegas Athletics"
            elif playoff_team == "Las Vegas Athletics" and year != "2024" and "Oakland Athletics" in search_names:
                playoff_team = "Oakland Athletics"
                
            # Check if playoff team matches any of our search names
            if any(playoff_team == search_name for search_name in search_names):
                playoff_result = place
                break
                
        # If team has a playoff finish, add weighted points
        if playoff_result:
            playoff_points = PLAYOFF_POINTS.get(playoff_result, 0)
            total_playoff_score += playoff_points * year_weight
    
    # Normalize to 0-100 scale based on maximum possible points
    # Max possible = winning 1st place every year (45 points * sum of year weights)
    max_possible = 45.0 * sum(HISTORY_WEIGHTS.values())
    normalized_score = (total_playoff_score / max_possible * 100) if max_possible > 0 else 0
    
    return normalized_score

def calculate_historical_score(team_name: str, history_data: Dict[str, pd.DataFrame]) -> float:
    """Calculate a team's historical performance score based on past seasons (excluding playoffs)"""
    
    if not history_data:
        return 0.0
        
    total_score = 0.0
    
    # Handle special cases for team name variations in historical data
    search_names = [team_name]
    if team_name == "Athletics" or team_name == "Las Vegas Athletics":
        search_names = ["Oakland Athletics", "Las Vegas Athletics"]
    
    # Debug info
    print(f"Calculating historical score for team: {team_name}, searching: {search_names}")
    
    for year, data in history_data.items():
        year_weight = HISTORY_WEIGHTS.get(year, 0.0)
        
        # Try all possible team names
        team_data = None
        for search_name in search_names:
            # If we're in 2024 and searching for Oakland Athletics, use Las Vegas Athletics
            if year == "2024" and search_name == "Oakland Athletics":
                search_name = "Las Vegas Athletics"
            # If we're in 2021-2023 and searching for Las Vegas Athletics, use Oakland Athletics
            elif year != "2024" and search_name == "Las Vegas Athletics":
                search_name = "Oakland Athletics"
                
            # Find the team in this year's data
            found_data = data[data['Team'] == search_name]
            if len(found_data) > 0:
                team_data = found_data
                break
        
        # If no team data found with any name, skip this year
        if team_data is None or len(team_data) == 0:
            print(f"No data found for {team_name} in {year}")
            continue
            
        # Calculate score based on Win% (scale from 0-100)
        win_pct = team_data['Win%'].values[0]
        win_pct_score = win_pct * 100
        
        # Get team rank and calculate rank score (1st = 100, 30th = 0, linear scale)
        rank = team_data['Rk'].values[0]
        total_teams = len(data['Team'].unique())
        rank_score = 100 * (1 - ((rank - 1) / (total_teams - 1)) if total_teams > 1 else 1)
        
        # Get fantasy points and calculate relative score
        # (team points / max points in that year) * 100
        fpts = team_data['FPts'].values[0]
        max_fpts = data['FPts'].max()
        fpts_score = (fpts / max_fpts) * 100 if max_fpts > 0 else 0
        
        # Combine the three metrics with equal weighting
        season_score = (win_pct_score + rank_score + fpts_score) / 3
        
        # Apply year weighting and add to total
        total_score += season_score * year_weight
    
    return total_score

def get_team_prospect_scores(roster_data: pd.DataFrame) -> pd.DataFrame:
    """
    Get team prospect scores by matching ANY player on the roster with the ABL-Import.csv file.
    This includes all players, not just those with MINORS status.
    """
    try:
        # Import the normalize_name function
        from components.prospects import normalize_name
        
        # Read prospect import data
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        
        # Normalize names in prospect import
        prospect_import['Name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)
        
        # Create team-level results
        team_prospect_scores = []
        
        # Process each team
        for team in roster_data['team'].unique():
            # Filter data by team
            team_roster = roster_data[roster_data['team'] == team].copy()
            team_roster['clean_name'] = team_roster['player_name'].fillna('').astype(str).apply(normalize_name)
            
            # IMPORTANT: Include ALL players, not just minors
            # Merge with prospect data
            team_prospects = pd.merge(
                team_roster,
                prospect_import[['Name', 'Score', 'Rank']], 
                left_on='clean_name',
                right_on='Name',
                how='left'
            )
            
            # Only include players that actually matched with the prospect data (have a Score)
            team_prospects = team_prospects[team_prospects['Score'].notna()]
            
            # Calculate prospect stats
            total_score = team_prospects['Score'].fillna(0).sum()
            avg_score = team_prospects['Score'].fillna(0).mean() if len(team_prospects) > 0 else 0
            count = len(team_prospects)
            
            # Add to results
            team_prospect_scores.append({
                'team': team,
                'total_score': total_score,
                'avg_score': avg_score,
                'prospect_count': count
            })
            
            # Debug for specific teams
            if team in ["Baltimore Orioles", "Kansas City Royals", "Atlanta Braves"]:
                print(f"Team '{team}' ALL prospects details:")
                print(f"  Total players matched: {len(team_prospects)}")
                print(f"  Players with scores: {team_prospects['Score'].notna().sum()}")
                print(f"  Total score: {total_score:.2f}")
                # Show the top 5 prospects for this team
                if len(team_prospects) > 0:
                    top_5 = team_prospects.sort_values('Score', ascending=False).head(5)
                    print(f"  Top 5 prospects:")
                    for _, row in top_5.iterrows():
                        print(f"    {row['player_name']} - Score: {row['Score']:.2f}, Rank: {row['Rank'] if pd.notna(row['Rank']) else 'N/A'}")
        
        # Convert to DataFrame
        team_scores = pd.DataFrame(team_prospect_scores)
        
        # Additional debug info - show the top teams
        print("\nTeam prospect scores (top 5):")
        for _, row in team_scores.sort_values('total_score', ascending=False).head(5).iterrows():
            print(f"{row['team']}: {row['total_score']:.2f} (Count: {int(row['prospect_count'])})")
        
        # Special debug for the teams mentioned
        print("\nReference team scores:")
        for team_name in ["Baltimore Orioles", "Kansas City Royals", "Atlanta Braves"]:
            team_data = team_scores[team_scores['team'] == team_name]
            if len(team_data) > 0:
                print(f"  {team_name}: {team_data['total_score'].values[0]:.2f}")
            else:
                print(f"  {team_name}: not found in team_scores")
        
        return team_scores
        
    except Exception as e:
        st.error(f"Error calculating team prospect scores: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
        # Return a simple DataFrame with empty scores
        teams = roster_data['team'].unique()
        return pd.DataFrame({
            'team': teams,
            'total_score': [0] * len(teams),
            'avg_score': [0] * len(teams),
            'prospect_count': [0] * len(teams)
        })

def calculate_ddi_scores(roster_data: pd.DataFrame, power_rankings: pd.DataFrame, history_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calculate the Dynasty Dominance Index for all teams"""
    
    # Get team prospect scores directly from the handbook calculation
    team_prospect_scores = get_team_prospect_scores(roster_data)
    
    # Extract unique teams from roster data
    teams = roster_data['team'].unique()
    
    # Create a DataFrame to store DDI components and total scores
    ddi_data = []
    
    for team in teams:
        # Account for "Oakland Athletics" / "Athletics" naming variants
        team_display = team  # Use this name for display
        
        # Handle Athletics name variation
        team_search = team
        team_history_search = team
        
        # For current API data (team might be "Athletics")
        if team == "Athletics":
            team_search = "Las Vegas Athletics"  # For current data
            team_history_search = "Oakland Athletics"  # For historical years 2021-2023
        
        # When looking at history data directly
        elif team == "Las Vegas Athletics":
            team_history_search = "Oakland Athletics"  # For historical years 2021-2023
        
        # Get power ranking score (normalized from 0-100, where 100 is best)
        # Try multiple possible column names for team and power score (handle different formats)
        team_col = 'team_name' if 'team_name' in power_rankings.columns else 'Team'
        score_col = 'power_score' if 'power_score' in power_rankings.columns else 'Power Score'
        
        team_power = power_rankings[(power_rankings[team_col] == team) | (power_rankings[team_col] == team_search)]
        if len(team_power) > 0:
            # Normalize power score where highest is 100
            max_score = power_rankings[score_col].max()
            if max_score > 0:
                power_score = (team_power[score_col].values[0] / max_score) * 100
            else:
                # Default to 100 if we have no valid power scores
                power_score = 100
        else:
            # Default to 100 as requested
            power_score = 100
            
        # Get prospect score from the handbook calculation (total_score from each team)
        team_prospects = team_prospect_scores[(team_prospect_scores['team'] == team) | (team_prospect_scores['team'] == team_search)]
        if len(team_prospects) > 0:
            # Get total prospect score and normalize to 0-100
            total_prospect_score = team_prospects['total_score'].values[0]
            # Normalize to 0-100 scale
            max_prospect_score = team_prospect_scores['total_score'].max()
            prospect_score = (total_prospect_score / max_prospect_score) * 100 if max_prospect_score > 0 else 0
        else:
            prospect_score = 0
            
        # Get historical performance score
        history_score = calculate_historical_score(team, history_data)
        
        # Get playoff performance score
        playoff_score = calculate_playoff_score(team)
        
        # Calculate overall DDI score with component weighting
        ddi_score = (
            (power_score * POWER_RANK_WEIGHT) +
            (prospect_score * PROSPECT_WEIGHT) +
            (history_score * HISTORY_WEIGHT) +
            (playoff_score * PLAYOFF_WEIGHT)
        )
        
        # Add to our data collection
        ddi_data.append({
            'Team': team,
            'Power Score': power_score,
            'Prospect Score': prospect_score,
            'Historical Score': history_score,
            'Playoff Score': playoff_score,
            'DDI Score': ddi_score
        })
    
    # Convert to DataFrame and sort by DDI Score
    ddi_df = pd.DataFrame(ddi_data)
    ddi_df = ddi_df.sort_values('DDI Score', ascending=False).reset_index(drop=True)
    
    # Add rank column based on DDI Score
    ddi_df['Rank'] = ddi_df.index + 1
    
    # Reorder columns to put Rank first
    ddi_df = ddi_df[['Rank', 'Team', 'DDI Score', 'Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score']]
    
    return ddi_df

def get_team_colors(team_name: str) -> dict:
    """Get team primary and secondary colors based on team name"""
    # Map of team names to primary and secondary colors
    team_colors = {
        'Pittsburgh Pirates': {'primary': '#FDB827', 'secondary': '#000000'},
        'Detroit Tigers': {'primary': '#0C2340', 'secondary': '#FA4616'},
        'Los Angeles Dodgers': {'primary': '#005A9C', 'secondary': '#FFFFFF'},
        'New York Yankees': {'primary': '#0C2340', 'secondary': '#FFFFFF'},
        'Kansas City Royals': {'primary': '#004687', 'secondary': '#BD9B60'},
        'Cleveland Guardians': {'primary': '#00385D', 'secondary': '#E31937'},
        'Texas Rangers': {'primary': '#C0111F', 'secondary': '#003278'},
        'Philadelphia Phillies': {'primary': '#E81828', 'secondary': '#002D72'},
        'Saint Louis Cardinals': {'primary': '#C41E3A', 'secondary': '#0C2340'},
        'Atlanta Braves': {'primary': '#CE1141', 'secondary': '#13274F'},
        'Baltimore Orioles': {'primary': '#DF4601', 'secondary': '#000000'},
        'Arizona Diamondbacks': {'primary': '#A71930', 'secondary': '#E3D4AD'},
        'Boston Red Sox': {'primary': '#BD3039', 'secondary': '#0C2340'},
        'Chicago Cubs': {'primary': '#0E3386', 'secondary': '#CC3433'},
        'Chicago White Sox': {'primary': '#000000', 'secondary': '#C4CED4'},
        'Cincinnati Reds': {'primary': '#C6011F', 'secondary': '#000000'},
        'Colorado Rockies': {'primary': '#33006F', 'secondary': '#C4CED4'},
        'Houston Astros': {'primary': '#002D62', 'secondary': '#EB6E1F'},
        'Los Angeles Angels': {'primary': '#BA0021', 'secondary': '#003263'},
        'Miami Marlins': {'primary': '#00A3E0', 'secondary': '#EF3340'},
        'Milwaukee Brewers': {'primary': '#0A2351', 'secondary': '#FFC52F'},
        'Minnesota Twins': {'primary': '#002B5C', 'secondary': '#D31145'},
        'New York Mets': {'primary': '#002D72', 'secondary': '#FF5910'},
        'Oakland Athletics': {'primary': '#003831', 'secondary': '#EFB21E'},
        'Athletics': {'primary': '#003831', 'secondary': '#EFB21E'},
        'Las Vegas Athletics': {'primary': '#003831', 'secondary': '#EFB21E'},
        'San Diego Padres': {'primary': '#2F241D', 'secondary': '#FFC425'},
        'San Francisco Giants': {'primary': '#FD5A1E', 'secondary': '#000000'},
        'Seattle Mariners': {'primary': '#0C2C56', 'secondary': '#005C5C'},
        'Tampa Bay Rays': {'primary': '#092C5C', 'secondary': '#8FBCE6'},
        'Toronto Blue Jays': {'primary': '#134A8E', 'secondary': '#1D2D5C'},
        'Washington Nationals': {'primary': '#AB0003', 'secondary': '#14225A'},
    }
    
    # Default to a standard color if team not found
    return team_colors.get(team_name, {'primary': '#1E88E5', 'secondary': '#0D47A1'})


def get_team_logo_url(team_name: str) -> str:
    """Get MLB team logo URL"""
    # Clean team name for URL formatting
    clean_name = team_name.lower().replace(' ', '-')
    
    # Handle special cases
    if 'athletics' in clean_name:
        clean_name = 'oakland-athletics'  # Use Oakland for now since that's the established logo
    elif 'guardians' in clean_name:
        clean_name = 'cleveland-guardians'
    
    # Return the logo URL from MLB
    return f"https://www.mlbstatic.com/team-logos/{clean_name}.svg"

def create_ddi_visualization(ddi_df: pd.DataFrame) -> go.Figure:
    """Create a stacked bar visualization of DDI components"""
    
    # Prepare data for visualization
    fig = go.Figure()
    
    # Sort by DDI Score (highest to lowest)
    sorted_df = ddi_df.sort_values('DDI Score', ascending=False)
    
    # Add stacked components
    fig.add_trace(go.Bar(
        y=sorted_df['Team'],
        x=sorted_df['Power Score'] * POWER_RANK_WEIGHT,
        name='Power Ranking',
        orientation='h',
        marker=dict(color='#4CAF50'),
        text=[f"{score:.1f}" for score in sorted_df['Power Score']],
        hovertemplate="Power Score: %{text}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sorted_df['Team'],
        x=sorted_df['Prospect Score'] * PROSPECT_WEIGHT,
        name='Prospect System',
        orientation='h',
        marker=dict(color='#2196F3'),
        text=[f"{score:.1f}" for score in sorted_df['Prospect Score']],
        hovertemplate="Prospect Score: %{text}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sorted_df['Team'],
        x=sorted_df['Historical Score'] * HISTORY_WEIGHT,
        name='Historical Performance',
        orientation='h',
        marker=dict(color='#FFC107'),
        text=[f"{score:.1f}" for score in sorted_df['Historical Score']],
        hovertemplate="Historical Score: %{text}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sorted_df['Team'],
        x=sorted_df['Playoff Score'] * PLAYOFF_WEIGHT,
        name='Playoff Success',
        orientation='h',
        marker=dict(color='#E91E63'),
        text=[f"{score:.1f}" for score in sorted_df['Playoff Score']],
        hovertemplate="Playoff Score: %{text}<extra></extra>"
    ))
    
    # Add ranking markers
    for i, (_, row) in enumerate(sorted_df.iterrows()):
        fig.add_annotation(
            y=row['Team'],
            x=0,
            text=f"{row['Rank']}",
            showarrow=False,
            font=dict(color='white', size=14, family='Arial Black'),
            bgcolor='rgba(0, 0, 0, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.5)',
            borderwidth=1,
            borderpad=3,
            xanchor='right',
            xshift=-10
        )
    
    # Update layout
    fig.update_layout(
        title='Dynasty Dominance Index (DDI) - Component Breakdown',
        barmode='stack',
        height=600,
        margin=dict(l=20, r=20, t=80, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            title="Component Weighted Score",
            gridcolor='rgba(255, 255, 255, 0.1)'
        ),
        yaxis=dict(
            title=None,
            autorange="reversed"
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='white')
    )
    
    return fig

def create_radar_chart(ddi_df: pd.DataFrame) -> go.Figure:
    """Create a radar chart comparing top teams across dimensions"""
    
    # Take top 5 teams for radar chart
    top_teams = ddi_df.head(5)
    
    # Set up categories for radar chart
    categories = ['Power Ranking', 'Prospect System', 'Historical Performance', 'Playoff Success']
    
    fig = go.Figure()
    
    # Add traces for each team
    for _, team in top_teams.iterrows():
        team_name = team['Team']
        fig.add_trace(go.Scatterpolar(
            r=[
                team['Power Score'], 
                team['Prospect Score'], 
                team['Historical Score'],
                team['Playoff Score']
            ],
            theta=categories,
            fill='toself',
            name=f"{team_name} (#{int(team['Rank'])})",
            line=dict(color=get_team_colors(team_name)['primary']),
            opacity=0.8
        ))
    
    # Update layout
    fig.update_layout(
        title="Top Dynasty Teams - Dimensional Comparison",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='rgba(255, 255, 255, 0.2)'
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.2)'
            ),
            bgcolor='rgba(0, 0, 0, 0)'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0, 0, 0, 0.5)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1
        ),
        height=500,
        margin=dict(l=80, r=80, t=80, b=80),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='white')
    )
    
    return fig

def create_treemap_chart(ddi_df: pd.DataFrame) -> go.Figure:
    """Create an interactive treemap visualization of DDI scores"""
    
    # Create a copy of the DataFrame for manipulation
    tm_df = ddi_df.copy()
    
    # Create custom hover text
    hover_texts = []
    for _, row in tm_df.iterrows():
        hover_text = (
            f"<b>{row['Team']}</b><br>" +
            f"DDI Score: {row['DDI Score']:.1f}<br>" +
            f"Rank: #{row['Rank']}<br>" +
            f"Power Score: {row['Power Score']:.1f}<br>" +
            f"Prospect Score: {row['Prospect Score']:.1f}<br>" +
            f"Historical Score: {row['Historical Score']:.1f}<br>" +
            f"Playoff Score: {row['Playoff Score']:.1f}"
        )
        hover_texts.append(hover_text)
    
    tm_df['hover_text'] = hover_texts
    
    # Get team colors for markers
    marker_colors = []
    for team in tm_df['Team']:
        colors = get_team_colors(team)
        marker_colors.append(colors['primary'])
    
    # Create treemap figure
    fig = px.treemap(
        tm_df,
        ids=tm_df.index,
        names='Team',
        parents=["" for _ in range(len(tm_df))],
        values='DDI Score',
        color='DDI Score',
        hover_data=['Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score'],
        color_continuous_scale=['blue', 'lightblue', 'white', 'pink', 'red'],  # Red for high, Blue for low
        color_continuous_midpoint=tm_df['DDI Score'].median()
    )
    
    # Customize appearance
    fig.update_traces(
        hovertemplate=tm_df['hover_text'],
        textfont=dict(
            family='Arial',
            size=14
        ),
        textposition="middle center",
        texttemplate="<b>%{label}</b><br>#%{customdata[0]}<br>%{value:.1f}"
    )
    
    # Add rank to customdata
    fig.update_traces(
        customdata=tm_df[['Rank']].values
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Dynasty Dominance Index - Team Rankings',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=True,
        height=600
    )
    
    return fig

def create_heatmap_chart(ddi_df: pd.DataFrame) -> go.Figure:
    """Create an interactive heatmap of DDI components across teams"""
    
    # Create a subset of data with just the components we want
    heat_df = ddi_df[['Team', 'Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score']].copy()
    
    # Sort by overall DDI score (which is the ordering in the input DataFrame)
    heat_df = heat_df.sort_values('Team')
    
    # Melt the dataframe to get it in the right format for the heatmap
    melted_df = pd.melt(
        heat_df, 
        id_vars=['Team'], 
        value_vars=['Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score'],
        var_name='Component',
        value_name='Score'
    )
    
    # Create custom hover text
    melted_df['hover_text'] = melted_df.apply(
        lambda row: f"<b>{row['Team']}</b><br>{row['Component']}: {row['Score']:.1f}", 
        axis=1
    )
    
    # Create the heatmap
    fig = px.imshow(
        heat_df.set_index('Team')[['Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score']],
        labels=dict(x="Component", y="Team", color="Score"),
        x=['Power', 'Prospects', 'Historical', 'Playoffs'],
        y=heat_df['Team'],
        color_continuous_scale='Viridis',
        aspect="auto"
    )
    
    # Customize appearance
    fig.update_traces(
        text=heat_df.set_index('Team')[['Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score']].round(1).values,
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"}
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Team Performance by Component',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=50, r=20, t=50, b=20),
        height=800,
        xaxis=dict(
            title="Component",
            side="top"
        ),
        yaxis=dict(
            title="Team",
            autorange="reversed"
        )
    )
    
    return fig

def render_team_card(team_row):
    """Render a card for a team with its DDI information"""
    team_name = team_row['Team']
    team_colors = get_team_colors(team_name)
    
    # Ultra-simple card that should render properly
    card_html = f"""
    <div style="background: linear-gradient(135deg, {team_colors['primary']} 0%, {team_colors['secondary']} 100%); 
         border-radius: 10px; padding: 15px; margin: 10px 0; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <div style="text-align: right; font-size: 24px; font-weight: bold; margin-bottom: 5px;">#{int(team_row['Rank'])}</div>
        <div style="font-size: 20px; font-weight: bold; margin-bottom: 5px;">{team_name}</div>
        <div style="font-weight: bold; margin-bottom: 10px;">DDI Score: {team_row['DDI Score']:.1f}</div>
        <div>Power: <b>{team_row['Power Score']:.1f}</b> | Prospects: <b>{team_row['Prospect Score']:.1f}</b> | History: <b>{team_row['Historical Score']:.1f}</b> | Playoffs: <b>{team_row['Playoff Score']:.1f}</b></div>
    </div>
    """
    
    return card_html

def render(roster_data: pd.DataFrame):
    """Render Dynasty Dominance Index (DDI) page"""
    
    st.title("Dynasty Dominance Index (DDI)")
    
    st.markdown("""
    ### What is DDI?
    The Dynasty Dominance Index (DDI) combines a team's current power ranking, prospect system, historical performance, and playoff success to create a comprehensive evaluation of dynasty team health and trajectory.
    
    #### DDI Components:
    - **Current Power Rankings (40%)**: How strong is the team right now?
    - **Prospect System (30%)**: How strong is the team's future talent pipeline?
    - **Historical Performance (20%)**: How consistently successful has the team been over time?
    - **Playoff Success (10%)**: How well has the team performed in the playoffs?
    """)
    
    # Create a horizontal rule
    st.markdown("---")
    
    try:
        # Load historical data
        st.write("Loading historical performance data...")
        history_data = load_historical_data()
        
        if not history_data:
            st.error("Historical data files could not be found. Please check the attached_assets directory.")
            return
            
        # Calculate power rankings (we'll need to use the existing power_rankings component logic)
        # For this example, we'll create a simple power ranking based on available roster data
        teams = roster_data['team'].unique()
        
        # Try to import the power_rankings logic first
        try:
            from components import power_rankings
            power_rankings_df = calculate_power_rankings_from_component(roster_data)
        except:
            # If we can't import power_rankings, create a basic version
            power_rankings_data = []
            for team in teams:
                team_df = roster_data[roster_data['team'] == team]
                power_score = len(team_df) * 2  # Simple placeholder score
                power_rankings_data.append({
                    'Team': team,
                    'Power Score': power_score
                })
            power_rankings_df = pd.DataFrame(power_rankings_data)
        
        # Calculate DDI scores
        ddi_df = calculate_ddi_scores(roster_data, power_rankings_df, history_data)
        
        # Format DDI dataframe for display
        display_df = ddi_df.copy()
        for col in ['DDI Score', 'Power Score', 'Prospect Score', 'Historical Score', 'Playoff Score']:
            display_df[col] = display_df[col].round(1)
        
        # Create visualization tabs
        vis_tab1, vis_tab2, vis_tab3, vis_tab4 = st.tabs([
            "Team Rankings", 
            "Team Cards", 
            "Component Breakdown",
            "Top Teams Comparison"
        ])
        
        # Tab 1: Interactive Team Rankings Visualization
        with vis_tab1:
            st.markdown("""
            ### Dynasty Dominance Index - Team Rankings
            Interactive visualizations of team performance across all dimensions of the Dynasty Dominance Index.
            """)
            
            # Use tabs for different visualizations within the first tab
            viz_1, viz_2 = st.tabs(["Treemap View", "Component Heatmap"])
            
            with viz_1:
                st.markdown("""
                ### Team Rankings Treemap
                Size and color represent DDI score. Larger and darker boxes indicate higher scores.
                """)
                
                # Create the treemap chart
                treemap_chart = create_treemap_chart(display_df)
                
                # Simple config without unnecessary controls
                chart_config = {
                    'displayModeBar': True,
                    'responsive': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                }
                
                # Display the treemap visualization
                st.plotly_chart(treemap_chart, use_container_width=True, config=chart_config)
            
            with viz_2:
                st.markdown("""
                ### Team Performance by Component
                Heatmap showing how each team performs across the three DDI components.
                """)
                
                # Display the heatmap as a secondary visualization
                heatmap_chart = create_heatmap_chart(display_df)
                st.plotly_chart(heatmap_chart, use_container_width=True, config=chart_config)
        
        # Tab 2: Team Cards 
        with vis_tab2:
            st.markdown("### Dynasty Dominance Rankings")
            
            # Show team cards in a single column for better readability
            for _, team_row in display_df.iterrows():
                st.markdown(render_team_card(team_row), unsafe_allow_html=True)
            
            # Also show the traditional table below
            with st.expander("View as Table"):
                st.dataframe(
                    display_df,
                    column_config={
                        "Rank": st.column_config.NumberColumn(
                            "Rank",
                            help="Team rank by DDI score",
                            format="%d"
                        ),
                        "Team": st.column_config.TextColumn(
                            "Team",
                            help="Team name"
                        ),
                        "DDI Score": st.column_config.NumberColumn(
                            "DDI Score",
                            help="Overall Dynasty Dominance Index score",
                            format="%.1f"
                        ),
                        "Power Score": st.column_config.NumberColumn(
                            "Power",
                            help="Current team strength score (0-100)",
                            format="%.1f"
                        ),
                        "Prospect Score": st.column_config.NumberColumn(
                            "Prospects",
                            help="Prospect system strength score (0-100)",
                            format="%.1f"
                        ),
                        "Historical Score": st.column_config.NumberColumn(
                            "History",
                            help="Historical performance score (0-100)",
                            format="%.1f"
                        ),
                        "Playoff Score": st.column_config.NumberColumn(
                            "Playoffs",
                            help="Playoff success score (0-100)",
                            format="%.1f"
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
        
        # Tab 3: Component Breakdown
        with vis_tab3:
            st.plotly_chart(create_ddi_visualization(ddi_df), use_container_width=True)
            
            # Add explanation of component weighting
            st.info(f"""
            **DDI Component Weighting:**
            - Power Rankings: {POWER_RANK_WEIGHT*100}%
            - Prospect System: {PROSPECT_WEIGHT*100}%
            - Historical Performance: {HISTORY_WEIGHT*100}%
            - Playoff Success: {PLAYOFF_WEIGHT*100}%
            """)
            
        # Tab 4: Top Teams Comparison
        with vis_tab4:
            st.plotly_chart(create_radar_chart(ddi_df), use_container_width=True)
            
            # Add breakdown of historical weighting
            st.info(f"""
            **Historical Performance Weighting:**
            - 2024 Season: {HISTORY_WEIGHTS['2024']*100}%
            - 2023 Season: {HISTORY_WEIGHTS['2023']*100}%
            - 2022 Season: {HISTORY_WEIGHTS['2022']*100}%
            - 2021 Season: {HISTORY_WEIGHTS['2021']*100}%
            """)
            
            # Add breakdown of playoff scoring
            st.info(f"""
            **Playoff Success Points:**
            - 1st Place: {PLAYOFF_POINTS['1st']} points
            - 2nd Place: {PLAYOFF_POINTS['2nd']} points
            - 3rd Place: {PLAYOFF_POINTS['3rd']} points
            
            Playoff points are weighted by season recency and normalized to a 0-100 scale.
            """)
        
    except Exception as e:
        st.error(f"Error calculating DDI rankings: {str(e)}")
        import traceback
        st.write(traceback.format_exc())

def calculate_power_rankings_from_component(roster_data: pd.DataFrame) -> pd.DataFrame:
    """
    Create power rankings based on roster data when we can't import 
    the power_rankings component directly
    """
    try:
        # Import power_rankings module and get actual power rankings data
        from components import power_rankings
        from utils import fetch_api_data, fetch_fantrax_data
        
        # First try to get real standings data from app.py's data flow
        try:
            data = fetch_api_data()
            if data and 'standings_data' in data:
                # Create a mock version of power_rankings.render()
                # that returns the actual power rankings DataFrame
                
                # Import the original function
                from components.power_rankings import calculate_power_score
                
                # Process the data the same way as in power_rankings.render()
                rankings_df = data['standings_data'].copy()
                
                # Add required fields for power score calculation
                rankings_df['total_points'] = rankings_df['wins'] * 2  # Assuming 2 points per win
                rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']
                rankings_df['recent_wins'] = rankings_df['wins'].rolling(window=3, min_periods=1).mean()
                rankings_df['recent_losses'] = rankings_df['losses'].rolling(window=3, min_periods=1).mean()
                
                # Calculate power scores
                rankings_df['power_score'] = rankings_df.apply(lambda x: calculate_power_score(x, rankings_df), axis=1)
                rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)
                
                # Rename columns to match expected format
                rankings_df = rankings_df.rename(columns={
                    'team_name': 'Team',
                    'power_score': 'Power Score'
                })
                
                # Keep only the columns we need
                if 'Team' not in rankings_df.columns and 'team_name' in rankings_df.columns:
                    rankings_df['Team'] = rankings_df['team_name']
                
                if 'Power Score' not in rankings_df.columns and 'power_score' in rankings_df.columns:
                    rankings_df['Power Score'] = rankings_df['power_score']
                    
                rankings_df = rankings_df[['Team', 'Power Score']]
                
                return rankings_df
        except Exception as e:
            print(f"Error getting power rankings from API data: {str(e)}")
            # Fall back to generating power scores directly
        
        # If we can't get real data, create power scores with the right calculation method
        from components.power_rankings import calculate_power_score
        
        # Group data by team
        teams = roster_data['team'].unique()
        power_data = []
        
        for team in teams:
            team_roster = roster_data[roster_data['team'] == team]
            
            # Create a reasonably realistic row with the required fields
            mock_row = pd.Series({
                'total_points': len(team_roster) * 10,
                'weeks_played': 10,  # Fixed value for now
                'recent_wins': min(len(team_roster) / 4, 8),  # Scale with roster size, max 8
                'recent_losses': min(10 - (len(team_roster) / 4), 4)  # Scale inversely
            })
            
            # Calculate power score using the real function
            power_score = calculate_power_score(mock_row, pd.DataFrame([mock_row]))
            
            power_data.append({
                'Team': team,
                'Power Score': power_score
            })
            
        return pd.DataFrame(power_data)
        
    except ImportError:
        # If we can't import power_rankings, create a basic version 
        # but with more realistic values that won't be zero
        teams = roster_data['team'].unique()
        power_rankings_data = []
        
        for team in teams:
            team_df = roster_data[roster_data['team'] == team]
            # Use roster size as a realistic proxy for team strength
            # Multiply by a factor to get scores in a reasonable range (50-150)
            power_score = len(team_df) * 4 + 30
            
            power_rankings_data.append({
                'Team': team,
                'Power Score': power_score
            })
            
        return pd.DataFrame(power_rankings_data)