import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import numpy as np
import re
from typing import Dict, List, Any, Optional, Tuple

# Constants for MLB team colors
from components.prospects import MLB_TEAM_COLORS, MLB_TEAM_IDS, MLB_TEAM_ABBR_TO_NAME

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

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        if not name or not isinstance(name, str):
            return ""
        
        # Convert to lowercase, remove accents, strip whitespace
        normalized = name.lower().strip()
        
        # Remove special characters and anything in brackets/parentheses
        normalized = re.sub(r'[\(\[].*?[\)\]]', '', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    except Exception:
        return ""

def create_player_id_cache(mlb_ids_df: pd.DataFrame = None) -> Dict[str, Dict[str, str]]:
    """
    Create a comprehensive player ID mapping system using both the PLAYERIDMAP.csv file and mlb_ids_df
    
    Returns:
        Dict with the following structure:
        {
            'fantrax_to_mlbid': Dict mapping Fantrax IDs to MLB IDs,
            'name_to_mlbid': Dict mapping player names to MLB IDs,
            'name_to_fantraxid': Dict mapping player names to Fantrax IDs
        }
    """
    cache = {
        'fantrax_to_mlbid': {},
        'name_to_mlbid': {},
        'name_to_fantraxid': {}
    }
    
    # Try to load the PLAYERIDMAP.csv file first (this has direct Fantrax ID to MLB ID mapping)
    try:
        player_map_df = pd.read_csv("attached_assets/PLAYERIDMAP.csv")
        
        # Process each row in the player map
        for _, row in player_map_df.iterrows():
            try:
                # Skip rows with missing critical data
                if pd.isna(row['MLBID']) or pd.isna(row['PLAYERNAME']):
                    continue
                
                # Convert MLBID to integer and then to string to remove decimal places
                try:
                    mlbid = str(int(row['MLBID']))
                except:
                    # If conversion fails, use as is but ensure no decimal places
                    mlbid = str(row['MLBID']).split('.')[0].strip()
                
                player_name = normalize_name(str(row['PLAYERNAME']).strip())
                
                # Add name to MLB ID mapping
                if player_name:
                    cache['name_to_mlbid'][player_name] = mlbid
                
                # Process Fantrax ID if available
                if not pd.isna(row['FANTRAXID']) and str(row['FANTRAXID']).strip():
                    fantrax_id = str(row['FANTRAXID']).strip()
                    
                    # Add Fantrax ID to MLB ID mapping
                    cache['fantrax_to_mlbid'][fantrax_id] = mlbid
                    
                    # Also add without asterisks
                    clean_fantrax_id = fantrax_id.replace('*', '')
                    if clean_fantrax_id != fantrax_id:
                        cache['fantrax_to_mlbid'][clean_fantrax_id] = mlbid
                    
                    # Add name to Fantrax ID mapping
                    if player_name:
                        cache['name_to_fantraxid'][player_name] = fantrax_id
                
                # Add first/last name variations
                if not pd.isna(row['FIRSTNAME']) and not pd.isna(row['LASTNAME']):
                    first = str(row['FIRSTNAME']).strip()
                    last = str(row['LASTNAME']).strip()
                    
                    # First + Last format
                    full_name = normalize_name(f"{first} {last}")
                    if full_name:
                        cache['name_to_mlbid'][full_name] = mlbid
                    
                    # Last, First format
                    alt_name = normalize_name(f"{last}, {first}")
                    if alt_name:
                        cache['name_to_mlbid'][alt_name] = mlbid
                    
                    # Last name only (as fallback)
                    last_name = normalize_name(last)
                    if last_name and len(last_name) > 3:  # Only use last names that are longer than 3 chars
                        cache['name_to_mlbid'][last_name] = mlbid
                
                # Add alternate team name mappings for team lookup
                if not pd.isna(row['TEAM']) and row['ACTIVE'] == 'Y':
                    team = str(row['TEAM']).strip()
                    if team in MLB_TEAM_ABBR_TO_NAME:
                        # If the player is active and we have a team, add their ID under the full team name too
                        full_team = MLB_TEAM_ABBR_TO_NAME.get(team, team)
                        team_player_key = f"{player_name}_{full_team}"
                        cache['name_to_mlbid'][team_player_key] = mlbid
                
            except Exception as e:
                # Continue silently on error
                continue
                
    except Exception as e:
        # Fall back to the original MLB IDs file if PLAYERIDMAP.csv isn't available
        st.warning(f"Could not load PLAYERIDMAP.csv: {str(e)}. Using fallback mapping.")
    
    # If we have an mlb_ids_df, add its data to the cache as fallback
    if mlb_ids_df is not None:
        try:
            for _, row in mlb_ids_df.iterrows():
                try:
                    # Skip rows with missing MLBAMID
                    if pd.isna(row['MLBAMID']):
                        continue
                    
                    # Convert MLBAMID to integer and then to string to remove decimal places
                    try:
                        mlbamid = str(int(row['MLBAMID']))
                    except:
                        # If conversion fails, use as is but ensure no decimal places
                        mlbamid = str(row['MLBAMID']).split('.')[0].strip()
                    
                    # Try using the Name column
                    if 'Name' in row and not pd.isna(row['Name']):
                        name = normalize_name(row['Name'])
                        if name and name not in cache['name_to_mlbid']:
                            cache['name_to_mlbid'][name] = mlbamid
                    
                    # Add FantraxID if available
                    if 'FantraxID' in row and not pd.isna(row['FantraxID']):
                        fantrax_id = str(row['FantraxID']).strip()
                        if fantrax_id and fantrax_id not in cache['fantrax_to_mlbid']:
                            cache['fantrax_to_mlbid'][fantrax_id] = mlbamid
                            
                            # Also add without asterisks
                            clean_fantrax_id = fantrax_id.replace('*', '')
                            if clean_fantrax_id != fantrax_id:
                                cache['fantrax_to_mlbid'][clean_fantrax_id] = mlbamid
                    
                    # Use First and Last name if available
                    if not pd.isna(row['First']) and not pd.isna(row['Last']):
                        first = str(row['First']).strip()
                        last = str(row['Last']).strip()
                        
                        # First + Last format
                        full_name = normalize_name(f"{first} {last}")
                        if full_name and full_name not in cache['name_to_mlbid']:
                            cache['name_to_mlbid'][full_name] = mlbamid
                        
                        # Last, First format
                        alt_name = normalize_name(f"{last}, {first}")
                        if alt_name and alt_name not in cache['name_to_mlbid']:
                            cache['name_to_mlbid'][alt_name] = mlbamid

                except Exception as e:
                    # Continue silently on error
                    continue
        except Exception as e:
            # Continue silently on error
            pass
    
    return cache

def get_player_headshot_html(player_id, player_name, player_id_cache=None):
    """
    Generate player headshot HTML with a simplified approach
    """
    # Default image for missing headshots
    default_image = "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/generic/headshot/67/current"
    
    try:
        # Default to generic image
        mlb_id = "generic"
        
        if player_id_cache and player_id in player_id_cache.get('fantrax_to_mlbid', {}):
            mlb_id = player_id_cache['fantrax_to_mlbid'][player_id]
        elif player_id_cache and normalize_name(player_name) in player_id_cache.get('name_to_mlbid', {}):
            mlb_id = player_id_cache['name_to_mlbid'][normalize_name(player_name)]
            
        # Remove decimal part if present
        mlb_id = str(mlb_id).split('.')[0]
        
        # For simplicity, if we have a valid MLB ID, use it in the URL
        if mlb_id != "generic":
            img_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlb_id}/headshot/67/current"
        else:
            img_url = default_image
            
        # Return a very simple img tag
        return f'<img src="{img_url}" alt="{player_name}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">'
    except Exception:
        # Return default image if anything goes wrong
        return f'<img src="{default_image}" alt="{player_name}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">'

