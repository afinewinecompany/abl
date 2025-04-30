import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import numpy as np
import re

# Constants for MLB team colors
from components.power_rankings import MLB_TEAM_COLORS, MLB_TEAM_IDS

def normalize_value(value, min_val, max_val, reverse=False):
    """
    Normalize a value to a 0-1 scale
    If reverse=True, smaller values are better (e.g., age, salary)
    """
    if max_val == min_val:
        return 1.0
    
    if reverse:
        # For metrics where lower is better
        return 1 - ((value - min_val) / (max_val - min_val))
    else:
        # For metrics where higher is better
        return (value - min_val) / (max_val - min_val)

def get_contract_score(contract):
    """
    Score contracts on a scale of 0-1 based on their length/quality
    Contract types in order of best to worst: 2050, 2045, 2040, 2035, 2029, 2028, 2027, 2026, 2025, 1st
    """
    contract_scores = {
        '2050': 1.0,
        '2045': 0.9,
        '2040': 0.8,
        '2035': 0.7,
        '2029': 0.6,
        '2028': 0.5,
        '2027': 0.4,
        '2026': 0.3,
        '2025': 0.2,
        '1st': 0.1
    }
    
    return contract_scores.get(contract, 0.1)  # Default to lowest if not found

def get_player_headshot_url(player_id):
    """
    Generate player headshot URL based on the Fantrax ID
    """
    # Clean player ID to remove asterisks
    clean_id = player_id.replace('*', '')
    return f"https://images.fantrax.com/headshots/{clean_id}.jpg"

def get_mlb_team_info(team_name):
    """
    Get team colors and logo URL for an MLB team
    """
    team_colors = MLB_TEAM_COLORS.get(team_name, {'primary': '#1a1c23', 'secondary': '#2d2f36'})
    team_id = MLB_TEAM_IDS.get(team_name, '')
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""
    
    return {
        'colors': team_colors,
        'logo_url': logo_url
    }

def calculate_mvp_score(player_row, weights, norm_columns):
    """
    Calculate MVP score based on the weighted normalized values
    """
    score = 0
    for col, weight in weights.items():
        if col in norm_columns:
            score += norm_columns[col][player_row.name] * weight
    
    return score

