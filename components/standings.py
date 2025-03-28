import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import json
import os

def load_division_data() -> pd.DataFrame:
    """Load division data from the CSV file"""
    try:
        divisions_path = os.path.join("attached_assets", "divisions.csv")
        if os.path.exists(divisions_path):
            divisions_df = pd.read_csv(divisions_path, header=None, names=["division", "team"])
            return divisions_df
        else:
            return pd.DataFrame(columns=["division", "team"])
    except Exception as e:
        st.error(f"Error loading division data: {str(e)}")
        return pd.DataFrame(columns=["division", "team"])

def add_division_info(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Add division information to the standings DataFrame"""
    try:
        # Load division data
        division_df = load_division_data()
        if division_df.empty:
            return standings_df
            
        # Make a copy of the standings DataFrame to avoid modifying the original
        enhanced_df = standings_df.copy()
        
        # Add 'division' column with a default value
        enhanced_df['division'] = 'Unknown'
        
        # Loop through each team and assign the division
        for index, row in enhanced_df.iterrows():
            team_name = row['team'] if 'team' in row else (row['team_name'] if 'team_name' in row else None)
            if team_name:
                # Find the division for this team
                matching_divisions = division_df[division_df['team'] == team_name]
                if not matching_divisions.empty:
                    enhanced_df.at[index, 'division'] = matching_divisions.iloc[0]['division']
        
        return enhanced_df
    except Exception as e:
        st.error(f"Error adding division info: {str(e)}")
        return standings_df

def render(standings_data: pd.DataFrame):
    """Render enhanced standings section with detailed analytics"""
    st.title("League Standings")

    # Debug section
    with st.expander("Standings Data Analysis", expanded=False):
        st.write("Raw Standings Data Schema:")
        
        if standings_data.empty:
            st.error("No standings data available")
        else:
            st.write(f"Columns available: {list(standings_data.columns)}")
            st.write(f"Number of teams: {len(standings_data)}")
            
            # Show sample data
            st.write("First row sample:")
            st.write(standings_data.iloc[0].to_dict())
            
            # Check for specific key columns
            expected_columns = ['team', 'team_id', 'rank', 'wins', 'losses', 'ties', 
                             'win_percentage', 'points_for', 'points_against', 'games_back', 'streak']
            
            for col in expected_columns:
                if col in standings_data.columns:
                    st.success(f"✓ Found column: {col}")
                else:
                    st.warning(f"✗ Missing column: {col}")

    if standings_data.empty:
        st.warning("No standings data available. Please check the API connection.")
        return

    # Make sure 'team' column exists
    if 'team_name' in standings_data.columns and 'team' not in standings_data.columns:
        standings_data = standings_data.rename(columns={'team_name': 'team'})
    
    # Add division information
    standings_data = add_division_info(standings_data)
    
    # Sort standings by rank
    standings_data = standings_data.sort_values('rank')

    # Create tabs for different views
    standings_tab, analytics_tab, comparison_tab = st.tabs(["Standings Table", "Team Analytics", "Division Comparison"])

    with standings_tab:
        # Enhanced standings display with custom styling
        st.subheader("Current Standings")
        
        # Determine column for displaying win/loss/tie record
        has_winpct = 'win_percentage' in standings_data.columns

        # Create formatted record column
        if all(col in standings_data.columns for col in ['wins', 'losses', 'ties']):
            standings_data['record'] = standings_data.apply(
                lambda x: f"{int(x['wins'])}-{int(x['losses'])}{f'-{int(x.ties)}' if x['ties'] > 0 else ''}",
                axis=1
            )
        
        # Apply conditional formatting
        standings_data_styled = standings_data.copy()
        
        # Format team names with rank
        display_columns = {
            "rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
            "team": "Team",
            "record": "Record (W-L-T)",
        }
        
        # Add win percentage if available
        if has_winpct:
            display_columns["win_percentage"] = st.column_config.NumberColumn("Win %", format="%.3f")
        
        # Add points data if available
        if 'points_for' in standings_data.columns:
            display_columns["points_for"] = st.column_config.NumberColumn("PF", format="%.1f", help="Points For")
        
        if 'points_against' in standings_data.columns:
            display_columns["points_against"] = st.column_config.NumberColumn("PA", format="%.1f", help="Points Against")
        
        # Add streak if available
        if 'streak' in standings_data.columns:
            display_columns["streak"] = "Streak"
            
        # Add games back if available
        if 'games_back' in standings_data.columns:
            display_columns["games_back"] = st.column_config.NumberColumn("GB", format="%.1f", help="Games Back")

        # Option to view standings by division or overall
        view_option = st.radio(
            "View Standings By:",
            ["Overall", "Division"],
            horizontal=True
        )
        
        if view_option == "Overall":
            # Display the overall standings table
            st.dataframe(
                standings_data_styled,
                column_config=display_columns,
                hide_index=True
            )
        else:  # Division view
            if 'division' in standings_data.columns and not all(standings_data['division'] == 'Unknown'):
                # Create two columns per row
                col1, col2 = st.columns(2)
                
                # Get unique divisions and sort them
                divisions = sorted(standings_data['division'].unique())
                
                # Display division standings side by side
                for i, division in enumerate(divisions):
                    # Select which column to use
                    column = col1 if i % 2 == 0 else col2
                    
                    with column:
                        st.subheader(division)
                        division_data = standings_data_styled[standings_data_styled['division'] == division].sort_values(
                            'win_percentage' if 'win_percentage' in standings_data.columns else 'rank', 
                            ascending=False
                        )
                        st.dataframe(
                            division_data,
                            column_config=display_columns,
                            hide_index=True
                        )
            else:
                st.info("Division data is available but not all teams have been assigned to a division. Check the divisions.csv file.")
                st.dataframe(
                    standings_data_styled,
                    column_config=display_columns,
                    hide_index=True
                )

    with analytics_tab:
        # Create subtabs for different analysis views
        record_tab, points_tab, division_tab = st.tabs(["Win-Loss Records", "Points Analysis", "Division Analysis"])
        
        with record_tab:
            # Win-Loss Record Visualization
            st.subheader("Win-Loss-Tie Records")
            
            # Prepare data for visualization
            if all(col in standings_data.columns for col in ['wins', 'losses', 'ties']):
                # Option to group by division
                if 'division' in standings_data.columns and not all(standings_data['division'] == 'Unknown'):
                    group_by_division = st.checkbox("Group by Division", value=True)
                else:
                    group_by_division = False
                
                win_loss_data = standings_data.melt(
                    id_vars=['team', 'division'] if group_by_division and 'division' in standings_data.columns else ['team'],
                    value_vars=['wins', 'losses', 'ties'],
                    var_name='record_type',
                    value_name='count'
                )
                
                # Create color mapping for record types
                color_map = {'wins': '#2ecc71', 'losses': '#e74c3c', 'ties': '#f39c12'}
                
                # Create the figure with or without division grouping
                if group_by_division and 'division' in standings_data.columns:
                    # Sort by division and win percentage within division
                    win_loss_data = win_loss_data.merge(
                        standings_data[['team', 'win_percentage']],
                        on='team',
                        how='left'
                    )
                    
                    # Create a composite sort key: division, then record_type, then win_percentage
                    win_loss_data['sort_key'] = win_loss_data.apply(
                        lambda x: (x['division'], 
                                  0 if x['record_type'] == 'wins' else (1 if x['record_type'] == 'losses' else 2), 
                                  -x['win_percentage']), 
                        axis=1
                    )
                    
                    # Sort the dataframe
                    win_loss_data = win_loss_data.sort_values('sort_key')
                    
                    fig = px.bar(
                        win_loss_data,
                        x='team',
                        y='count',
                        color='record_type',
                        facet_row='division',
                        color_discrete_map=color_map,
                        title='Team Win-Loss-Tie Distribution by Division',
                        barmode='stack',
                        labels={'team': 'Team', 'count': 'Games', 'record_type': 'Result', 'division': 'Division'},
                        category_orders={'team': list(win_loss_data.sort_values(['division', 'win_percentage'], ascending=[True, False])['team'].unique())}
                    )
                    
                    # Adjust subplot titles
                    for i, division in enumerate(sorted(win_loss_data['division'].unique())):
                        fig.layout.annotations[i].text = division
                        
                    fig.update_layout(height=800)  # Make it taller for multiple divisions
                else:
                    # Sort by win percentage
                    sorted_teams = standings_data.sort_values('win_percentage', ascending=False)['team'].tolist()
                    
                    fig = px.bar(
                        win_loss_data,
                        x='team',
                        y='count',
                        color='record_type',
                        color_discrete_map=color_map,
                        title='Team Win-Loss-Tie Distribution',
                        barmode='stack',
                        labels={'team': 'Team', 'count': 'Games', 'record_type': 'Result'},
                        category_orders={'team': sorted_teams}
                    )
                    
                    fig.update_layout(height=500)
                
                # Customize figure appearance
                fig.update_layout(
                    xaxis_tickangle=-45,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        title=None
                    ),
                    margin=dict(t=80, b=100),
                )
                
                # Update series names to be more user-friendly
                fig.for_each_trace(lambda t: t.update(name=t.name.capitalize() if t.name in ['wins', 'losses', 'ties'] else t.name))
                
                st.plotly_chart(fig, use_container_width=True)
        
        with points_tab:
            # Points Analysis if available
            if all(col in standings_data.columns for col in ['points_for', 'points_against']):
                st.subheader("Points Analysis")
                
                # Calculate point differential
                standings_data['point_diff'] = standings_data['points_for'] - standings_data['points_against']
                
                # Create scatter plot for points
                fig2 = px.scatter(
                    standings_data.sort_values('point_diff', ascending=False),
                    x='points_for',
                    y='points_against',
                    color='point_diff',
                    size='wins',
                    hover_name='team',
                    color_continuous_scale='RdBu_r',  # Red for high (positive diff), blue for low (negative diff)
                    title='Points For vs Points Against',
                    labels={
                        'points_for': 'Points For',
                        'points_against': 'Points Against',
                        'point_diff': 'Point Differential',
                        'wins': 'Wins'
                    }
                )
                
                # Add diagonal line for equal points for/against
                diagonal_values = [
                    min(standings_data['points_for'].min(), standings_data['points_against'].min()),
                    max(standings_data['points_for'].max(), standings_data['points_against'].max())
                ]
                
                fig2.add_trace(
                    go.Scatter(
                        x=diagonal_values,
                        y=diagonal_values,
                        mode='lines',
                        line=dict(color='rgba(0,0,0,0.3)', dash='dash'),
                        name='Equal PF/PA'
                    )
                )
                
                # Add annotations for team names
                for i, row in standings_data.iterrows():
                    fig2.add_annotation(
                        x=row['points_for'],
                        y=row['points_against'],
                        text=row['team'],
                        showarrow=False,
                        font=dict(size=10),
                        bgcolor="rgba(255, 255, 255, 0.7)",
                        bordercolor="rgba(0, 0, 0, 0.3)",
                        borderwidth=1,
                        borderpad=3,
                        yshift=10
                    )
                
                fig2.update_layout(height=600)
                st.plotly_chart(fig2, use_container_width=True)
                
                # Add a bar chart for point differential
                st.subheader("Point Differential by Team")
                
                # Sort teams by point differential
                sorted_diff_data = standings_data.sort_values('point_diff', ascending=False)
                
                # Color for bars based on point differential (positive = green, negative = red)
                colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in sorted_diff_data['point_diff']]
                
                fig3 = go.Figure([
                    go.Bar(
                        x=sorted_diff_data['team'],
                        y=sorted_diff_data['point_diff'],
                        marker_color=colors
                    )
                ])
                
                fig3.update_layout(
                    title='Team Point Differential (Points For - Points Against)',
                    xaxis_tickangle=-45,
                    height=500,
                    yaxis_title='Point Differential',
                    xaxis_title='Team'
                )
                
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Points data not available in the current standings information.")
        
        with division_tab:
            # Division Analysis if available
            if 'division' in standings_data.columns and not all(standings_data['division'] == 'Unknown'):
                st.subheader("Division Performance Analysis")
                
                # Calculate division performance metrics
                division_stats = standings_data.groupby('division').agg({
                    'wins': 'sum',
                    'losses': 'sum',
                    'ties': 'sum',
                    'win_percentage': 'mean',
                    'points_for': 'mean',
                    'points_against': 'mean',
                    'team': 'count'
                }).reset_index()
                
                division_stats = division_stats.rename(columns={
                    'win_percentage': 'avg_win_pct',
                    'points_for': 'avg_points_for',
                    'points_against': 'avg_points_against',
                    'team': 'teams'
                })
                
                division_stats['win_loss_ratio'] = division_stats.apply(
                    lambda x: round(x['wins'] / x['losses'], 2) if x['losses'] > 0 else x['wins'],
                    axis=1
                )
                
                # Display division stats
                st.subheader("Division Statistics")
                st.dataframe(
                    division_stats,
                    column_config={
                        "division": "Division",
                        "wins": st.column_config.NumberColumn("Wins", format="%d"),
                        "losses": st.column_config.NumberColumn("Losses", format="%d"),
                        "ties": st.column_config.NumberColumn("Ties", format="%d"),
                        "avg_win_pct": st.column_config.NumberColumn("Avg Win %", format="%.3f"),
                        "avg_points_for": st.column_config.NumberColumn("Avg PF", format="%.1f"),
                        "avg_points_against": st.column_config.NumberColumn("Avg PA", format="%.1f"),
                        "win_loss_ratio": st.column_config.NumberColumn("W/L Ratio", format="%.2f"),
                        "teams": st.column_config.NumberColumn("Teams", format="%d")
                    },
                    hide_index=True
                )
                
                # Create comparison visualizations
                metric_selector = st.selectbox(
                    "Select Metric for Comparison:",
                    options=[
                        "avg_win_pct", "avg_points_for", "avg_points_against", 
                        "wins", "losses", "win_loss_ratio"
                    ],
                    format_func=lambda x: {
                        "avg_win_pct": "Average Win Percentage",
                        "avg_points_for": "Average Points For", 
                        "avg_points_against": "Average Points Against",
                        "wins": "Total Wins",
                        "losses": "Total Losses",
                        "win_loss_ratio": "Win/Loss Ratio"
                    }[x]
                )
                
                # Create color scale based on selected metric
                color_scale = 'RdBu_r'  # Default
                if metric_selector in ['avg_win_pct', 'avg_points_for', 'wins', 'win_loss_ratio']:
                    color_scale = 'RdBu_r'  # Red (high) to Blue (low)
                elif metric_selector in ['avg_points_against', 'losses']:
                    color_scale = 'BuRd_r'  # Blue (low) to Red (high)
                
                # Sort divisions by the selected metric
                sort_ascending = metric_selector in ['avg_points_against', 'losses']
                sorted_divisions = division_stats.sort_values(metric_selector, ascending=sort_ascending)['division'].tolist()
                
                # Create bar chart
                fig4 = px.bar(
                    division_stats.sort_values(metric_selector, ascending=sort_ascending),
                    x='division',
                    y=metric_selector,
                    color=metric_selector,
                    color_continuous_scale=color_scale,
                    title=f'Division Comparison by {metric_selector.replace("_", " ").title()}',
                    labels={
                        'division': 'Division',
                        metric_selector: metric_selector.replace('_', ' ').title()
                    },
                    category_orders={'division': sorted_divisions}
                )
                
                st.plotly_chart(fig4, use_container_width=True)
                
                # Create division radar chart
                st.subheader("Division Strength Comparison")
                
                # Prepare data for radar chart
                radar_metrics = ['avg_win_pct', 'avg_points_for', 'win_loss_ratio']
                radar_df = division_stats.copy()
                
                # Normalize values to 0-1 scale for radar chart
                for metric in radar_metrics:
                    if radar_df[metric].max() != radar_df[metric].min():
                        radar_df[metric] = (radar_df[metric] - radar_df[metric].min()) / (radar_df[metric].max() - radar_df[metric].min())
                    else:
                        radar_df[metric] = 0.5
                
                # For avg_points_against, lower is better, so we invert it
                if 'avg_points_against' in radar_df.columns:
                    radar_df['defense'] = 1 - (radar_df['avg_points_against'] - radar_df['avg_points_against'].min()) / (radar_df['avg_points_against'].max() - radar_df['avg_points_against'].min()) if radar_df['avg_points_against'].max() != radar_df['avg_points_against'].min() else 0.5
                    radar_metrics.append('defense')
                
                # Create radar chart
                fig5 = go.Figure()
                
                for _, division_row in radar_df.iterrows():
                    division_name = division_row['division']
                    
                    # Get values for radar chart
                    values = [division_row[metric] for metric in radar_metrics]
                    
                    # Close the loop by repeating the first value
                    values.append(values[0])
                    
                    # Prepare labels
                    labels = [metric.replace('_', ' ').title() for metric in radar_metrics]
                    labels = [label.replace('Avg Win Pct', 'Win %').replace('Avg Points For', 'Offense').replace('Defense', 'Defense').replace('Win Loss Ratio', 'W/L Ratio') for label in labels]
                    labels.append(labels[0])  # Repeat first label
                    
                    fig5.add_trace(go.Scatterpolar(
                        r=values,
                        theta=labels,
                        fill='toself',
                        name=division_name
                    ))
                
                fig5.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )
                    ),
                    showlegend=True,
                    title="Division Strength Comparison",
                    height=600
                )
                
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("Division data is not available. Please check that teams are assigned to divisions in the divisions.csv file.")

    with comparison_tab:
        st.subheader("Team Performance Radar Chart")
        
        # Create an advanced radar chart for team comparison
        if standings_data.shape[0] > 0:
            # Let user select teams to compare
            unique_teams = standings_data['team'].tolist()
            default_selections = unique_teams[:4] if len(unique_teams) >= 4 else unique_teams
            
            selected_teams = st.multiselect(
                "Select teams to compare (max 5 recommended):",
                options=unique_teams,
                default=default_selections
            )
            
            if not selected_teams:
                st.info("Please select at least one team to display the radar chart.")
            else:
                # Filter dataframe for selected teams
                filtered_teams = standings_data[standings_data['team'].isin(selected_teams)]
                
                # Determine metrics to use based on available columns
                metrics = []
                if 'win_percentage' in standings_data.columns:
                    metrics.append('win_percentage')
                    
                if 'points_for' in standings_data.columns:
                    metrics.append('points_for')
                    
                if 'points_against' in standings_data.columns:
                    # For points against, lower is better, so we'll invert it
                    filtered_teams['defense'] = filtered_teams['points_against'].max() - filtered_teams['points_against']
                    metrics.append('defense')
                
                # If we have at least 2 metrics, create radar chart
                if len(metrics) >= 2:
                    # Normalize values to 0-1 scale for radar chart
                    normalized_data = filtered_teams.copy()
                    
                    for metric in metrics:
                        if metric in normalized_data.columns and normalized_data[metric].max() != normalized_data[metric].min():
                            normalized_data[metric] = (normalized_data[metric] - normalized_data[metric].min()) / (normalized_data[metric].max() - normalized_data[metric].min())
                    
                    # Create radar chart
                    fig = go.Figure()
                    
                    for i, team in enumerate(normalized_data['team']):
                        team_data = normalized_data[normalized_data['team'] == team]
                        
                        # Get values for radar chart
                        values = [team_data[metric].values[0] for metric in metrics]
                        
                        # Close the loop by repeating the first value
                        values.append(values[0])
                        
                        # Prepare labels
                        labels = [metric.replace('_', ' ').title() for metric in metrics]
                        labels = [label.replace('Win Percentage', 'Win %').replace('Points For', 'Offense').replace('Defense', 'Defense') for label in labels]
                        labels.append(labels[0])  # Repeat first label
                        
                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=labels,
                            fill='toself',
                            name=team
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        showlegend=True,
                        title="Team Performance Comparison",
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Not enough metrics available for a radar chart comparison.")
                    
        # Add a division standings comparison if we can group teams by division
        st.subheader("Division Standings")
        
        # Check if we have divisions in our data
        if 'division' in standings_data.columns and not all(standings_data['division'] == 'Unknown'):
            # Group teams by division
            division_groups = standings_data.groupby('division')
            
            # Create an expander for each division
            for division_name, division_data in division_groups:
                with st.expander(f"{division_name} Standings", expanded=True):
                    # Sort division data by rank
                    division_data = division_data.sort_values('win_percentage' if 'win_percentage' in division_data.columns else 'rank', ascending=False)
                    
                    # Display standings table for this division
                    # Create a displayable table with only the most relevant columns
                    display_df = division_data[['team', 'wins', 'losses', 'ties', 'win_percentage', 'points_for']].copy() if all(col in division_data.columns for col in ['wins', 'losses', 'ties', 'win_percentage', 'points_for']) else division_data
                    
                    # Format the table
                    st.dataframe(
                        display_df,
                        column_config={
                            "team": "Team",
                            "wins": st.column_config.NumberColumn("W", format="%d"),
                            "losses": st.column_config.NumberColumn("L", format="%d"),
                            "ties": st.column_config.NumberColumn("T", format="%d"),
                            "win_percentage": st.column_config.NumberColumn("Win %", format="%.3f"),
                            "points_for": st.column_config.NumberColumn("PF", format="%.1f")
                        },
                        hide_index=True
                    )
                    
                    # Calculate and display division stats
                    if len(division_data) > 0 and 'points_for' in division_data.columns:
                        division_total_points = division_data['points_for'].sum()
                        division_avg_points = division_data['points_for'].mean()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Division Points", f"{division_total_points:.1f}")
                        with col2:
                            st.metric("Avg Team Points", f"{division_avg_points:.1f}")
            
            # Add a division comparison chart
            st.subheader("Division Comparison")
            
            # Prepare data for division comparison
            division_stats = []
            for division_name, division_data in division_groups:
                if 'points_for' in division_data.columns and 'win_percentage' in division_data.columns:
                    division_stats.append({
                        'division': division_name,
                        'avg_points': division_data['points_for'].mean(),
                        'avg_win_pct': division_data['win_percentage'].mean(),
                        'teams': len(division_data),
                        'total_wins': division_data['wins'].sum() if 'wins' in division_data.columns else 0
                    })
            
            if division_stats:
                division_stats_df = pd.DataFrame(division_stats)
                
                # Create a bar chart for division comparison
                fig = px.bar(
                    division_stats_df,
                    x='division',
                    y=['avg_points', 'avg_win_pct', 'total_wins'],
                    barmode='group',
                    title='Division Performance Comparison',
                    labels={
                        'division': 'Division',
                        'value': 'Value',
                        'variable': 'Metric'
                    },
                    color_discrete_sequence=['#3498db', '#2ecc71', '#f39c12']
                )
                
                # Customize the legend labels
                fig.for_each_trace(lambda t: t.update(
                    name={'avg_points': 'Avg Points', 'avg_win_pct': 'Avg Win %', 'total_wins': 'Total Wins'}[t.name]
                ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a sunburst chart showing division hierarchy
                if 'wins' in standings_data.columns and 'points_for' in standings_data.columns:
                    sunburst_data = standings_data[['team', 'division', 'wins', 'points_for']].copy()
                    sunburst_data['size'] = sunburst_data['points_for']  # Size based on points
                    
                    fig2 = px.sunburst(
                        sunburst_data,
                        path=['division', 'team'],
                        values='size',
                        color='wins',
                        color_continuous_scale='RdYlGn',
                        title='Team Distribution by Division',
                        hover_data=['points_for', 'wins']
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Division data has been loaded from attached_assets/divisions.csv. Use it to compare performance across divisions.")
            
            # Show how to set up divisions
            with st.expander("Division Setup Information"):
                st.write("""
                The division data is loaded from the attached_assets/divisions.csv file. 
                Each row in this file should contain:
                - Division name (e.g., AL East, NL Central)
                - Team name (must match exactly the team names used in the API)
                
                For example:
                ```
                AL East,New York Yankees
                AL East,Boston Red Sox
                NL West,Los Angeles Dodgers
                ```
                """)