def get_mlb_team_info(team_name):
    """
    Get team colors and logo URL for an MLB team
    Handles different team name formats (abbreviation, full name, shorthand)
    """
    # Use the mapping dictionary to normalize team names
    team_name_normalized = team_name
    
    # Handle Athletics variations explicitly first (highest priority)
    if team_name in ["ATH", "OAK", "A's", "Athletics", "Oakland Athletics", "Las Vegas Athletics"]:
        team_name_normalized = "Athletics"
    # Special case handling for other problematic teams
    elif team_name in ["STL", "St. Louis Cardinals", "Cardinals"]:
        team_name_normalized = "Saint Louis Cardinals"
    # For other teams, try the general mapping
    elif team_name in MLB_TEAM_ABBR_TO_NAME:
        team_name_normalized = MLB_TEAM_ABBR_TO_NAME[team_name]
    
    # Try to get team colors with normalized name
    team_colors = MLB_TEAM_COLORS.get(team_name_normalized, None)
    
    # If that failed, try the original name
    if team_colors is None:
        team_colors = MLB_TEAM_COLORS.get(team_name, {'primary': '#1a1c23', 'secondary': '#2d2f36'})
    
    # Try to get team ID with normalized name
    team_id = MLB_TEAM_IDS.get(team_name_normalized, '')
    
    # If that failed, try the original name
    if team_id == '':
        team_id = MLB_TEAM_IDS.get(team_name, '')
    
    # Special case for Athletics since their ID might be different
    if team_name_normalized == "Athletics" and team_id == '':
        team_id = MLB_TEAM_IDS.get("Oakland Athletics", '')
    
    # Debug the team name mappings if needed
    #st.sidebar.write(f"Team: {team_name} → {team_name_normalized} → ID: {team_id}")
    
    # Generate the logo URL if we have a team ID
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""
    
    return {
        'colors': team_colors,
        'logo_url': logo_url
    }

