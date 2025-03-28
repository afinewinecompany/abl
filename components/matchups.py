import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def render(matchups_data: List[Dict[str, Any]], scoring_periods: List[Dict[str, Any]]):
    """
    Render the matchups page with detailed information about team matchups.
    
    Args:
        matchups_data: List of matchup dictionaries
        scoring_periods: List of scoring period information
    """
    st.title("Fantasy Matchups")
    
    # Create period selector
    periods = []
    current_period_id = None
    
    # Process scoring periods for the dropdown
    if scoring_periods:
        for period in scoring_periods:
            period_id = period.get('week')
            if period_id is not None:
                # Try to convert to int for proper sorting
                try:
                    period_id = int(period_id)
                except (ValueError, TypeError):
                    pass
                
                # Get display name for period
                period_name = f"Week {period_id}"
                start_date = period.get('start_date')
                end_date = period.get('end_date')
                
                if start_date and end_date:
                    try:
                        # Format dates if available
                        start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        date_range = f"{start_date_obj.strftime('%b %d')} - {end_date_obj.strftime('%b %d')}"
                        period_name = f"Week {period_id} ({date_range})"
                    except (ValueError, TypeError):
                        pass
                
                periods.append({"id": period_id, "name": period_name})
                
                # Identify current period
                if period.get('is_current', False):
                    current_period_id = period_id
    
    # If no periods found from API, create fallback periods
    if not periods:
        periods = [{"id": i, "name": f"Week {i}"} for i in range(1, 26)]
        current_period_id = 1  # Default to week 1
    
    # Sort periods
    periods = sorted(periods, key=lambda x: x["id"])
    
    # Create period selector with meaningful labels
    period_options = {period["name"]: period["id"] for period in periods}
    
    # Find the current period option
    default_period_option = next((name for name, period_id in period_options.items() 
                               if period_id == current_period_id), list(period_options.keys())[0])
    
    selected_period_name = st.selectbox(
        "Select Scoring Period",
        options=list(period_options.keys()),
        index=list(period_options.keys()).index(default_period_option) if default_period_option in period_options.keys() else 0
    )
    
    selected_period_id = period_options[selected_period_name]
    
    # Filter matchups to the selected period with improved error handling
    if not matchups_data:
        st.warning("No matchup data is available")
        
        # Display information about what matchups will show
        st.info("""
        ### When Matchups Are Available
        
        This section will display detailed matchup information including:
        - Matchup score cards with team records
        - Win probability calculations
        - League-wide scoring distributions
        - Team performance trends across weeks
        """)
        return
        
    filtered_matchups = [matchup for matchup in matchups_data if matchup.get('period_id') == selected_period_id]
    
    if not filtered_matchups:
        st.warning(f"No matchups available for {selected_period_name}")
        
        # Suggest checking other periods
        available_periods = set([m.get('period_id') for m in matchups_data if m.get('period_id') is not None])
        if available_periods:
            available_period_names = [next((p["name"] for p in periods if p["id"] == period_id), f"Week {period_id}") 
                                     for period_id in available_periods]
            st.info(f"Matchups are available for: {', '.join(available_period_names)}")
        return
    
    # Display matchups in visually appealing cards
    st.markdown(f"### Matchups for {selected_period_name}")
    
    # Create a grid layout for matchups
    for i in range(0, len(filtered_matchups), 2):
        cols = st.columns(2 if i + 1 < len(filtered_matchups) else 1)
        
        # First matchup in this row
        render_matchup_card(filtered_matchups[i], cols[0])
        
        # Second matchup in this row (if exists)
        if i + 1 < len(filtered_matchups):
            render_matchup_card(filtered_matchups[i + 1], cols[1])
    
    # Display league-wide matchup statistics
    st.markdown("---")
    st.markdown("### League Matchup Statistics")
    
    # Calculate matchup statistics
    if filtered_matchups:
        matchup_stats = calculate_matchup_stats(filtered_matchups)
        display_matchup_stats(matchup_stats)
        
        # Create visualization
        create_score_distribution_chart(filtered_matchups)
        create_margin_of_victory_chart(filtered_matchups)
    else:
        st.info("No matchup data available for statistical analysis")

