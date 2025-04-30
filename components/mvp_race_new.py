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
    Generate player headshot HTML with simplified approach using only the most reliable URL format
    Uses the comprehensive player ID mapping system to find the right MLB ID
    """
    try:
        # Default fallback MLBAMID for missing headshots
        fallback_mlbamid = "805805"

        # Get MLB ID using our mapping system
        mlb_id = fallback_mlbamid

        if player_id_cache:
            # First try direct Fantrax ID to MLB ID mapping (most reliable)
            if 'fantrax_to_mlbid' in player_id_cache:
                # Try with asterisks
                if player_id in player_id_cache['fantrax_to_mlbid']:
                    mlb_id = player_id_cache['fantrax_to_mlbid'][player_id]
                # Try without asterisks
                else:
                    clean_fantrax_id = str(player_id).replace('*', '')
                    if clean_fantrax_id in player_id_cache['fantrax_to_mlbid']:
                        mlb_id = player_id_cache['fantrax_to_mlbid'][clean_fantrax_id]

            # If we couldn't find by Fantrax ID, try by player name
            if mlb_id == fallback_mlbamid and 'name_to_mlbid' in player_id_cache and player_name:
                norm_name = normalize_name(player_name)

                # Try direct name match
                if norm_name in player_id_cache['name_to_mlbid']:
                    mlb_id = player_id_cache['name_to_mlbid'][norm_name]
                # Try last name only
                elif ' ' in player_name:
                    last_name = normalize_name(player_name.split(' ')[-1])
                    if last_name in player_id_cache['name_to_mlbid']:
                        mlb_id = player_id_cache['name_to_mlbid'][last_name]

                # Try without "Jr." suffix
                if (mlb_id == fallback_mlbamid and 
                    ("Jr." in player_name or "Jr" in player_name or "II" in player_name)):
                    base_name = player_name
                    base_name = base_name.replace(" Jr.", "").replace(" Jr", "")
                    base_name = base_name.replace(" II", "").replace(" III", "")
                    if normalize_name(base_name) in player_id_cache['name_to_mlbid']:
                        mlb_id = player_id_cache['name_to_mlbid'][normalize_name(base_name)]

        # Ensure MLB ID has no decimal point and is properly formatted as 6-digit number
        if mlb_id != fallback_mlbamid:
            try:
                # Convert to int and then back to string to remove any decimals
                mlb_id = str(int(float(mlb_id)))
            except:
                # If conversion fails, use as is but strip any decimal part
                mlb_id = str(mlb_id).split('.')[0].strip()

        # Use the specific URL format we know works
        player_image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlb_id}/headshot/67/current"

        # Create HTML for the image
        img_html = f'<img src="{player_image_url}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" alt="{player_name} headshot">'

        return img_html
    except Exception as e:
        # Return fallback image if there's any error
        return f"""<img src="https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/805805/headshot/67/current" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" alt="Default headshot">"""

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

    # Generate the logo URL if we have a team ID
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

    return {
        'colors': team_colors,
        'logo_url': logo_url
    }

