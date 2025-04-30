import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
from typing import Dict, List, Any

# Constants for MLB team colors
from components.prospects import MLB_TEAM_COLORS, MLB_TEAM_IDS, MLB_TEAM_ABBR_TO_NAME

def get_contract_score(contract):
    """Score contracts on a scale of 0-1 based on their length/quality"""
    contract_scores = {
        '2050': 1.0, '2045': 0.9, '2040': 0.8, '2035': 0.7, '2029': 0.6,
        '2028': 0.5, '2027': 0.4, '2026': 0.3, '2025': 0.2, '1st': 0.1
    }
    return contract_scores.get(contract, 0.1)

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    if not name or not isinstance(name, str):
        return ""
    normalized = name.lower().strip()
    normalized = re.sub(r'[\(\[].*?[\)\]]', '', normalized)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

def get_player_headshot_html(player_id, player_name):
    """Generate player headshot HTML with a simple approach"""
    try:
        # Default fallback ID for missing headshots
        fallback_id = "805805"
        
        # Simplified player image URL
        player_image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{player_id or fallback_id}/headshot/67/current"
        
        # Create simple HTML for the image
        img_html = f'<img src="{player_image_url}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover;" alt="{player_name} headshot">'
        
        return img_html
    except:
        # Return fallback image if there's any error
        return f'<img src="https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/805805/headshot/67/current" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover;" alt="Default headshot">'

def get_mlb_team_info(team_name):
    """Get team colors and logo URL for an MLB team"""
    # Normalize team name
    team_name_normalized = team_name
    
    # Handle special cases
    if team_name in ["ATH", "OAK", "A's", "Athletics", "Oakland Athletics", "Las Vegas Athletics"]:
        team_name_normalized = "Athletics"
    elif team_name in ["STL", "St. Louis Cardinals", "Cardinals"]:
        team_name_normalized = "Saint Louis Cardinals"
    elif team_name in MLB_TEAM_ABBR_TO_NAME:
        team_name_normalized = MLB_TEAM_ABBR_TO_NAME[team_name]
    
    # Get team colors with normalized name
    team_colors = MLB_TEAM_COLORS.get(team_name_normalized, None)
    
    # Fallback to original name or default colors
    if team_colors is None:
        team_colors = MLB_TEAM_COLORS.get(team_name, {'primary': '#1a1c23', 'secondary': '#2d2f36'})
    
    # Get team ID with normalized name
    team_id = MLB_TEAM_IDS.get(team_name_normalized, '')
    
    # Fallback to original name
    if team_id == '':
        team_id = MLB_TEAM_IDS.get(team_name, '')
    
    # Special case for Athletics
    if team_name_normalized == "Athletics" and team_id == '':
        team_id = MLB_TEAM_IDS.get("Oakland Athletics", '')
    
    # Generate logo URL
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""
    
    return {
        'colors': team_colors,
        'logo_url': logo_url
    }

def get_position_value(position_str, position_counts=None):
    """Calculate a position score based on value and scarcity"""
    # Base positional values
    base_values = {
        'SP': 0.90, 'C': 0.90, 'SS': 0.85, 'CF': 0.80, '2B': 0.75,
        '3B': 0.70, 'RF': 0.65, 'LF': 0.60, '1B': 0.55, 'UT': 0.50, 'RP': 0.40
    }
    
    # Position scarcity bonus
    scarcity_bonus = {
        'C': 0.10, 'SP': 0.05, 'SS': 0.05, 'CF': 0.05, '2B': 0.05,
        '3B': 0.05, 'RF': 0.05, 'LF': 0.05, '1B': 0.05, 'UT': 0.05, 'RP': 0.05
    }
    
    # Calculate position value
    if isinstance(position_str, str):
        positions = position_str.split('/')
        values = []
        for pos in positions:
            pos = pos.strip()
            base_value = base_values.get(pos, 0.4)
            pos_scarcity = scarcity_bonus.get(pos, 0.0)
            values.append(base_value + pos_scarcity)
        return max(values) if values else 0.4
    else:
        return 0.4