def render():
    """Render the MVP Race page"""
    st.title("🏆 MVP Race Tracker")
    
    st.write("""
    ## American Baseball League Most Valuable Player
    
    This tool analyzes player performance, value, and impact to determine the MVP race leaders.
    Each player is evaluated based on their performance (FPts, FP/G) alongside their contract value (age, salary, contract length).
    """)
    
    # Load the MVP player list
    try:
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        # Convert columns to appropriate data types
        mvp_data['Age'] = pd.to_numeric(mvp_data['Age'], errors='coerce')
        mvp_data['Salary'] = pd.to_numeric(mvp_data['Salary'], errors='coerce')
        mvp_data['FPts'] = pd.to_numeric(mvp_data['FPts'], errors='coerce')
        mvp_data['FP/G'] = pd.to_numeric(mvp_data['FP/G'], errors='coerce')
        
        # Create player name field and IDs
        mvp_data['ID'] = mvp_data['ID'].astype(str)
        mvp_data['Player_Name'] = mvp_data['Player']
        
        # Fill missing values with sensible defaults
        mvp_data = mvp_data.fillna({
            'Age': mvp_data['Age'].mean(),
            'Salary': mvp_data['Salary'].mean(),
            'Contract': '1st',
            'FPts': 0,
            'FP/G': 0
        })
        
        # Define weights for MVP criteria (sum should be 1.0)
        default_weights = {
            'FPts': 0.35,
            'FP/G': 0.25,
            'Salary': 0.20,
            'Contract': 0.10,
            'Age': 0.10
        }
        
        # Allow user to adjust weights
        st.sidebar.header("MVP Calculation Settings")
        
        custom_weights = {}
        use_custom_weights = st.sidebar.checkbox("Customize MVP Criteria Weights", value=False)
        
        if use_custom_weights:
            st.sidebar.write("Adjust the importance of each factor (should sum to 100%):")
            total = 0
            
            for factor, default in default_weights.items():
                weight = st.sidebar.slider(
                    f"{factor} Weight", 
                    min_value=0, 
                    max_value=100, 
                    value=int(default * 100),
                    step=5
                )
                custom_weights[factor] = weight / 100
                total += weight
            
            # Show warning if weights don't sum to 100%
            if total != 100:
                st.sidebar.warning(f"Weights sum to {total}%, not 100%. Results may be skewed.")
            
            weights = custom_weights
        else:
            weights = default_weights
        
        # Filter options
        st.sidebar.header("Filter Options")
        
        # Filter by position
        all_positions = []
        for pos_list in mvp_data['Position'].str.split(','):
            all_positions.extend([p.strip() for p in pos_list])
        unique_positions = sorted(list(set(all_positions)))
        
        selected_position = st.sidebar.selectbox(
            "Filter by Position",
            ["All Positions"] + unique_positions
        )
        
        # Filter by team
        teams = sorted(mvp_data['Team'].unique())
        selected_team = st.sidebar.selectbox(
            "Filter by Team",
            ["All Teams"] + teams
        )
        
        # Calculate normalized values for each metric
        norm_columns = {}
        
        # For metrics where higher is better (FPts, FP/G)
        for col in ['FPts', 'FP/G']:
            min_val = mvp_data[col].min()
            max_val = mvp_data[col].max()
            norm_columns[col] = mvp_data[col].apply(lambda x: normalize_value(x, min_val, max_val, reverse=False))
        
        # For metrics where lower is better (Age, Salary)
        for col in ['Age', 'Salary']:
            min_val = mvp_data[col].min()
            max_val = mvp_data[col].max()
            norm_columns[col] = mvp_data[col].apply(lambda x: normalize_value(x, min_val, max_val, reverse=True))
        
        # For Contract (special case with predefined values)
        norm_columns['Contract'] = mvp_data['Contract'].apply(get_contract_score)
        
        # Apply filters if selected
        filtered_data = mvp_data.copy()
        
        if selected_position != "All Positions":
            # Filter by position (check if the selected position is in the comma-separated list)
            filtered_data = filtered_data[filtered_data['Position'].str.contains(selected_position)]
            
        if selected_team != "All Teams":
            # Filter by team
            filtered_data = filtered_data[filtered_data['Team'] == selected_team]
        
        # Calculate MVP score for each player
        mvp_scores = []
        
        for idx, row in filtered_data.iterrows():
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
                team_info = get_mlb_team_info(player['Team'])
                colors = team_info['colors']
                logo_url = team_info['logo_url']
                
                # Calculate stars based on MVP score (1-5 stars)
                stars = min(5, max(1, int(player['MVP_Score'] * 5 + 0.5)))
                stars_display = "⭐" * stars
                
                # Display player card
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                    border-radius: 10px;
                    padding: 1rem;
                    position: relative;
                    overflow: hidden;
                    height: 360px;
                ">
                    <div style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.1); padding: 5px; border-radius: 5px;">
                        <span style="color: white; font-size: 0.8rem;">#{i+1}</span>
                    </div>
                    <div style="position: absolute; top: 10px; left: 10px; opacity: 0.2;">
                        <img src="{logo_url}" style="width: 80px; height: 80px;" alt="Team Logo">
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 0.5rem;">
                        <img src="{get_player_headshot_url(player['ID'])}" style="width: 120px; height: 120px; border-radius: 50%; border: 3px solid white; object-fit: cover;" alt="{player['Player']}">
                        <h3 style="color: white; margin: 0.5rem 0; text-align: center;">{player['Player']}</h3>
                        <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.3rem;">{player['Position']} | {player['Team']}</div>
                        <div style="margin: 0.5rem 0; color: gold; font-size: 1.2rem;">{stars_display}</div>
                        <div style="
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 0.5rem;
                            width: 100%;
                            margin-top: 0.5rem;
                        ">
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">FPts</div>
                                <div style="color: white; font-weight: bold;">{player['FPts']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">FP/G</div>
                                <div style="color: white; font-weight: bold;">{player['FP/G']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">Age</div>
                                <div style="color: white; font-weight: bold;">{player['Age']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">Salary</div>
                                <div style="color: white; font-weight: bold;">$M{player['Salary']}</div>
                            </div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center; width: 100%; margin-top: 0.5rem;">
                            <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">Contract</div>
                            <div style="color: white; font-weight: bold;">{player['Contract']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # MVP Race Complete Rankings Table
        st.write("## Complete MVP Rankings")
        
        # Create two tabs for table view and radar chart view
        tab1, tab2, tab3 = st.tabs(["Table View", "Visual Breakdown", "Value Analysis"])
        
        with tab1:
            # Enhanced table with styling
            display_columns = ['Player', 'Position', 'Team', 'Age', 'Salary', 'Contract', 'FPts', 'FP/G', 'MVP_Score']
            
            # Format the MVP score for display
            display_df = filtered_data[display_columns].copy()
            display_df['MVP_Score'] = (display_df['MVP_Score'] * 100).round(1)
            
            # Add a rank column
            display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
            
            # Rename columns for better display
            display_df = display_df.rename(columns={
                'MVP_Score': 'MVP Score'
            })
            
            st.dataframe(
                display_df,
                column_config={
                    "Rank": st.column_config.NumberColumn(format="%d"),
                    "MVP Score": st.column_config.ProgressColumn(
                        "MVP Score",
                        help="MVP score out of 100",
                        format="%d",
                        min_value=0,
                        max_value=100
                    ),
                    "FPts": st.column_config.NumberColumn(format="%.1f"),
                    "FP/G": st.column_config.NumberColumn(format="%.2f"),
                    "Salary": st.column_config.NumberColumn(format="$%dM"),
                },
                hide_index=True,
                use_container_width=True
            )
        
        with tab2:
            # Radar chart for performance breakdown
            st.write("### MVP Candidates Performance Breakdown")
            
            # Allow user to select players to compare
            num_display = min(10, len(filtered_data))
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
                    legend=dict(
                        yanchor="top",
                        y=1.1,
                        xanchor="left",
                        x=0
                    ),
                    height=600,
                    template="plotly_dark",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Please select at least one player to display the radar chart.")
            
            # Bar chart showing breakdown of MVP score components
            st.write("### MVP Score Component Breakdown")
            
            top_players = filtered_data.head(10) if not selected_players else filtered_data[filtered_data['Player'].isin(selected_players)]
            
            # Create a DataFrame for the breakdown
            breakdown_data = []
            
            for _, player in top_players.iterrows():
                for component, weight in weights.items():
                    if component in norm_columns:
                        score_contribution = norm_columns[component][player.name] * weight
                        breakdown_data.append({
                            'Player': player['Player'],
                            'Team': player['Team'],
                            'Component': component,
                            'Value': score_contribution,
                            'Total MVP Score': player['MVP_Score']
                        })
            
            breakdown_df = pd.DataFrame(breakdown_data)
            
            # Create stacked bar chart
            fig = px.bar(
                breakdown_df,
                x='Player',
                y='Value',
                color='Component',
                title='MVP Score Breakdown by Component',
                hover_data=['Team'],
                height=500,
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            
            # Sort bars by total MVP score
            fig.update_layout(
                xaxis={'categoryorder': 'array', 'categoryarray': top_players.sort_values('MVP_Score', ascending=False)['Player'].tolist()},
                template="plotly_dark",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Scatter plot showing value analysis
            st.write("### Value vs Performance Analysis")
            
            # Create a plot comparing FPts vs Salary with point size as Age
            fig = px.scatter(
                filtered_data.head(50),
                x='Salary',
                y='FPts',
                size='Age',
                color='FP/G',
                hover_name='Player',
                hover_data=['Team', 'Position', 'Contract'],
                title='Performance vs Cost Analysis (Top 50 MVP Candidates)',
                labels={
                    'Salary': 'Salary ($M)',
                    'FPts': 'Fantasy Points',
                    'FP/G': 'Fantasy Points per Game',
                    'Age': 'Age'
                },
                color_continuous_scale='viridis',
                template="plotly_dark",
                size_max=20,
                height=700
            )
            
            # Add quadrant lines
            avg_salary = filtered_data.head(50)['Salary'].mean()
            avg_fpts = filtered_data.head(50)['FPts'].mean()
            
            fig.add_shape(
                type='line',
                x0=avg_salary,
                y0=0,
                x1=avg_salary,
                y1=filtered_data['FPts'].max() * 1.1,
                line=dict(color='rgba(255,255,255,0.5)', width=1, dash='dash')
            )
            
            fig.add_shape(
                type='line',
                x0=0,
                y0=avg_fpts,
                x1=filtered_data['Salary'].max() * 1.1,
                y1=avg_fpts,
                line=dict(color='rgba(255,255,255,0.5)', width=1, dash='dash')
            )
            
            # Add quadrant labels
            fig.add_annotation(
                x=avg_salary/2,
                y=avg_fpts*1.5,
                text="HIGH VALUE<br>(High Performance/Low Cost)",
                showarrow=False,
                font=dict(size=12, color="lightgreen")
            )
            
            fig.add_annotation(
                x=avg_salary*1.5,
                y=avg_fpts*1.5,
                text="STAR PLAYERS<br>(High Performance/High Cost)",
                showarrow=False,
                font=dict(size=12, color="gold")
            )
            
            fig.add_annotation(
                x=avg_salary/2,
                y=avg_fpts/2,
                text="LOW IMPACT<br>(Low Performance/Low Cost)",
                showarrow=False,
                font=dict(size=12, color="lightgray")
            )
            
            fig.add_annotation(
                x=avg_salary*1.5,
                y=avg_fpts/2,
                text="OVERVALUED<br>(Low Performance/High Cost)",
                showarrow=False,
                font=dict(size=12, color="tomato")
            )
            
            # Update layout
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add explanation
            st.markdown("""
            ### Understanding the Value Analysis:
            
            - **High Value Players**: Players with high performance but relatively low cost (upper left quadrant)
            - **Star Players**: Players with high performance and corresponding high cost (upper right quadrant)
            - **Low Impact Players**: Players with lower performance and lower cost (lower left quadrant)
            - **Overvalued Players**: Players with high cost but lower performance (lower right quadrant)
            
            Bubble size represents the player's age - larger bubbles are older players.
            Color intensity shows fantasy points per game - brighter colors indicate higher FP/G.
            """)
        
    except Exception as e:
        st.error(f"Error loading or processing MVP data: {str(e)}")