def get_position_value(position_str, position_counts=None):
    """
    Calculate a position score based on the relative value and scarcity of the position.
    
    This function now heavily emphasizes positional scarcity while still considering
    the inherent defensive value of each position. Scarcity is calculated dynamically
    based on the actual distribution of players at each position.
    
    For players with multiple positions, we take the highest position value.
    """
    # Base positional values (defensive value/premium position)
    # These now account for 40% of the total position value (reduced from previous implementation)
    base_values = {
        'SP': 0.90,    # Starting pitchers are premium
        'C': 0.90,     # Catchers are premium defensive positions
        'SS': 0.85,    # Shortstops are premium defensive positions
        'CF': 0.80,    # Center fielders are premium defensive positions
        '2B': 0.75,    # Second basemen are moderately valuable
        '3B': 0.70,    # Third basemen are moderately valuable
        'RF': 0.65,    # Right fielders have moderate value
        'LF': 0.60,    # Left fielders have moderate value
        '1B': 0.55,    # First basemen have lower defensive value
        'UT': 0.50,    # Utility players have flexible value
        'RP': 0.40     # Relief pitchers have lower value
    }
    
    # Default scarcity values when position_counts is not available
    # Only used as fallback when we can't calculate actual scarcity
    default_scarcity = {
        'C': 0.85,     # Catchers are historically scarce
        'SS': 0.80,    # Shortstops are premium and scarce
        'SP': 0.75,    # Quality starting pitchers are scarce
        'CF': 0.70,    # Center fielders are moderately scarce
        '2B': 0.65,    # Second basemen are moderately scarce
        '3B': 0.60,    # Third basemen are moderately common
        'RF': 0.55,    # Right fielders are common
        'LF': 0.50,    # Left fielders are common
        '1B': 0.45,    # First basemen are very common
        'UT': 0.40,    # Utility players are common
        'RP': 0.35     # Relief pitchers are very common
    }
    
    # Calculate dynamic scarcity based on actual player counts (60% of position value)
    scarcity_values = default_scarcity.copy()  # Start with defaults
    
    if position_counts is not None and len(position_counts) > 0:
        # Get the count range for scaling
        min_count = min(position_counts.values()) 
        max_count = max(position_counts.values())
        count_range = max_count - min_count
        
        # Only recalculate if we have a meaningful distribution
        if count_range > 0:
            for pos in position_counts:
                if pos in scarcity_values:
                    count = position_counts[pos]
                    
                    # Normalize the count inversely (fewer players = higher scarcity)
                    # This creates a score from 0 to 1 where 1 = most scarce (fewest players)
                    normalized_scarcity = 1 - ((count - min_count) / count_range)
                    
                    # Apply a curve to emphasize differences in scarcity
                    # Squaring the value puts more emphasis on the most scarce positions
                    curved_scarcity = normalized_scarcity ** 1.5
                    
                    # Scale to a range from 0.3 to 1.0
                    scarcity_values[pos] = 0.3 + (curved_scarcity * 0.7)
    
    # Split by comma and get the list of positions
    positions = [pos.strip() for pos in position_str.split(',')]
    
    # Find the highest position value considering both base value and scarcity
    max_pos_value = 0
    for pos in positions:
        # Get component values with defaults if position not found
        base = base_values.get(pos, 0.5)  # Default to 0.5 if position not found
        scarcity = scarcity_values.get(pos, 0.4)  # Default scarcity
        
        # Weight the components: 40% base value, 60% scarcity
        total_value = (base * 0.4) + (scarcity * 0.6)
        
        max_pos_value = max(max_pos_value, total_value)
    
    # Cap at 1.0 to ensure we stay within scale
    return min(max_pos_value, 1.0)

