import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import plotly.express as px
import json
from components.prospects import get_player_headshot_html, create_player_id_cache

def render(available_players_df: pd.DataFrame, mlb_ids_df: Optional[pd.DataFrame] = None):
    """
    Render available players component with filters and interactive display
    
    Args:
        available_players_df: DataFrame of available players from Fantrax
        mlb_ids_df: Optional DataFrame with MLB player IDs for headshots
    """
    st.header("Available Players", divider="blue")
    
    if available_players_df.empty:
        st.error("⚠️ No available players data found from Fantrax")
        
        if st.session_state.get('fantrax_logged_in', False):
            st.warning("You're logged in, but we couldn't retrieve player data.")
            
            with st.expander("🔍 Troubleshooting Steps", expanded=True):
                st.markdown("""
                ### Possible Issues:
                1. **Authentication Problems**: Your Fantrax session may have expired
                2. **API Changes**: Fantrax may have updated their API structure
                3. **Access Restrictions**: Your account may not have access to this specific league's available players
                
                ### Try these solutions:
                1. Click the **Logout** button in the sidebar and log in again
                2. Make sure your league ID is correct in the .env file (current ID: `{league_id}`)
                3. Check if you can access the [Available Players page](https://www.fantrax.com/fantasy/league/{league_id}/players;view=AVAILABLE) directly in your browser
                4. Try toggling the Debug Mode in the sidebar to see detailed error information
                """.format(league_id=st.session_state.get('league_id', 'unknown')))
            
            # Show debug info if in debug mode
            if st.session_state.get('debug_mode', False):
                st.info("🔍 Debug Information")
                auth_status = st.session_state.get('fantrax_auth', {})
                cookie_count = len(auth_status.get('cookies', {}))
                st.code(f"""
Authentication Status: {st.session_state.get('fantrax_logged_in', False)}
Username: {st.session_state.get('fantrax_username', 'Not set')}
Cookie Count: {cookie_count}
League ID: {st.session_state.get('league_id', 'Not set')}
                """)
            
            return
        else:
            st.warning("Please log in with your Fantrax account to view available players.")
            st.info("Enter your Fantrax credentials in the sidebar to authenticate and access player data.")
            return
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    
    # Get unique values for filters
    positions = sorted(available_players_df['position'].unique())
    mlb_teams = sorted(available_players_df['mlb_team'].unique())
    
    with col1:
        selected_position = st.selectbox("Position", ["All"] + list(positions))
    
    with col2:
        selected_team = st.selectbox("MLB Team", ["All"] + list(mlb_teams))
    
    with col3:
        search_term = st.text_input("Search Player", "")
    
    # Apply filters
    filtered_df = available_players_df.copy()
    
    if selected_position != "All":
        filtered_df = filtered_df[filtered_df['position'] == selected_position]
    
    if selected_team != "All":
        filtered_df = filtered_df[filtered_df['mlb_team'] == selected_team]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['player_name'].str.lower().str.contains(search_term.lower())
        ]
    
    # Create player ID cache for headshots if MLB IDs are available
    player_id_cache = {}
    if mlb_ids_df is not None and not mlb_ids_df.empty:
        player_id_cache = create_player_id_cache(mlb_ids_df)
    
    # Display players in card format
    st.subheader(f"Found {len(filtered_df)} Players")
    
    # Create rows of player cards (3 per row)
    for i in range(0, len(filtered_df), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(filtered_df):
                player = filtered_df.iloc[i + j]
                with cols[j]:
                    render_player_card(player, player_id_cache)
    
def render_player_card(player, player_id_cache):
    """
    Render a card for an individual player
    
    Args:
        player: Series containing player information
        player_id_cache: Dictionary mapping player names to MLB IDs for headshots
    """
    # Get player headshot if available
    headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
    
    # Determine card color based on player position (pitcher vs hitter)
    if player['position'] in ['SP', 'RP', 'P']:
        card_color = "rgba(23, 162, 184, 0.1)"  # Blue for pitchers
        border_color = "rgba(23, 162, 184, 0.5)"
    else:
        card_color = "rgba(40, 167, 69, 0.1)"  # Green for hitters
        border_color = "rgba(40, 167, 69, 0.5)"
    
    # Card HTML with player details
    card_html = f"""
    <div style="
        background-color: {card_color}; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 15px;
        border: 1px solid {border_color};
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center;">
            <div style="flex: 0 0 70px; margin-right: 15px;">
                {headshot_html}
            </div>
            <div style="flex-grow: 1;">
                <h3 style="margin: 0; color: #333;">{player['player_name']}</h3>
                <div style="color: #666; margin: 5px 0;">
                    <span style="font-weight: bold;">{player['position']}</span> | {player['mlb_team']}
                </div>
                <div style="color: #777; font-size: 14px;">
                    Status: {player['status']}
                </div>
            </div>
        </div>
    """
    
    # Add stats section if available
    if isinstance(player['stats'], dict) and player['stats']:
        # Format the stats display
        if player['position'] in ['SP', 'RP', 'P']:
            # Pitcher stats
            pit_stats = {k.replace('pit_', ''): v for k, v in player['stats'].items() if k.startswith('pit_')}
            if pit_stats:
                card_html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1);">'
                card_html += '<div style="font-weight: bold; margin-bottom: 5px;">Pitching Stats</div>'
                card_html += '<div style="display: flex; flex-wrap: wrap;">'
                
                # Prioritize key pitching stats
                key_stats = ['ERA', 'WHIP', 'W', 'SV', 'SO']
                for stat in key_stats:
                    if stat in pit_stats:
                        value = pit_stats[stat]
                        if isinstance(value, (int, float)):
                            if stat in ['ERA', 'WHIP']:
                                value = f"{value:.2f}"
                            else:
                                value = f"{int(value)}"
                        card_html += f'<div style="flex: 0 0 50%; margin-bottom: 3px;"><span style="color: #555;">{stat}:</span> {value}</div>'
                
                card_html += '</div></div>'
        else:
            # Hitter stats
            hit_stats = {k.replace('hit_', ''): v for k, v in player['stats'].items() if k.startswith('hit_')}
            if hit_stats:
                card_html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1);">'
                card_html += '<div style="font-weight: bold; margin-bottom: 5px;">Hitting Stats</div>'
                card_html += '<div style="display: flex; flex-wrap: wrap;">'
                
                # Prioritize key hitting stats
                key_stats = ['AVG', 'HR', 'RBI', 'R', 'SB']
                for stat in key_stats:
                    if stat in hit_stats:
                        value = hit_stats[stat]
                        if isinstance(value, (int, float)):
                            if stat == 'AVG':
                                value = f"{value:.3f}".lstrip('0')
                            else:
                                value = f"{int(value)}"
                        card_html += f'<div style="flex: 0 0 50%; margin-bottom: 3px;"><span style="color: #555;">{stat}:</span> {value}</div>'
                
                card_html += '</div></div>'
    
    # Close the card div
    card_html += '</div>'
    
    # Render the card
    st.markdown(card_html, unsafe_allow_html=True)

