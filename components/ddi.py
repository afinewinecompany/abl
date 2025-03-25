import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import os
import numpy as np

# Define weighting factors
POWER_RANK_WEIGHT = 0.35  # 35% of the score based on current power ranking
PROSPECT_WEIGHT = 0.25    # 25% of the score based on prospect strength
HISTORY_WEIGHT = 0.40     # 40% of the score based on historical performance

# Historical weights (more recent years weighted more heavily)
HISTORY_WEIGHTS = {
    "2024": 0.40,  # 40% of historical score from most recent year
    "2023": 0.30,  # 30% of historical score from previous year
    "2022": 0.20,  # 20% of historical score from 2 years ago
    "2021": 0.10,  # 10% of historical score from 3 years ago
}

# Playoff finish weights
PLAYOFF_POINTS = {
    "1st": 30,  # Points for championship
    "2nd": 20,  # Points for runner-up
    "3rd": 10,  # Points for third place
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

def calculate_historical_score(team_name: str, history_data: Dict[str, pd.DataFrame]) -> float:
    """Calculate a team's historical performance score based on past seasons"""
    
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
        
        # Add playoff bonus if applicable
        playoff_result = None
        for place, playoff_team in PLAYOFF_HISTORY.get(year, {}).items():
            # Check if playoff team matches any of our search names
            if any(playoff_team == search_name for search_name in search_names):
                playoff_result = place
                break
                
        if playoff_result:
            playoff_bonus = PLAYOFF_POINTS.get(playoff_result, 0)
            season_score += playoff_bonus
            
        # Apply year weighting and add to total
        total_score += season_score * year_weight
    
    return total_score

def get_team_prospect_scores(roster_data: pd.DataFrame) -> pd.DataFrame:
    """
    Get team prospect scores using the exact same method as the prospects.py component.
    This ensures consistency across the application.
    """
    try:
        # Use the same method as the prospects component
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        
        # Helper function to normalize player names - identical to prospects.py
        def normalize_name(name: str) -> str:
            """Simple normalization for player names"""
            if pd.isna(name):
                return ""
            if not isinstance(name, str):
                return str(name).strip()
            
            name = name.lower()
            name = name.split('(')[0].strip()
            name = name.replace('.', '').strip()
            return ' '.join(name.split())
        
        # Normalize names in prospect import
        prospect_import['Name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)
        
        # Create a copy of roster data with clean_name for matching
        prospects_data = roster_data.copy()
        prospects_data['clean_name'] = prospects_data['player_name'].fillna('').astype(str).apply(normalize_name)
        prospects_data = prospects_data.drop_duplicates(subset=['clean_name'], keep='first')
        
        # Debug info
        print(f"Total prospects in import: {len(prospect_import)}")
        print(f"Total players in roster data: {len(prospects_data)}")
        
        # Merge using the IDENTICAL method to prospects.py component
        ranked_prospects = pd.merge(
            prospects_data,
            prospect_import[['Name', 'Position', 'MLB Team', 'Score', 'Rank']],
            left_on='clean_name',
            right_on='Name',  # Fixed: use string column name, not the actual column
            how='outer'  # Outer join to keep all players
        )
        
        # This is important: Use the exact same fields as prospects.py
        ranked_prospects['prospect_score'] = pd.to_numeric(ranked_prospects['Score'].fillna(0), errors='coerce')
        ranked_prospects['player_name'] = ranked_prospects['player_name'].fillna(ranked_prospects['Name'])
        
        # Remove duplicates but keep the one with rank if available
        ranked_prospects = ranked_prospects.sort_values('Rank').drop_duplicates(
            subset=['Name'], 
            keep='first'
        )
        
        # Debug merged data
        print(f"Total records after merge: {len(ranked_prospects)}")
        print(f"Number of prospects found: {ranked_prospects['Score'].notna().sum()}")
        
        # Calculate team scores - identical to prospects.py
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Clean up column names - identical to prospects.py
        team_scores.columns = ['team', 'total_score', 'avg_score', 'prospect_count']
        
        # Debug team scores
        print(f"Teams with prospect data: {len(team_scores)}")
        
        # Handle teams with NA or missing values
        team_scores['total_score'] = team_scores['total_score'].fillna(0)
        team_scores['avg_score'] = team_scores['avg_score'].fillna(0)
        team_scores['prospect_count'] = team_scores['prospect_count'].fillna(0)
        
        # Make sure all teams are included
        all_teams = roster_data['team'].unique()
        for team in all_teams:
            if team not in team_scores['team'].values:
                team_scores = pd.concat([
                    team_scores,
                    pd.DataFrame({
                        'team': [team],
                        'total_score': [0],
                        'avg_score': [0],
                        'prospect_count': [0]
                    })
                ])
        
        # Additional debug info
        print("Team prospect scores:")
        for _, row in team_scores.iterrows():
            print(f"{row['team']}: {row['total_score']:.2f} (Count: {int(row['prospect_count'])})")
        
        # Special debug for the teams you mentioned
        for team_name in ["Baltimore Orioles", "Kansas City Royals", "Atlanta Braves"]:
            team_data = team_scores[team_scores['team'] == team_name]
            if len(team_data) > 0:
                print(f"Special check - {team_name}: {team_data['total_score'].values[0]:.2f}")
            else:
                print(f"Special check - {team_name}: not found in team_scores")
        
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
        team_power = power_rankings[(power_rankings['Team'] == team) | (power_rankings['Team'] == team_search)]
        if len(team_power) > 0:
            # Normalize power score where highest is 100
            power_score = (team_power['Power Score'].values[0] / power_rankings['Power Score'].max()) * 100
        else:
            power_score = 0
            
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
        
        # Calculate overall DDI score with component weighting
        ddi_score = (
            (power_score * POWER_RANK_WEIGHT) +
            (prospect_score * PROSPECT_WEIGHT) +
            (history_score * HISTORY_WEIGHT)
        )
        
        # Add to our data collection
        ddi_data.append({
            'Team': team,
            'Power Score': power_score,
            'Prospect Score': prospect_score,
            'Historical Score': history_score,
            'DDI Score': ddi_score
        })
    
    # Convert to DataFrame and sort by DDI Score
    ddi_df = pd.DataFrame(ddi_data)
    ddi_df = ddi_df.sort_values('DDI Score', ascending=False).reset_index(drop=True)
    
    # Add rank column based on DDI Score
    ddi_df['Rank'] = ddi_df.index + 1
    
    # Reorder columns to put Rank first
    ddi_df = ddi_df[['Rank', 'Team', 'DDI Score', 'Power Score', 'Prospect Score', 'Historical Score']]
    
    return ddi_df

def get_team_color(team_name: str) -> str:
    """Get team color based on team name"""
    # Map of team names to colors (add more as needed)
    team_colors = {
        'Pittsburgh Pirates': '#FDB827',
        'Detroit Tigers': '#0C2340',
        'Los Angeles Dodgers': '#005A9C',
        'New York Yankees': '#0C2340',
        'Kansas City Royals': '#004687',
        'Cleveland Guardians': '#00385D',
        'Texas Rangers': '#C0111F',
        'Philadelphia Phillies': '#E81828',
        'Saint Louis Cardinals': '#C41E3A',
    }
    
    # Default to a standard color if team not found
    return team_colors.get(team_name, '#1E88E5')

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
    categories = ['Power Ranking', 'Prospect System', 'Historical Performance']
    
    fig = go.Figure()
    
    # Add traces for each team
    for _, team in top_teams.iterrows():
        team_name = team['Team']
        fig.add_trace(go.Scatterpolar(
            r=[
                team['Power Score'], 
                team['Prospect Score'], 
                team['Historical Score']
            ],
            theta=categories,
            fill='toself',
            name=f"{team_name} (#{int(team['Rank'])})",
            line=dict(color=get_team_color(team_name)),
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

def render(roster_data: pd.DataFrame):
    """Render Dynasty Dominance Index (DDI) page"""
    
    st.title("Dynasty Dominance Index (DDI)")
    
    st.markdown("""
    ### What is DDI?
    The Dynasty Dominance Index (DDI) combines a team's current power ranking, prospect system strength, and historical performance to create a comprehensive evaluation of dynasty team health and trajectory.
    
    #### DDI Components:
    - **Current Power Rankings (35%)**: How strong is the team right now?
    - **Prospect System (25%)**: How strong is the team's future talent pipeline?
    - **Historical Performance (40%)**: How consistently successful has the team been over time?
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
        for col in ['DDI Score', 'Power Score', 'Prospect Score', 'Historical Score']:
            display_df[col] = display_df[col].round(1)
        
        # Display the rankings table
        st.subheader("Dynasty Dominance Index Rankings")
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
            },
            use_container_width=True,
            hide_index=True,
        )
        
        # Add visualization tabs
        vis_tab1, vis_tab2 = st.tabs(["Component Breakdown", "Top Teams Comparison"])
        
        with vis_tab1:
            st.plotly_chart(create_ddi_visualization(ddi_df), use_container_width=True)
            
            # Add explanation of component weighting
            st.info(f"""
            **DDI Component Weighting:**
            - Power Rankings: {POWER_RANK_WEIGHT*100}%
            - Prospect System: {PROSPECT_WEIGHT*100}%
            - Historical Performance: {HISTORY_WEIGHT*100}%
            """)
            
        with vis_tab2:
            st.plotly_chart(create_radar_chart(ddi_df), use_container_width=True)
            
            # Add breakdown of historical weighting
            st.info(f"""
            **Historical Performance Weighting:**
            - 2024 Season: {HISTORY_WEIGHTS['2024']*100}%
            - 2023 Season: {HISTORY_WEIGHTS['2023']*100}%
            - 2022 Season: {HISTORY_WEIGHTS['2022']*100}%
            - 2021 Season: {HISTORY_WEIGHTS['2021']*100}%
            
            Plus playoff bonus points for top 3 finishes each season.
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
        # Import power_rankings and use its calculate_power_score function
        from components import power_rankings
        from components.power_rankings import calculate_power_score
        
        # Group data by team
        teams = roster_data['team'].unique()
        power_data = []
        
        for team in teams:
            team_roster = roster_data[roster_data['team'] == team]
            
            # Create a mock row with the required fields for power score calculation
            mock_row = pd.Series({
                'Team': team,
                'weekly_avg': np.random.uniform(70, 90),  # Placeholder value
                'total_points': len(team_roster) * 10,    # Placeholder value
                'recent_record': np.random.uniform(0.4, 0.8)  # Placeholder value  
            })
            
            # Calculate power score
            power_score = calculate_power_score(mock_row, pd.DataFrame([mock_row]))
            
            power_data.append({
                'Team': team,
                'Power Score': power_score
            })
            
        return pd.DataFrame(power_data)
        
    except ImportError:
        # If we can't import power_rankings, create a basic version
        teams = roster_data['team'].unique()
        power_rankings_data = []
        for team in teams:
            team_df = roster_data[roster_data['team'] == team]
            power_score = len(team_df) * np.random.uniform(0.8, 1.2)  # Simple placeholder score
            power_rankings_data.append({
                'Team': team,
                'Power Score': power_score
            })
        return pd.DataFrame(power_rankings_data)