def calculate_mvp_score(player_row, weights, norm_columns, position_counts=None):
    """
    Calculate MVP score based on the weighted normalized values
    
    Now includes position value in the calculation that accounts for positional scarcity
    Age component has been removed as requested and its weight was added to FPts
    """
    score = 0
    for col, weight in weights.items():
        if col in norm_columns and col != 'Position':  # Skip Position as we're handling it separately
            score += norm_columns[col][player_row.name] * weight
    
    # Add position value to the score, accounting for positional scarcity
    if 'Position' in player_row and weights.get('Position', 0) > 0:
        position_score = get_position_value(player_row['Position'], position_counts)
        score += position_score * weights.get('Position', 0)
    
    return score

def render():
    """Render the MVP Race page"""
    # Add enhanced CSS for hover effects
    st.markdown("""
    <style>
    /* MVP Favorites Cards Hover Effect */
    .player-card-top:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.4) !important;
        transition: all 0.3s ease-in-out !important;
    }
    
    /* Complete Player Rankings Styles and Effects */
    .player-card-container {
        transition: all 0.3s ease-in-out !important;
        cursor: pointer !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        border: 2px solid rgba(255,255,255,0.1) !important;
        margin-bottom: 16px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    /* Add a subtle divider between cards */
    .player-card-container::after {
        content: "";
        position: absolute;
        bottom: -8px;
        left: 10%;
        width: 80%;
        height: 1px;
        background: rgba(255,255,255,0.1);
    }
    
    /* Hover effects */
    .player-card-container:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5) !important;
        border-color: rgba(255,215,0,0.3) !important;
    }
    
    /* Player name hover effect */
    .player-card-container:hover .player-name {
        color: gold !important;
        text-shadow: 0 0 5px rgba(255,215,0,0.5) !important;
    }
    
    /* MVP score bar hover effect */
    .player-card-container:hover .mvp-score-bar {
        background: linear-gradient(90deg, gold, #ffcc00) !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
    }
    
    /* Reveal animation as you scroll */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Base animation for all cards with staggered delays */
    .player-card-container {
        opacity: 0;
        animation: fadeInUp 0.5s ease-out forwards;
    }
    
    /* Staggered animation delays for player cards */
    .player-card-container:nth-child(1) { animation-delay: 0.05s; }
    .player-card-container:nth-child(2) { animation-delay: 0.1s; }
    .player-card-container:nth-child(3) { animation-delay: 0.15s; }
    .player-card-container:nth-child(4) { animation-delay: 0.2s; }
    .player-card-container:nth-child(5) { animation-delay: 0.25s; }
    .player-card-container:nth-child(6) { animation-delay: 0.3s; }
    .player-card-container:nth-child(7) { animation-delay: 0.35s; }
    .player-card-container:nth-child(8) { animation-delay: 0.4s; }
    .player-card-container:nth-child(9) { animation-delay: 0.45s; }
    .player-card-container:nth-child(10) { animation-delay: 0.5s; }
    
    /* For cards beyond 10, we'll use a formula based on their position */
    .player-card-container:nth-child(n+11) { 
        animation-delay: calc(0.5s + (var(--index, 0) * 0.05s)); 
    }
    </style>
    """, unsafe_allow_html=True)
    
    # TEST SECTION - Uncomment to debug HTML rendering
    with st.expander("HTML Test Section"):
        st.markdown("### Testing HTML Rendering")
        
        # Test simple container
        html_code = """
        <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center; width: 100%; margin-top: 0.5rem;">
            <p style="margin: 0; color: white;">MVP Score: 82.1</p>
        </div>
        """
        st.markdown("#### Simple HTML Container:")
        st.markdown(html_code, unsafe_allow_html=True)
        
        # Test complex card
        card_html = """
        <div style="
            background: linear-gradient(135deg, #4a0072 0%, #9c0063 100%);
            border-radius: 10px;
            padding: 1rem;
            position: relative;
            overflow: hidden;
            margin-bottom: 15px;
        ">
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 0.5rem;">
                <h3 style="color: white; margin: 0.5rem 0; text-align: center;">Test Player</h3>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.3rem;">SP | LAD</div>
                <div style="margin: 0.5rem 0; color: gold; font-size: 1.2rem;">⭐⭐⭐⭐</div>
                <div style="color: white; background: rgba(0,0,0,0.3); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.9rem; margin-bottom: 0.5rem;">
                    <b>MVP Score:</b> 82.1
                </div>
                
                <div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center; width: 100%; margin-top: 0.5rem;">
                    <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">Contract</div>
                    <div style="color: white; font-weight: bold;">2035</div>
                </div>
            </div>
        </div>
        """
        st.markdown("#### Complex Player Card HTML:")
        st.markdown(card_html, unsafe_allow_html=True)
    
    st.title("🏆 MVP Race Tracker")
    
    st.write("""
    ## Armchair Baseball League Most Valuable Player
    
    This tool analyzes player performance, value, and impact to determine the MVP race leaders.
    Each player is evaluated based on their performance (FPts), position value, and overall team value.
    
    ### MVP Score Components:
    - **FPts (65%)**: Fantasy points scoring is the primary performance metric
    - **Position (5%)**: Position value with SP, C, and SS being the most valuable positions
    - **Value (30%)**: Combined measure of salary and contract length
        - Low salary, long-term contracts are most valuable
        - Young players (under 26) on 1st contracts receive a bonus
        - Contract length provides more value for lower-salaried players
    """)
    
    # Load MLB player IDs and create cache for headshots
    player_id_cache = {}
    try:
        mlb_ids_df = pd.read_csv("attached_assets/mlb_player_ids-2.csv")
        player_id_cache = create_player_id_cache(mlb_ids_df)
    except Exception as e:
        st.warning(f"Could not load MLB player IDs: {str(e)}")
    
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
        
        # Calculate value score that combines salary and contract
        def calculate_value_score(salary, contract, age):
            # Base salary score (lower is better)
            salary_score = 1.0 - (salary / mvp_data['Salary'].max())
            
            # Contract length base values
            contract_values = {
                '2050': 1.0,
                '2045': 0.9,
                '2040': 0.8,
                '2035': 0.7,
                '2029': 0.6,
                '2028': 0.5,
                '2027': 0.4,
                '2026': 0.3,
                '2025': 0.2,
                '1st': 0.15  # Base value for 1st contracts
            }
            
            # Get base contract value
            contract_value = contract_values.get(contract, 0.1)
            
            # Special handling for 1st contracts of young players
            if contract == '1st' and age < 26:
                contract_value += 0.3  # Significant boost for young 1st contracts
            
            # Salary tiers affect contract multiplier
            if salary < 5:  # Low salary players
                contract_multiplier = 1.5  # Better contract multiplier for low salary
            elif salary < 10:  # Mid salary players
                contract_multiplier = 1.2
            else:  # High salary players
                contract_multiplier = 1.0
            
            # Calculate final value score
            value_score = (salary_score * 0.6) + (contract_value * contract_multiplier * 0.4)
            
            return min(1.0, value_score)  # Cap at 1.0

        # Add Value score to normalized columns
        norm_columns['Value'] = mvp_data.apply(
            lambda x: calculate_value_score(x['Salary'], x['Contract'], x['Age']), 
            axis=1
        )

        # Define weights for MVP criteria (sum should be 1.0)
        default_weights = {
            'FPts': 0.65,      # Performance is still primary factor
            'Position': 0.05,  # Position value remains same
            'Value': 0.30,    # Combined salary and contract value
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
        
        # For metrics where higher is better (FPts)
        for col in ['FPts']:
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
        
        # For Position (calculate based on position value function)
        norm_columns['Position'] = mvp_data['Position'].apply(get_position_value)
        
        # Apply filters if selected
        filtered_data = mvp_data.copy()
        
        if selected_position != "All Positions":
            # Filter by position (check if the selected position is in the comma-separated list)
            filtered_data = filtered_data[filtered_data['Position'].str.contains(selected_position)]
            
        if selected_team != "All Teams":
            # Filter by team
            filtered_data = filtered_data[filtered_data['Team'] == selected_team]
        
        # Calculate position counts for scarcity analysis
        position_counts = {}
        for pos_list in mvp_data['Position'].str.split(','):
            for pos in pos_list:
                pos = pos.strip()
                if pos in position_counts:
                    position_counts[pos] += 1
                else:
                    position_counts[pos] = 1
        
        # Debug position counts
        #st.sidebar.write("Position Counts:", position_counts)
        
        # Calculate MVP score for each player
        mvp_scores = []
        
        for idx, row in filtered_data.iterrows():
            score = calculate_mvp_score(row, weights, norm_columns, position_counts)
            mvp_scores.append(score)
        
        filtered_data['MVP_Score_Raw'] = mvp_scores
        
        # Scale the MVP scores to a 0-100 scale for better user understanding
        max_score = max(mvp_scores)
        min_score = min(mvp_scores)
        score_range = max_score - min_score
        
        # Scale scores to 0-100 range and round to 1 decimal place
        if score_range > 0:
            filtered_data['MVP_Score'] = ((filtered_data['MVP_Score_Raw'] - min_score) / score_range * 100).round(1)
        else:
            filtered_data['MVP_Score'] = 50.0  # Default if all scores are the same
        
        # Sort by MVP score in descending order
        filtered_data = filtered_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
        
        # Top 3 MVP candidates with special highlighting
        st.write("## Current MVP Favorites")
        
        # Display top 3 stacked vertically
        for i, (_, player) in enumerate(filtered_data.head(3).iterrows()):
            team_info = get_mlb_team_info(player['Team'])
            colors = team_info['colors']
            logo_url = team_info['logo_url']
            
            # Calculate stars based on MVP score (1-5 stars) using 0-100 scale
            # Scores above 80 get 5 stars, above 60 get 4 stars, etc.
            star_score = player['MVP_Score'] / 20  # Convert 0-100 scale to 0-5 scale
            stars = min(5, max(1, int(star_score + 0.5)))  # Round to nearest star, minimum 1, maximum 5
            stars_display = "⭐" * stars
            
            # Create a more native implementation with less complex HTML
            col1, col2, col3 = st.columns([1, 10, 1])
            
            with col2:
                # Create a container with custom styling
                with st.container():
                    # Apply CSS for the container background
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        border-radius: 10px;
                        padding: 1rem;
                        position: relative;
                        text-align: center;
                        margin-bottom: 15px;
                    ">
                        <div style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.1); padding: 5px; border-radius: 5px;">
                            <span style="color: white; font-size: 0.8rem;">#{i+1}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Player headshot (simple version)
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: -60px;">
                        {get_player_headshot_html(player['ID'], player['Player'], player_id_cache).replace('width: 60px; height: 60px;', 'width: 120px; height: 120px; border: 3px solid white;')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Player info
                    st.markdown(f"""
                    <h3 style="color: white; margin: 0.5rem 0; text-align: center;">{player['Player']}</h3>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.3rem; text-align: center;">{player['Position']} | {player['Team']}</div>
                    """, unsafe_allow_html=True)
                    
                    # Star rating
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0; color: gold; font-size: 1.2rem; text-align: center;">{stars_display}</div>
                    """, unsafe_allow_html=True)
                    
                    # MVP Score 
                    st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.3); padding: 0.3rem; border-radius: 12px; margin: 0 auto; width: 60%; text-align: center;">
                        <span style="color: white; font-weight: bold;">MVP Score: {player['MVP_Score']:.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Removed Contract display as requested
        
        # MVP Race Complete Rankings Table
        st.write("## Complete MVP Rankings")
        
        # Create tabs for different views of the data
        tab1, tab2, tab3 = st.tabs(["Player Cards", "Performance Breakdown", "Value Analysis"])
        
        with tab1:
            # Grid view of player cards
            st.write("### Complete Player Rankings")
            
            # Get total number of players to display
            num_display = min(50, len(filtered_data))
            display_data = filtered_data.head(num_display)
            
            # Filter option
            display_count = st.slider("Number of players to display", 10, 100, 30, 5)
            display_data = filtered_data.head(display_count)
            
            # Instead of using a grid, stack the cards vertically
            for i, (_, player) in enumerate(display_data.iterrows()):
                rank = i + 1
                team_info = get_mlb_team_info(player['Team'])
                colors = team_info['colors']
                
                # MVP score is already on a 0-100 scale, use directly for progress bar
                mvp_score_pct = int(player['MVP_Score'])
                
                # Make star rating based on MVP score using 0-100 scale
                # Scores above 80 get 5 stars, above 60 get 4 stars, etc.
                star_score = player['MVP_Score'] / 20  # Convert 0-100 scale to 0-5 scale
                stars = min(5, max(1, int(star_score + 0.5)))  # Round to nearest star, minimum 1, maximum 5
                stars_display = "⭐" * stars
                # Create mini card container with simplified HTML in smaller chunks
                with st.container():
                    # Background container and rank with added class for hover effects
                    st.markdown(f"""
                    <div class="player-card-container" style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        border-radius: 12px;
                        padding: 1rem;
                        margin-bottom: 20px;
                        position: relative;
                        min-height: 80px;
                        border: 2px solid rgba(255,255,255,0.1);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                        backdrop-filter: blur(5px);
                    ">
                        <div style="position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 12px;">
                            <span style="color: white; font-weight: bold;">#{rank}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Player header with image and name
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            {get_player_headshot_html(player['ID'], player['Player'], player_id_cache).replace('width: 60px; height: 60px;', 'width: 40px; height: 40px; border: 2px solid white;')}
                            <div style="margin-left: 0.5rem;">
                                <div class="player-name" style="color: white; font-weight: bold; font-size: 0.9rem; line-height: 1;">{player['Player']}</div>
                                <div style="color: rgba(255,255,255,0.8); font-size: 0.7rem;">{player['Position']} | {player['Team']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # First row of stats (FPts and Age)
                    st.markdown(f"""
                        <div style="display: flex; gap: 0.4rem; margin: 0.4rem 0;">
                            <div style="flex: 1; background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">FPts</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['FPts']:.1f}</div>
                            </div>
                            <div style="flex: 1; background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Age</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['Age']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Second row of stats (Salary and Contract)
                    st.markdown(f"""
                        <div style="display: flex; gap: 0.4rem; margin: 0.4rem 0;">
                            <div style="flex: 1; background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Salary</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">${player['Salary']}</div>
                            </div>
                            <div style="flex: 1; background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Contract</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['Contract']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # MVP Score with progress bar
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.2); padding: 0.4rem; border-radius: 4px; margin-top: 0.4rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">MVP Score: <span style="color: white; font-weight: bold;">{player['MVP_Score']:.1f}</span></div>
                                <div style="color: gold; font-size: 0.7rem;">{stars_display}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Progress bar for MVP score
                    st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.1); border-radius: 3px; height: 6px; margin-top: 0.2rem;">
                            <div class="mvp-score-bar" style="height: 6px; background: gold; border-radius: 3px; width: {mvp_score_pct}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab2:
            # Radar chart for performance breakdown
            st.write("### MVP Candidates Performance Breakdown")
            
            # Position Scarcity Analysis
            st.write("#### Position Value Breakdown")
            st.markdown("""
            The **Position** component (5% of MVP score) now heavily emphasizes positional scarcity.
            It's calculated using two factors:
            - **Base Value (40%)**: The inherent defensive value of a position
            - **Scarcity (60%)**: The rarity of players at each position
            """)
            
            # Create a visualization of position scarcity
            if position_counts and len(position_counts) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Display the player counts by position in a bar chart
                    positions = list(position_counts.keys())
                    counts = list(position_counts.values())
                    position_df = pd.DataFrame({
                        'Position': positions,
                        'Player Count': counts
                    })
                    
                    position_df = position_df.sort_values('Player Count')
                    fig = px.bar(
                        position_df, 
                        x='Position', 
                        y='Player Count',
                        title='Player Distribution by Position (Lower Count = Higher Scarcity)',
                        color='Player Count',
                        color_continuous_scale=px.colors.sequential.Viridis_r,  # Reversed so lower count is brighter
                        height=300
                    )
                    fig.update_layout(
                        xaxis_title="Position",
                        yaxis_title="Number of Players",
                        template="plotly_dark",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Calculate and display the position values
                    position_values = {}
                    for pos in positions:
                        position_values[pos] = get_position_value(pos, position_counts)
                    
                    value_df = pd.DataFrame({
                        'Position': list(position_values.keys()),
                        'Position Value': list(position_values.values())
                    })
                    value_df = value_df.sort_values('Position Value', ascending=False)
                    
                    st.markdown("##### Position Value Ranking")
                    st.table(value_df.set_index('Position').style.format({'Position Value': '{:.2f}'}))
            else:
                st.info("Position data not available for scarcity analysis.")
            
            # Allow user to select players to compare
            st.write("#### Player Attribute Comparison")
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