def generate_sample_player_data() -> pd.DataFrame:
    """
    Generate sample player data for demonstration purposes
    Returns a DataFrame with sample player data formatted like Fantrax data
    """
    # Define sample data
    sample_players = [
        # Star hitters
        {"player_id": "h1", "player_name": "Aaron Judge", "position": "OF", "mlb_team": "NYY", "status": "Active",
         "eligible_positions": ["OF", "DH"], 
         "stats": {"hit_AVG": .294, "hit_HR": 41, "hit_RBI": 102, "hit_R": 96, "hit_SB": 12}},
        {"player_id": "h2", "player_name": "Juan Soto", "position": "OF", "mlb_team": "NYY", "status": "Active",
         "eligible_positions": ["OF", "DH"], 
         "stats": {"hit_AVG": .306, "hit_HR": 35, "hit_RBI": 86, "hit_R": 109, "hit_SB": 6}},
        {"player_id": "h3", "player_name": "Shohei Ohtani", "position": "DH", "mlb_team": "LAD", "status": "Active",
         "eligible_positions": ["DH", "UT"], 
         "stats": {"hit_AVG": .289, "hit_HR": 44, "hit_RBI": 95, "hit_R": 115, "hit_SB": 25}},
        {"player_id": "h4", "player_name": "Bobby Witt Jr.", "position": "SS", "mlb_team": "KC", "status": "Active",
         "eligible_positions": ["SS", "3B"], 
         "stats": {"hit_AVG": .311, "hit_HR": 27, "hit_RBI": 92, "hit_R": 99, "hit_SB": 36}},
        {"player_id": "h5", "player_name": "Gunnar Henderson", "position": "SS", "mlb_team": "BAL", "status": "Active",
         "eligible_positions": ["SS", "3B"], 
         "stats": {"hit_AVG": .284, "hit_HR": 30, "hit_RBI": 82, "hit_R": 104, "hit_SB": 18}},
         
        # Injured hitters
        {"player_id": "h6", "player_name": "Julio Rodriguez", "position": "OF", "mlb_team": "SEA", "status": "IL",
         "eligible_positions": ["OF"], 
         "stats": {"hit_AVG": .278, "hit_HR": 18, "hit_RBI": 56, "hit_R": 68, "hit_SB": 23}},
        {"player_id": "h7", "player_name": "Bryce Harper", "position": "1B", "mlb_team": "PHI", "status": "IL",
         "eligible_positions": ["1B", "OF", "DH"], 
         "stats": {"hit_AVG": .297, "hit_HR": 29, "hit_RBI": 89, "hit_R": 82, "hit_SB": 11}},
         
        # Prospect hitters
        {"player_id": "h8", "player_name": "Jackson Holliday", "position": "SS", "mlb_team": "BAL", "status": "Minors",
         "eligible_positions": ["SS", "2B"], 
         "stats": {"hit_AVG": .312, "hit_HR": 12, "hit_RBI": 44, "hit_R": 66, "hit_SB": 16}},
        {"player_id": "h9", "player_name": "Jordan Lawlar", "position": "SS", "mlb_team": "ARI", "status": "Minors",
         "eligible_positions": ["SS"], 
         "stats": {"hit_AVG": .285, "hit_HR": 14, "hit_RBI": 58, "hit_R": 62, "hit_SB": 25}},
         
        # Star pitchers
        {"player_id": "p1", "player_name": "Gerrit Cole", "position": "SP", "mlb_team": "NYY", "status": "Active",
         "eligible_positions": ["SP"], 
         "stats": {"pit_ERA": 3.05, "pit_WHIP": 1.02, "pit_W": 14, "pit_SV": 0, "pit_SO": 218}},
        {"player_id": "p2", "player_name": "Spencer Strider", "position": "SP", "mlb_team": "ATL", "status": "IL",
         "eligible_positions": ["SP"], 
         "stats": {"pit_ERA": 2.58, "pit_WHIP": 0.94, "pit_W": 8, "pit_SV": 0, "pit_SO": 104}},
        {"player_id": "p3", "player_name": "Emmanuel Clase", "position": "RP", "mlb_team": "CLE", "status": "Active",
         "eligible_positions": ["RP"], 
         "stats": {"pit_ERA": 1.88, "pit_WHIP": 0.82, "pit_W": 5, "pit_SV": 41, "pit_SO": 62}},
        {"player_id": "p4", "player_name": "Zac Gallen", "position": "SP", "mlb_team": "ARI", "status": "Active",
         "eligible_positions": ["SP"], 
         "stats": {"pit_ERA": 3.22, "pit_WHIP": 1.12, "pit_W": 12, "pit_SV": 0, "pit_SO": 183}},
         
        # Prospect pitchers
        {"player_id": "p5", "player_name": "Jackson Jobe", "position": "SP", "mlb_team": "DET", "status": "Minors",
         "eligible_positions": ["SP"], 
         "stats": {"pit_ERA": 2.81, "pit_WHIP": 1.05, "pit_W": 7, "pit_SV": 0, "pit_SO": 92}},
        {"player_id": "p6", "player_name": "Cade Horton", "position": "SP", "mlb_team": "CHC", "status": "Minors",
         "eligible_positions": ["SP"], 
         "stats": {"pit_ERA": 3.14, "pit_WHIP": 1.13, "pit_W": 9, "pit_SV": 0, "pit_SO": 118}},
    ]
    
    # Convert to DataFrame
    return pd.DataFrame(sample_players)

def fetch_mlb_player_ids() -> pd.DataFrame:
    """
    Fetch MLB player IDs from CSV files in attached_assets
    Returns a DataFrame with player names and IDs
    """
    try:
        # Try both possible file locations
        try:
            df = pd.read_csv("attached_assets/mlb_player_ids.csv")
        except:
            try:
                df = pd.read_csv("attached_assets/mlb_player_ids-2.csv")
            except:
                return pd.DataFrame(columns=["PLAYERNAME", "MLBAMID"])
                
        # Clean and prepare the DataFrame
        if "PLAYERNAME" in df.columns and "MLBAMID" in df.columns:
            return df[["PLAYERNAME", "MLBAMID"]]
        else:
            return pd.DataFrame(columns=["PLAYERNAME", "MLBAMID"])
    except Exception as e:
        st.error(f"Error loading MLB player IDs: {str(e)}")
        return pd.DataFrame(columns=["PLAYERNAME", "MLBAMID"])