def render_matchup_card(matchup: Dict[str, Any], column):
    """Render a single matchup card in the specified column with improved styling and error handling"""
    with column:
        # Validate and extract required fields with fallbacks
        try:
            away_team = matchup.get('away_team', 'Unknown')
            home_team = matchup.get('home_team', 'Unknown')
            
            # Convert scores to float with error handling
            try:
                away_score = float(matchup.get('away_score', 0))
            except (ValueError, TypeError):
                away_score = 0
                
            try:
                home_score = float(matchup.get('home_score', 0))
            except (ValueError, TypeError):
                home_score = 0
            
            # Calculate score difference if not provided
            score_difference = matchup.get('score_difference')
            if score_difference is None:
                score_difference = abs(away_score - home_score)
            
            # Determine winner for styling
            if away_score > home_score:
                away_style = "font-weight: bold; color: #2ea043;"  # Green for winner
                home_style = ""
                away_indicator = "▲"  # Up triangle for winner
                home_indicator = ""
            elif home_score > away_score:
                home_style = "font-weight: bold; color: #2ea043;"  # Green for winner
                away_style = ""
                home_indicator = "▲"  # Up triangle for winner
                away_indicator = ""
            else:
                away_style = home_style = "font-style: italic;"
                away_indicator = home_indicator = "="  # Equal sign for tie
            
            # Create enhanced matchup card with clean styling and win indicators
            st.markdown(f"""
            <div style="
                border: 1px solid rgba(230, 230, 230, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: rgba(35, 38, 45, 0.8);
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <div style="text-align: left; {away_style}">
                        <div style="font-size: 18px; display: flex; align-items: center;">
                            <span>{away_team}</span>
                            <span style="margin-left: 5px; font-size: 14px; color: #2ea043;">{away_indicator}</span>
                        </div>
                        <div style="font-size: 24px;">{away_score:.1f}</div>
                    </div>
                    <div style="text-align: center; margin-top: 15px;">
                        <span style="opacity: 0.6;">@</span>
                    </div>
                    <div style="text-align: right; {home_style}">
                        <div style="font-size: 18px; display: flex; align-items: center; justify-content: flex-end;">
                            <span>{home_team}</span>
                            <span style="margin-left: 5px; font-size: 14px; color: #2ea043;">{home_indicator}</span>
                        </div>
                        <div style="font-size: 24px;">{home_score:.1f}</div>
                    </div>
                </div>
                <div style="text-align: center; opacity: 0.8; font-size: 14px; margin-top: 10px;">
                    <span style="background-color: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 10px; font-family: monospace;">
                        Diff: {score_difference:.1f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            # Fallback rendering if there's an error with the matchup data
            st.warning(f"Error rendering matchup: {str(e)}")
            st.markdown("""
            <div style="
                border: 1px solid rgba(255, 0, 0, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: rgba(35, 38, 45, 0.8);
            ">
                <div style="text-align: center;">
                    <p>Unable to display matchup information</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

def calculate_matchup_stats(matchups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about the matchups for display"""
    if not matchups:
        return {}
    
    # Collect all scores
    all_scores = []
    for matchup in matchups:
        all_scores.append(matchup.get('away_score', 0))
        all_scores.append(matchup.get('home_score', 0))
    
    # Calculate score differentials
    score_diffs = [matchup.get('score_difference', 0) for matchup in matchups]
    
    # Collect team performances
    team_performances = {}
    for matchup in matchups:
        away_team = matchup.get('away_team', 'Unknown')
        home_team = matchup.get('home_team', 'Unknown')
        away_score = matchup.get('away_score', 0)
        home_score = matchup.get('home_score', 0)
        
        # Update team stats
        if away_team not in team_performances:
            team_performances[away_team] = {'scores': [], 'wins': 0, 'losses': 0, 'ties': 0}
        if home_team not in team_performances:
            team_performances[home_team] = {'scores': [], 'wins': 0, 'losses': 0, 'ties': 0}
        
        # Add scores
        team_performances[away_team]['scores'].append(away_score)
        team_performances[home_team]['scores'].append(home_score)
        
        # Update win/loss/tie records
        if away_score > home_score:
            team_performances[away_team]['wins'] += 1
            team_performances[home_team]['losses'] += 1
        elif home_score > away_score:
            team_performances[home_team]['wins'] += 1
            team_performances[away_team]['losses'] += 1
        else:
            team_performances[away_team]['ties'] += 1
            team_performances[home_team]['ties'] += 1
    
    # Calculate high and low scores
    high_score = max(all_scores) if all_scores else 0
    high_score_team = None
    low_score = min(all_scores) if all_scores else 0
    low_score_team = None
    
    for team, stats in team_performances.items():
        if high_score in stats['scores']:
            high_score_team = team
        if low_score in stats['scores']:
            low_score_team = team
    
    # Calculate closest and biggest margins
    closest_margin = min(score_diffs) if score_diffs else 0
    biggest_margin = max(score_diffs) if score_diffs else 0
    
    closest_matchup = None
    biggest_blowout = None
    
    for matchup in matchups:
        if matchup.get('score_difference') == closest_margin:
            closest_matchup = matchup
        if matchup.get('score_difference') == biggest_margin:
            biggest_blowout = matchup
    
    # Return calculated stats
    return {
        'high_score': {'score': high_score, 'team': high_score_team},
        'low_score': {'score': low_score, 'team': low_score_team},
        'closest_matchup': closest_matchup,
        'biggest_blowout': biggest_blowout,
        'average_score': sum(all_scores) / len(all_scores) if all_scores else 0,
        'average_margin': sum(score_diffs) / len(score_diffs) if score_diffs else 0,
        'team_performances': team_performances
    }

def display_matchup_stats(stats: Dict[str, Any]):
    """Display calculated matchup statistics"""
    # Create a 2x2 grid for key stats
    col1, col2 = st.columns(2)
    
    # Highest and lowest scores
    with col1:
        st.markdown("#### Highest Score")
        if stats.get('high_score'):
            st.markdown(f"""
            <div style="background-color: rgba(46, 160, 67, 0.2); padding: 10px; border-radius: 5px;">
                <span style="font-size: 24px; font-weight: bold;">{stats['high_score']['score']:.1f}</span>
                <br/><span>{stats['high_score']['team']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### Closest Matchup")
        if stats.get('closest_matchup'):
            closest = stats['closest_matchup']
            st.markdown(f"""
            <div style="background-color: rgba(33, 150, 243, 0.2); padding: 10px; border-radius: 5px;">
                <span style="font-size: 18px;">{closest['away_team']} ({closest['away_score']:.1f}) @ {closest['home_team']} ({closest['home_score']:.1f})</span>
                <br/><span>Margin: {closest['score_difference']:.1f}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Lowest Score")
        if stats.get('low_score'):
            st.markdown(f"""
            <div style="background-color: rgba(229, 57, 53, 0.2); padding: 10px; border-radius: 5px;">
                <span style="font-size: 24px; font-weight: bold;">{stats['low_score']['score']:.1f}</span>
                <br/><span>{stats['low_score']['team']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### Biggest Blowout")
        if stats.get('biggest_blowout'):
            blowout = stats['biggest_blowout']
            # Make sure we have all required fields
            if all(k in blowout for k in ['away_team', 'away_score', 'home_team', 'home_score', 'winner', 'score_difference']):
                winner = blowout['winner']
                loser = blowout['away_team'] if winner == blowout['home_team'] else blowout['home_team']
                winner_score = blowout['away_score'] if winner == blowout['away_team'] else blowout['home_score']
                loser_score = blowout['home_score'] if winner == blowout['away_team'] else blowout['away_score']
                
                st.markdown(f"""
                <div style="background-color: rgba(255, 152, 0, 0.2); padding: 10px; border-radius: 5px;">
                    <span style="font-size: 18px;">{winner} ({winner_score:.1f}) vs {loser} ({loser_score:.1f})</span>
                    <br/><span>Margin: {blowout['score_difference']:.1f}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: rgba(255, 152, 0, 0.2); padding: 10px; border-radius: 5px;">
                    <span style="font-size: 18px;">{blowout.get('away_team', 'Team A')} ({blowout.get('away_score', 0):.1f}) @ {blowout.get('home_team', 'Team B')} ({blowout.get('home_score', 0):.1f})</span>
                    <br/><span>Margin: {blowout.get('score_difference', 0):.1f}</span>
                </div>
                """, unsafe_allow_html=True)
    
    # Average scores
    st.markdown("#### League Averages")
    avg_col1, avg_col2 = st.columns(2)
    
    with avg_col1:
        st.metric("Average Score", f"{stats.get('average_score', 0):.1f}")
    
    with avg_col2:
        st.metric("Average Margin of Victory", f"{stats.get('average_margin', 0):.1f}")

def create_score_distribution_chart(matchups: List[Dict[str, Any]]):
    """Create a distribution chart of team scores"""
    # Collect all scores with team labels
    scores = []
    for matchup in matchups:
        scores.append({
            'Team': matchup.get('away_team', 'Unknown'),
            'Score': matchup.get('away_score', 0),
            'Location': 'Away'
        })
        scores.append({
            'Team': matchup.get('home_team', 'Unknown'),
            'Score': matchup.get('home_score', 0),
            'Location': 'Home'
        })
    
    if not scores:
        return
    
    # Convert to DataFrame for plotting
    scores_df = pd.DataFrame(scores)
    
    # Create score distribution chart
    fig = px.histogram(
        scores_df, 
        x='Score', 
        color='Team',
        title='Team Score Distribution',
        labels={'Score': 'Fantasy Points', 'count': 'Number of Occurrences'},
        opacity=0.7,
        barmode='overlay'
    )
    
    fig.update_layout(
        xaxis_title='Fantasy Points',
        yaxis_title='Count',
        legend_title='Team',
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_margin_of_victory_chart(matchups: List[Dict[str, Any]]):
    """Create a bar chart showing margin of victory by matchup"""
    if not matchups:
        return
    
    # Prepare data for the chart
    matchup_data = []
    for matchup in matchups:
        winner = matchup.get('winner', 'Unknown')
        loser = matchup.get('loser', 'Unknown')
        margin = matchup.get('score_difference', 0)
        
        # Skip ties
        if winner == "Tie" or loser == "Tie":
            matchup_label = f"{matchup.get('away_team')} vs {matchup.get('home_team')} (Tie)"
            matchup_data.append({
                'Matchup': matchup_label,
                'Margin': 0,
                'Winner': 'Tie',
                'Loser': 'Tie'
            })
        else:
            matchup_label = f"{winner} vs {loser}"
            matchup_data.append({
                'Matchup': matchup_label,
                'Margin': margin,
                'Winner': winner,
                'Loser': loser
            })
    
    # Convert to DataFrame
    margin_df = pd.DataFrame(matchup_data)
    
    # Sort by margin for better visualization
    margin_df = margin_df.sort_values(by='Margin', ascending=False)
    
    # Create margin chart
    fig = px.bar(
        margin_df,
        x='Matchup',
        y='Margin',
        color='Winner',
        title='Margin of Victory by Matchup',
        hover_data=['Winner', 'Loser', 'Margin'],
        labels={'Margin': 'Points Difference', 'Matchup': 'Teams'},
        height=500
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title='',
        yaxis_title='Margin of Victory (Points)',
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)