def get_position_value(position_str, position_counts=None):
    """
    Calculate a position score based on the relative value and scarcity of the position.

    This function now balances two factors:
    1. The inherent defensive value of each position
    2. The positional scarcity based on counts of players at each position

    For players with multiple positions, we take the highest position value.
    """
    # Base positional values (defensive value/premium position)
    base_values = {
        'SP': 0.90,
        'C': 0.90,
        'SS': 0.85,
        'CF': 0.80,
        '2B': 0.75,
        '3B': 0.70,
        'RF': 0.65,
        'LF': 0.60,
        '1B': 0.55,
        'UT': 0.50,
        'RP': 0.40
    }

    # Default scarcity bonus - how rare the position is in general
    scarcity_bonus = {
        'C': 0.10,     # Catchers are rare and valuable
        'SP': 0.05,    # Top starting pitchers are valuable
        'SS': 0.05,    # Shortstops are premium
        'CF': 0.05,    # Center fielders are premium
        '2B': 0.05,    # Second basemen are moderately rare
        '3B': 0.05,    # Third basemen are moderately rare
        'RF': 0.05,    # Right fielders get slight bonus
        'LF': 0.05,    # Left fielders get slight bonus
        '1B': 0.05,    # First basemen are common but still get value
        'UT': 0.05,    # Utility players offer flexibility
        'RP': 0.05     # Relief pitchers are common but still get value
    }

    # Calculate dynamic position value based on player counts at each position
    if position_counts is not None:
        # Calculate max count for normalization
        max_count = max(position_counts.values()) if position_counts else 1
        
        # Update scarcity bonus based on position counts
        for pos in position_counts:
            if pos in scarcity_bonus:
                # Calculate normalized scarcity (rarer positions get higher bonus)
                count = position_counts[pos]
                normalized_scarcity = 1 - (count / max_count) if max_count > 0 else 0
                # Scale to a reasonable bonus range (0-0.2)
                scarcity_bonus[pos] = normalized_scarcity * 0.2

    # If position_str is a string, process it
    if isinstance(position_str, str):
        # Handle multi-position players (e.g., "SS/2B", "LF/RF", etc.)
        positions = position_str.split('/')
        
        # Calculate value for each position and take the highest
        values = []
        for pos in positions:
            pos = pos.strip()
            base_value = base_values.get(pos, 0.4)  # Default to 0.4 if unknown
            pos_scarcity = scarcity_bonus.get(pos, 0.0)
            values.append(base_value + pos_scarcity)
        
        # Return the highest position value
        return max(values) if values else 0.4
    else:
        # If position_str is not a string (e.g., NaN), return default value
        return 0.4

def calculate_mvp_score(player_row, weights, norm_columns, position_counts=None):
    """
    Calculate MVP score based on the weighted normalized values

    Now includes position value in the calculation that accounts for positional scarcity
    """
    score = 0.0
    
    # Add up all weighted components
    for component, weight in weights.items():
        if component in norm_columns:
            component_score = norm_columns[component][player_row.name] * weight
            score += component_score
    
    return score