def calculate_mvp_score(player_row, weights, norm_columns):
    """Calculate MVP score based on weighted normalized values"""
    score = 0.0
    for component, weight in weights.items():
        if component in norm_columns:
            component_score = norm_columns[component][player_row.name] * weight
            score += component_score
    return score

def render():
    """Render MVP Race page with simplified UI"""
    st.title("MLB Most Valuable Player Race")
    
    st.markdown("""
    The MVP race evaluates player value based on Fantasy Points, Salary, Contract, Age, and Position.
    Players are scored on a 0-100 scale combining these factors with appropriate weighting.
    """)
    
    try:
        # Load player data
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        # Basic data cleaning
        mvp_data = mvp_data.dropna(subset=['Player', 'FPts'])
        
        # Convert numeric columns
        for col in ['FPts', 'FP/G', 'Salary', 'Age']:
            try:
                if col == 'Salary':
                    mvp_data[col] = mvp_data[col].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                mvp_data[col] = pd.to_numeric(mvp_data[col], errors='coerce')
            except Exception as e:
                st.error(f"Error converting {col} column to numeric: {str(e)}")
        
        # Fill missing values
        mvp_data = mvp_data.fillna({
            'FPts': 0, 'FP/G': 0, 'Salary': 0, 'Age': 25,
            'Contract': '1st', 'Position': 'UT', 'Team': 'Unknown'
        })
        
        # Count positions for scarcity calculation
        position_counts = {}
        for pos_str in mvp_data['Position']:
            if isinstance(pos_str, str):
                for pos in pos_str.split('/'):
                    pos = pos.strip()
                    position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Create filter sidebar
        st.sidebar.header("Filter Players")
        
        # Position filter
        all_positions = sorted(list(set([
            pos.strip() 
            for pos_list in mvp_data['Position'].dropna() 
            for pos in pos_list.split('/')
        ])))
        
        selected_positions = st.sidebar.multiselect(
            "Filter by Position",
            all_positions,
            default=[]
        )
        
        # Team filter
        all_teams = sorted(mvp_data['Team'].dropna().unique())
        selected_teams = st.sidebar.multiselect(
            "Filter by Team",
            all_teams,
            default=[]
        )
        
        # Contract filter
        all_contracts = sorted(mvp_data['Contract'].dropna().unique())
        selected_contracts = st.sidebar.multiselect(
            "Filter by Contract",
            all_contracts,
            default=[]
        )
        
        # Filter data based on selections
        filtered_data = mvp_data.copy()
        
        if selected_positions:
            position_mask = filtered_data['Position'].apply(
                lambda x: any(pos.strip() in x for pos in selected_positions) if isinstance(x, str) else False
            )
            filtered_data = filtered_data[position_mask]
        
        if selected_teams:
            filtered_data = filtered_data[filtered_data['Team'].isin(selected_teams)]
        
        if selected_contracts:
            filtered_data = filtered_data[filtered_data['Contract'].isin(selected_contracts)]
        
        # Default weights
        default_weights = {
            'Fantasy Points': 0.50,
            'Salary': 0.20,
            'Contract': 0.10,
            'Age': 0.10,
            'Position': 0.10
        }
        
        # Let user adjust weights with sliders
        st.sidebar.header("MVP Score Weights")
        st.sidebar.write("Adjust the weights of different components in the MVP calculation:")
        
        weights = {}
        for component, default_weight in default_weights.items():
            weights[component] = st.sidebar.slider(
                f"{component} Weight",
                0.0, 1.0, default_weight, 0.01
            )
        
        # Normalize weights to sum to 1
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            weights = {k: v/weight_sum for k, v in weights.items()}
        
        # Calculate normalized values for each component
        norm_columns = {}
        
        if len(filtered_data) > 0:
            # Fantasy Points (higher is better)
            max_fpts = filtered_data['FPts'].max()
            min_fpts = filtered_data['FPts'].min()
            norm_columns['Fantasy Points'] = filtered_data['FPts'].apply(
                lambda x: (x - min_fpts) / (max_fpts - min_fpts) if max_fpts != min_fpts else 1.0
            )
        
            # Salary (lower is better)
            max_salary = filtered_data['Salary'].max()
            min_salary = filtered_data['Salary'].min()
            norm_columns['Salary'] = filtered_data['Salary'].apply(
                lambda x: 1 - ((x - min_salary) / (max_salary - min_salary)) if max_salary != min_salary else 1.0
            )
            
            # Age (optimum is 24-27)
            norm_columns['Age'] = filtered_data['Age'].apply(
                lambda age: 1.0 if 24 <= age <= 27 else
                           0.8 if 28 <= age <= 29 else
                           0.6 if 30 <= age <= 31 else
                           0.4 if 32 <= age <= 33 else
                           0.2 if 34 <= age <= 35 else 0.1
            )
            
            # Contract (longer is better)
            norm_columns['Contract'] = filtered_data['Contract'].apply(get_contract_score)
            
            # Position value
            norm_columns['Position'] = filtered_data['Position'].apply(
                lambda x: get_position_value(x, position_counts)
            )
            
            # Calculate MVP scores
            mvp_scores = []
            for _, row in filtered_data.iterrows():
                score = calculate_mvp_score(row, weights, norm_columns)
                mvp_scores.append(score)
            
            filtered_data['MVP_Score'] = mvp_scores
            
            # Sort by MVP score in descending order
            filtered_data = filtered_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
            
            # Top 3 MVP candidates with special highlighting
            st.write("## Current MVP Favorites")
            
            # Display top 3 in a row
            cols = st.columns(3)
            
            for i, (_, player) in enumerate(filtered_data.head(3).iterrows()):
                with cols[i]:
                    # Get team colors
                    team_info = get_mlb_team_info(player['Team'])
                    colors = team_info['colors']
                    
                    # Calculate stars and MVP score
                    stars = min(5, max(1, int(player['MVP_Score'] * 5 + 0.5)))
                    stars_display = "⭐" * stars
                    mvp_score_display = int(player['MVP_Score'] * 100)
                    
                    # Create a simple colored box
                    st.markdown(
                        f"""
                        <div style="background: {colors['primary']}; 
                                    padding: 10px; 
                                    border-radius: 10px; 
                                    text-align: center;">
                            <h3 style="color: white; margin: 0;">#{i+1}</h3>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Display player headshot
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin: 10px 0;">
                            {get_player_headshot_html(player['ID'], player['Player'])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Player name and info
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin-bottom: 10px;">
                            <h4 style="margin: 5px 0;">{player['Player']}</h4>
                            <p style="opacity: 0.8; margin: 0;">{player['Position']} | {player['Team']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Star rating
                    st.markdown(f"<p style='text-align: center; color: gold;'>{stars_display}</p>", unsafe_allow_html=True)
                    
                    # MVP score
                    st.markdown(f"<p style='text-align: center;'><b>MVP Score:</b> {mvp_score_display}</p>", unsafe_allow_html=True)
                    st.progress(player['MVP_Score'])
                    
                    # Stats using Streamlit's native components
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("FPts", f"{player['FPts']:.1f}")
                    with col2:
                        st.metric("Age", f"{player['Age']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Salary", f"${player['Salary']}")
                    with col2:
                        st.metric("FP/G", f"{player['FP/G']:.1f}")
                    
                    st.info(f"Contract: {player['Contract']}")
            
            # MVP Race Complete Rankings Table
            st.write("## Complete MVP Rankings")
            
            # Create tabs for different views of the data
            tab1, tab2, tab3 = st.tabs(["Player Cards", "Performance Analysis", "Rankings Table"])
            
            with tab1:
                # Player cards in a scrollable list
                st.write("### Player Rankings")
                
                # Filter option for number of players to display
                display_count = st.slider("Number of players to display", 10, 100, 30, 5)
                display_data = filtered_data.head(display_count)
                
                # Use a container for better mobile display
                for i, (_, player) in enumerate(display_data.iterrows()):
                    rank = i + 1
                    team_info = get_mlb_team_info(player['Team'])
                    colors = team_info['colors']
                    
                    # Calculate score values
                    mvp_score_pct = min(100, int(player['MVP_Score'] * 100))
                    stars = min(5, max(1, int(player['MVP_Score'] * 5 + 0.5)))
                    stars_display = "⭐" * stars
                    
                    # Create a simple container with player info
                    col1, col2 = st.columns([0.15, 0.85])
                    
                    with col1:
                        # Rank number
                        st.markdown(f"<h3 style='text-align:center;'>#{rank}</h3>", unsafe_allow_html=True)
                        # Small headshot
                        st.markdown(f"<div style='text-align:center;'>{get_player_headshot_html(player['ID'], player['Player']).replace('width: 80px;', 'width: 60px;').replace('height: 80px;', 'height: 60px;')}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        # Create a colored box with player info
                        st.markdown(
                            f"""
                            <div style="background: linear-gradient(90deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                                       padding: 10px; border-radius: 8px; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>
                                        <h4 style="color: white; margin: 0;">{player['Player']}</h4>
                                        <p style="color: rgba(255,255,255,0.8); margin: 0;">{player['Position']} | {player['Team']}</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="color: gold; margin: 0;">{stars_display}</p>
                                        <p style="color: white; font-weight: bold; margin: 0;">MVP: {mvp_score_pct}</p>
                                    </div>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                                    <div style="color: white;">FPts: {player['FPts']:.1f}</div>
                                    <div style="color: white;">Age: {player['Age']}</div>
                                    <div style="color: white;">Salary: ${player['Salary']}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    # Add a separator
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
            
            with tab2:
                # Performance analysis charts
                st.write("### MVP Candidates Performance Breakdown")
                
                # Allow user to select players to compare
                selected_players = st.multiselect(
                    "Select Players to Compare",
                    filtered_data['Player'].tolist(),
                    default=filtered_data['Player'].head(5).tolist()
                )
                
                if selected_players:
                    # Get selected players data
                    selected_data = filtered_data[filtered_data['Player'].isin(selected_players)]
                    
                    # Create radar chart
                    categories = list(weights.keys())
                    
                    fig = go.Figure()
                    
                    for _, player in selected_data.iterrows():
                        # Get normalized values for each category
                        values = []
                        for cat in categories:
                            if cat in norm_columns:
                                values.append(norm_columns[cat][player.name])
                        
                        # Add player to radar chart
                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=f"{player['Player']} ({player['Team']})",
                            hovertemplate="%{theta}: %{r:.2f}<extra></extra>"
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        showlegend=True,
                        height=600,
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Please select at least one player to display the radar chart.")
            
            with tab3:
                # Table view of player data (sortable)
                st.write("### Complete MVP Data Table")
                
                # Display full data with MVP score
                display_cols = ['Player', 'Team', 'Position', 'FPts', 'FP/G', 'Age', 'Salary', 'Contract', 'MVP_Score']
                
                # Format the MVP Score column to show as percentage
                display_data = filtered_data[display_cols].copy()
                display_data['MVP_Score'] = (display_data['MVP_Score'] * 100).round(1).astype(str) + '%'
                
                # Allow sorting by any column
                st.dataframe(display_data)
        else:
            st.error("No data available after filtering. Please adjust your filters.")
    
    except Exception as e:
        st.error(f"Error loading or processing MVP data: {str(e)}")
        st.error("Please check if 'attached_assets/MVP-Player-List.csv' exists and is properly formatted.")

if __name__ == "__main__":
    render()