def render():
    """Render the MVP Race page"""
    st.title("Armchair Baseball League Most Valuable Player")
    
    st.write("""
    The MVP race evaluates player value based on Fantasy Points, Salary, Contract, Age, and Position.
    Players are scored on a 0-100 scale combining these factors with appropriate weighting.
    """)
    
    # Attempt to load the data
    try:
        # Load player data
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        # Load MLB IDs data for player headshots
        mlb_ids_df = None
        try:
            mlb_ids_df = pd.read_csv("attached_assets/mlb_player_ids-2.csv")
        except:
            try:
                mlb_ids_df = pd.read_csv("attached_assets/mlb_player_ids.csv")
            except:
                st.warning("Could not load MLB player IDs file. Player headshots may not display correctly.")
        
        # Create player ID cache for headshot lookups
        player_id_cache = create_player_id_cache(mlb_ids_df)
        
        # Basic data cleaning
        mvp_data = mvp_data.dropna(subset=['Player', 'FPts'])
        
        # Ensure FPts and FP/G are numeric and handle any formatting issues
        for col in ['FPts', 'FP/G', 'Salary', 'Age']:
            try:
                # Remove any non-numeric characters for Salary
                if col == 'Salary':
                    mvp_data[col] = mvp_data[col].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                
                mvp_data[col] = pd.to_numeric(mvp_data[col], errors='coerce')
            except Exception as e:
                st.error(f"Error converting {col} column to numeric: {str(e)}")
        
        # Fill missing values
        mvp_data = mvp_data.fillna({
            'FPts': 0,
            'FP/G': 0,
            'Salary': 0,
            'Age': 25,  # Default age
            'Contract': '1st',  # Default contract
            'Position': 'UT',  # Default position
            'Team': 'Unknown'  # Default team
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
        
        # Position filter (multi-select)
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
        
        # Team filter (multi-select)
        all_teams = sorted(mvp_data['Team'].dropna().unique())
        selected_teams = st.sidebar.multiselect(
            "Filter by Team",
            all_teams,
            default=[]
        )
        
        # Contract filter (multi-select)
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
        
        # Allow user to adjust component weights
        st.sidebar.header("MVP Score Weights")
        st.sidebar.write("Adjust the weights of different components in the MVP calculation:")
        
        # Default weights
        default_weights = {
            'Fantasy Points': 0.50,
            'Salary': 0.20,
            'Contract': 0.10,
            'Age': 0.10,
            'Position': 0.10
        }
        
        # Let user adjust weights with sliders
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
        
        # Normalize Fantasy Points (higher is better)
        if len(filtered_data) > 0:
            max_fpts = filtered_data['FPts'].max()
            min_fpts = filtered_data['FPts'].min()
            norm_columns['Fantasy Points'] = filtered_data['FPts'].apply(
                lambda x: normalize_value(x, min_fpts, max_fpts, reverse=False)
            )
        
            # Normalize Salary (lower is better)
            max_salary = filtered_data['Salary'].max()
            min_salary = filtered_data['Salary'].min()
            norm_columns['Salary'] = filtered_data['Salary'].apply(
                lambda x: normalize_value(x, min_salary, max_salary, reverse=True)
            )
            
            # Normalize Age (lower is better, but with a sweet spot)
            # Scale: 0-0.5 for >30, 0.5-1 for <28, with 24-27 being optimal
            norm_columns['Age'] = filtered_data['Age'].apply(
                lambda age: 1.0 if 24 <= age <= 27 else
                           0.8 if 28 <= age <= 29 else
                           0.6 if 30 <= age <= 31 else
                           0.4 if 32 <= age <= 33 else
                           0.2 if 34 <= age <= 35 else
                           0.1
            )
            
            # Normalize Contract (longer/better is higher)
            norm_columns['Contract'] = filtered_data['Contract'].apply(get_contract_score)
            
            # Calculate and normalize Position value
            norm_columns['Position'] = filtered_data['Position'].apply(
                lambda x: get_position_value(x, position_counts)
            )
            
            # Calculate MVP scores
            mvp_scores = []
            for _, row in filtered_data.iterrows():
                score = calculate_mvp_score(row, weights, norm_columns, position_counts)
                mvp_scores.append(score)
            
            filtered_data['MVP_Score'] = mvp_scores
            
            # Sort by MVP score in descending order
            filtered_data = filtered_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
            
            # Top 3 MVP candidates with special highlighting
            st.write("## Current MVP Favorites")
            
            # Display top 3 in a row
            cols = st.columns(3)
            
            # Use a simpler approach with limited HTML and more native Streamlit components
            for i, (_, player) in enumerate(filtered_data.head(3).iterrows()):
                with cols[i]:
                    team_info = get_mlb_team_info(player['Team'])
                    colors = team_info['colors']
                    
                    # Calculate stars based on MVP score (1-5 stars)
                    stars = min(5, max(1, int(player['MVP_Score'] * 5 + 0.5)))
                    stars_display = "⭐" * stars
                    
                    # Calculate MVP score as percentage (0-100)
                    mvp_score_display = int(player['MVP_Score'] * 100)
                    
                    # Create a container with background color
                    st.markdown(
                        f"""
                        <div style="
                            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                            border-radius: 10px;
                            padding: 15px;
                            color: white;
                            text-align: center;
                            margin-bottom: 10px;
                        ">
                            <div style="font-size: 1.2rem; font-weight: bold">#{i+1}</div>
                            <div style="margin: 10px 0;">
                                {get_player_headshot_html(player['ID'], player['Player'], player_id_cache).replace('width: 60px; height: 60px;', 'width: 100px; height: 100px; border: 3px solid white;')}
                            </div>
                            <h4 style="margin: 5px 0;">{player['Player']}</h4>
                            <div style="opacity: 0.8; margin-bottom: 10px;">{player['Position']} | {player['Team']}</div>
                            <div style="color: gold; margin: 5px 0;">{stars_display}</div>
                            <div style="font-weight: bold; margin-bottom: 5px;">MVP Score: {mvp_score_display}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Use native Streamlit components for the stats
                    st.markdown("<h5 style='text-align: center; margin: 0;'>Player Stats</h5>", unsafe_allow_html=True)
                    
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
                    
                    st.metric("Contract", f"{player['Contract']}")
            
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
                    
                    # Calculate MVP score as percentage (capped at 100%)
                    mvp_score_pct = min(100, int(player['MVP_Score'] * 100))
                    
                    # Make star rating based on MVP score
                    stars = min(5, max(1, int(player['MVP_Score'] * 5 + 0.5)))
                    stars_display = "⭐" * stars
                    # Create condensed player card with string variable to ensure all tags are properly closed
                    card_html = f"""
                    <div style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        border-radius: 8px;
                        padding: 0.8rem;
                        margin-bottom: 0.8rem;
                        position: relative;
                        min-height: 80px;
                        border: 1px solid rgba(255,255,255,0.1);
                        width: 100%;
                        box-sizing: border-box;
                    ">
                        <div style="position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 12px;">
                            <span style="color: white; font-weight: bold;">#{rank}</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            {get_player_headshot_html(player['ID'], player['Player'], player_id_cache).replace('width: 60px; height: 60px;', 'width: 40px; height: 40px; border: 2px solid white;')}
                            <div style="margin-left: 0.5rem;">
                                <div style="color: white; font-weight: bold; font-size: 0.9rem; line-height: 1;">{player['Player']}</div>
                                <div style="color: rgba(255,255,255,0.8); font-size: 0.7rem;">{player['Position']} | {player['Team']}</div>
                            </div>
                        </div>
                        <div style="
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 0.4rem;
                            margin: 0.4rem 0;
                        ">
                            <div style="background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">FPts</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['FPts']:.1f}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Age</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['Age']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Salary</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">${player['Salary']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.25rem; border-radius: 4px; text-align: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.65rem;">Contract</div>
                                <div style="color: white; font-weight: bold; font-size: 0.8rem;">{player['Contract']}</div>
                            </div>
                        </div>
                        <div style="background: rgba(0,0,0,0.2); padding: 0.4rem; border-radius: 4px; margin-top: 0.4rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="color: rgba(255,255,255,0.7); font-size: 0.7rem;">MVP Score: <span style="color: white; font-weight: bold;">{mvp_score_pct}</span></div>
                                <div style="color: gold; font-size: 0.7rem;">{stars_display}</div>
                            </div>
                            <div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; margin-top: 0.2rem;">
                                <div style="height: 6px; background: gold; border-radius: 3px; width: {mvp_score_pct}%;"></div>
                            </div>
                        </div>
                    </div>
                    """
                    
                    # Display the player card
                    st.markdown(card_html, unsafe_allow_html=True)
            
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
                    x=avg_salary * 1.5,
                    y=avg_fpts * 1.5,
                    text="High Value, High Cost",
                    showarrow=False,
                    font=dict(size=12, color="white")
                )
                
                fig.add_annotation(
                    x=avg_salary * 0.5,
                    y=avg_fpts * 1.5,
                    text="High Value, Low Cost<br>Bargains",
                    showarrow=False,
                    font=dict(size=12, color="gold")
                )
                
                fig.add_annotation(
                    x=avg_salary/2,
                    y=avg_fpts/2,
                    text="Low Value, Low Cost",
                    showarrow=False,
                    font=dict(size=12, color="white")
                )
                
                fig.add_annotation(
                    x=avg_salary * 1.5,
                    y=avg_fpts/2,
                    text="Low Value, High Cost<br>Overpaid",
                    showarrow=False,
                    font=dict(size=12, color="red")
                )
                
                # Customize layout
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0.1)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
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