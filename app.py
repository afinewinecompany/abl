import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
from components import league_info, rosters, standings, power_rankings, prospects, transactions, ddi, mvp_race_new as mvp_race, dump_deadline
# Projected Rankings completely removed as it's no longer relevant for this season
from utils import (
    fetch_api_data, 
    save_power_rankings_data, 
    load_power_rankings_data, 
    save_weekly_results, 
    load_weekly_results,
    save_rankings_history,
    load_rankings_history,
    create_ranking_trend_chart,
    should_take_weekly_snapshot
)

# This must be the first Streamlit command
st.set_page_config(
    page_title="ABL Analytics Dashboard",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add baseball particles animation
st.markdown("""
    <style>
    .stApp {
        background: rgba(26, 28, 35, 0.95);
        backdrop-filter: blur(5px);
    }
    #tsparticles {
        position: fixed;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: -1;
    }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.9.3/tsparticles.bundle.min.js"></script>
    <div id="tsparticles"></div>
    <script>
    window.addEventListener('DOMContentLoaded', (event) => {
        tsParticles.load("tsparticles", {
            fpsLimit: 60,
            particles: {
                number: {
                    value: 40,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: ["#ffffff"]
                },
                shape: {
                    type: "circle"
                },
                opacity: {
                    value: 0.25,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 5,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 2,
                        size_min: 1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: "#ffffff",
                    opacity: 0.1,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: "none",
                    random: true,
                    straight: false,
                    out_mode: "bounce",
                    bounce: true,
                    attract: {
                        enable: true,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: "window",
                events: {
                    onhover: {
                        enable: true,
                        mode: ["grab", "bubble", "repulse"]
                    },
                    onclick: {
                        enable: true,
                        mode: "push"
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 200,
                        line_linked: {
                            opacity: 0.3
                        }
                    },
                    bubble: {
                        distance: 300,
                        size: 12,
                        duration: 2,
                        opacity: 0.2,
                        speed: 2
                    },
                    repulse: {
                        distance: 150,
                        duration: 0.4
                    },
                    push: {
                        particles_nb: 4
                    },
                    attract: {
                        distance: 200,
                        duration: 0.4,
                        factor: 5
                    }
                }
            },
            retina_detect: true,
            background: {
                color: "transparent",
                position: "50% 50%",
                repeat: "no-repeat",
                size: "cover"
            }
        });
    });
    </script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        padding: 1rem 2rem;
        background: rgba(14, 17, 23, 0.8);
    }

    /* Mobile-first approach */
    @media screen and (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }

        h1 {
            font-size: 1.8em !important;
            padding: 1rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap;
            gap: 0.5rem !important;
            padding: 0.5rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            min-width: 100px !important;
            padding: 0 1rem !important;
            height: 3rem !important;
            font-size: 0.9rem !important;
        }

        .stMetric {
            padding: 1rem !important;
        }

        /* Make data tables scrollable horizontally */
        .stDataFrame {
            max-width: 100%;
            overflow-x: auto;
            padding: 1rem !important;
        }

        /* Adjust column sizes for mobile */
        [data-testid="stDataFrameResizable"] td {
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
            white-space: nowrap;
        }

        [data-testid="stDataFrameResizable"] th {
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
            white-space: nowrap;
        }

        /* Adjust chart containers */
        [data-testid="stArrowVegaLiteChart"] {
            width: 100% !important;
            padding: 0 !important;
        }
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: #1a1c23;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(30, 100, 255, 0.15);
        border: 1px solid rgba(30, 100, 255, 0.1);
        display: flex;
        justify-content: center;
        width: 100%;
        margin: 0 auto 2rem auto;
    }

    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        color: #fafafa;
        border-radius: 8px;
        padding: 0 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 140px;
        text-align: center;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ff3030;
        text-shadow: 0 0 10px rgba(255, 30, 30, 0.5);
        background: rgba(255, 30, 30, 0.1);
    }

    /* Tab list container */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
        justify-content: center;
    }

    /* Active tab indicator */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ff3030;
        background: rgba(255, 30, 30, 0.1);
        box-shadow: 0 0 15px rgba(255, 30, 30, 0.2);
    }

    h1 {
        color: #ffffff;
        text-align: center;
        padding: 2rem;
        margin-bottom: 2rem;
        font-size: 2.8em;
        font-weight: 700;
        letter-spacing: -1px;
        text-shadow: 
            0 0 10px rgba(255, 30, 30, 0.6),
            0 0 20px rgba(30, 100, 255, 0.6);
        background: linear-gradient(180deg, #1a1c23 0%, rgba(26, 28, 35, 0.8) 100%);
        border-radius: 16px;
        border: 1px solid rgba(255, 30, 30, 0.2);
        box-shadow: 
            0 0 20px rgba(30, 100, 255, 0.2),
            inset 0 0 50px rgba(255, 30, 30, 0.05);
    }

    .stMetric {
        background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.9) 100%);
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid rgba(30, 100, 255, 0.1);
        box-shadow: 
            0 0 20px rgba(30, 100, 255, 0.15),
            inset 0 0 30px rgba(255, 30, 30, 0.03);
        transition: all 0.3s ease;
    }

    .stMetric:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 
            0 0 30px rgba(30, 100, 255, 0.25),
            inset 0 0 30px rgba(255, 30, 30, 0.05);
    }

    .stDataFrame {
        background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.95) 100%);
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 30, 30, 0.1);
        box-shadow: 
            0 0 25px rgba(30, 100, 255, 0.15),
            inset 0 0 40px rgba(255, 30, 30, 0.03);
        margin-bottom: 1.5rem;
    }

    .css-1d391kg {  /* Streamlit containers */
        background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.9) 100%);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 30, 30, 0.1);
        box-shadow: 
            0 0 25px rgba(30, 100, 255, 0.15),
            inset 0 0 40px rgba(255, 30, 30, 0.03);
        margin-bottom: 2rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, rgba(30, 100, 255, 0.1) 0%, rgba(255, 30, 30, 0.05) 100%);
        border: 1px solid rgba(255, 30, 30, 0.2);
        color: #ffffff;
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(30, 100, 255, 0.2) 0%, rgba(255, 30, 30, 0.1) 100%);
        border: 1px solid rgba(255, 30, 30, 0.3);
        box-shadow: 0 0 20px rgba(30, 100, 255, 0.2);
        transform: translateY(-1px);
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0e1117;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: #2e3137;
        border-radius: 4px;
        border: 2px solid #0e1117;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #ff3030;
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.9) 100%);
    }

    .css-1p05t8e {
        background: #0e1117;
    }

    /* Select boxes and inputs */
    .stSelectbox [data-baseweb="select"] {
        background: #1a1c23;
        border: 1px solid rgba(0, 255, 136, 0.2);
        border-radius: 8px;
    }

    .stSelectbox [data-baseweb="select"]:hover {
        border: 1px solid rgba(0, 255, 136, 0.4);
    }

    /* Headers */
    h2, h3, h4 {
        color: #fafafa;
        font-weight: 600;
        letter-spacing: -0.5px;
        margin-bottom: 1rem;
    }

    /* Links */
    a {
        color: #3080ff;
        text-decoration: none;
        transition: all 0.2s ease;
    }

    a:hover {
        color: #ff3030;
        text-shadow: 0 0 8px rgba(255, 30, 30, 0.5);
    }

    /* DataFrames and Tables */
    .stDataFrame {
        background: linear-gradient(145deg, #1a1c23 0%, rgba(26, 28, 35, 0.95) 100%);
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid rgba(30, 100, 255, 0.1);
        box-shadow: 
            0 0 25px rgba(255, 30, 30, 0.15),
            inset 0 0 40px rgba(30, 100, 255, 0.03);
        margin-bottom: 1.5rem;
    }

    /* Table headers */
    [data-testid="stDataFrameResizable"] th {
        background: rgba(30, 100, 255, 0.1) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border-bottom: 1px solid rgba(30, 100, 255, 0.2) !important;
        letter-spacing: 0.5px;
    }

    /* Table cells */
    [data-testid="stDataFrameResizable"] td {
        background: transparent !important;
        color: #fafafa !important;
        padding: 0.8rem 1rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        font-size: 0.95rem;
    }

    /* Row hover effect */
    [data-testid="stDataFrameResizable"] tr:hover td {
        background: rgba(255, 30, 30, 0.05) !important;
        transition: all 0.2s ease;
    }

    /* Table container */
    .element-container iframe {
        background: transparent !important;
    }

    /* Sort indicators */
    button[data-testid="stDataFrameResizable"] svg {
        fill: #ff3030 !important;
    }

    /* Custom scrollbar for tables */
    [data-testid="stDataFrameResizable"] ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    [data-testid="stDataFrameResizable"] ::-webkit-scrollbar-track {
        background: #0e1117;
        border-radius: 3px;
    }

    [data-testid="stDataFrameResizable"] ::-webkit-scrollbar-thumb {
        background: #2e3137;
        border-radius: 3px;
        border: 1px solid #0e1117;
    }

    [data-testid="stDataFrameResizable"] ::-webkit-scrollbar-thumb:hover {
        background: #ff3030;
    }

    /* Number formatting */
    [data-testid="stDataFrameResizable"] td:has(.style_numeric) {
        font-family: 'Inter', monospace;
        letter-spacing: -0.5px;
    }

    /* Status indicators */
    .status-active {
        color: #ff3030 !important;
    }

    .status-reserve {
        color: #ffffff !important;
    }

    .status-minors {
        color: #3080ff !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    try:
        # Display header image
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            try:
                # Load the image from attached_assets folder
                header_img = Image.open('attached_assets/331073D2-5049-4D62-B0E8-56A215C5C224.jpeg')
                
                # Create a stylized container for the image
                container = st.container()
                with container:
                    # Apply styling to the container
                    st.markdown(
                        """
                        <style>
                        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
                            border-radius: 10px;
                            padding: 20px;
                            background: rgba(26, 28, 35, 0.7);
                            text-align: center;
                            margin: 0 auto;
                            box-shadow: 0 0 30px rgba(0, 204, 255, 0.2);
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Display the image with Streamlit's image function inside the container
                    st.image(header_img, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load header image: {str(e)}")
                # Fallback to text header
                st.markdown(
                    """
                    <div style="width: 100%;">
                        <div style="border-radius: 10px; padding: 20px; 
                             background: rgba(26, 28, 35, 0.7); text-align: center; margin: 0 auto; 
                             box-shadow: 0 0 30px rgba(0, 204, 255, 0.2);">
                            <h1 style="margin: 0; font-family: 'Arial Black', sans-serif; font-size: 2.5rem; 
                                       color: #00ccff; text-shadow: 0 0 10px #00ccff, 0 0 20px #00ccff; 
                                       display: flex; justify-content: center; align-items: center;">
                                ABL <span style="color: #ff3030; text-shadow: 0 0 10px #ff3030, 0 0 20px #ff3030; 
                                               margin: 0 10px;">⚾</span> ANALYTICS
                            </h1>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        # Add error notification box
        err_placeholder = st.empty()

        # Streamlined sidebar
        with st.sidebar:
            st.markdown("### 🔄 League Controls")
            st.markdown("Refresh roster data to get the latest trades and player assignments from Fantrax API.")
            if st.button("🔄 Refresh Roster Data", use_container_width=True):
                # Clear the cache to force fresh API data
                fetch_api_data.clear()
                st.success("Cache cleared! Refreshing with latest roster data...")
                st.rerun()
            
            # Add API test button
            st.markdown("### 🔍 API Diagnostics")
            if st.button("Test Fantrax API Connection", use_container_width=True):
                with st.spinner("Testing API connection..."):
                    try:
                        from api_client import FantraxAPI
                        api_client = FantraxAPI()
                        
                        # Test roster API directly
                        st.info("Testing getTeamRosters endpoint...")
                        roster_response = api_client.get_team_rosters()
                        
                        if isinstance(roster_response, dict) and 'rosters' in roster_response:
                            rosters_data = roster_response.get('rosters', {})
                            st.success(f"✅ API Working: Found {len(rosters_data)} teams in roster data")
                            
                            # Show sample team names
                            team_names = []
                            for team_id, team_data in list(rosters_data.items())[:3]:
                                team_name = team_data.get('teamName', 'Unknown')
                                team_names.append(team_name)
                            st.info(f"Sample teams: {', '.join(team_names)}")
                        else:
                            st.error("❌ API returned unexpected format or mock data")
                            st.write("Response type:", type(roster_response))
                            
                    except Exception as e:
                        st.error(f"❌ API Test Failed: {str(e)}")
            
            # Add "Take New Rankings Snapshot" button with improved styling and feedback
            st.markdown("### 📸 Rankings History")
            st.markdown("""
            <div style="margin-bottom: 10px;">
                Take a snapshot of current rankings to use as reference for movement indicators. 
                This will store the current team rankings and be used to show which teams are 
                moving up ▲ or down ▼ in future rankings.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📊 Take New Rankings Snapshot", use_container_width=True):
                # Create a placeholder for status messages
                status_msg = st.empty()
                status_msg.info("📸 Taking snapshot of current rankings...")
                
                # Track success for overall status message
                power_success = False
                ddi_success = False
                
                # Get the current calculated power rankings
                if 'power_rankings_calculated' in st.session_state and st.session_state.power_rankings_calculated is not None:
                    # Save Power Rankings history
                    if save_rankings_history(st.session_state.power_rankings_calculated, ranking_type="power"):
                        power_success = True
                    else:
                        status_msg.error("❌ Failed to save Power Rankings snapshot")
                        
                # Get the current calculated DDI rankings
                if 'ddi_data_calculated' in st.session_state and st.session_state.ddi_data_calculated is not None:
                    # Save DDI Rankings history
                    if save_rankings_history(st.session_state.ddi_data_calculated, ranking_type="ddi"):
                        ddi_success = True
                
                # Show final success message
                if power_success and ddi_success:
                    status_msg.success("✅ Rankings snapshot saved successfully! Future ranking movement will be compared to this snapshot.")
                elif power_success:
                    status_msg.warning("⚠️ Power Rankings snapshot saved, but DDI snapshot failed.")
                elif ddi_success:
                    status_msg.warning("⚠️ DDI Rankings snapshot saved, but Power Rankings snapshot failed.")
                else:
                    status_msg.error("❌ Failed to save rankings snapshots - no ranking data available.")
                
            # Only showing Current API as data source now
            data_source = "Current API"
            
            # Add power rankings data input section
            st.markdown("---")
            st.markdown("### 📊 Power Rankings Data")
            
            # Initialize session state for power rankings data if not exists
            if 'power_rankings_data' not in st.session_state:
                # Try to load saved data first
                saved_data = load_power_rankings_data()
                if saved_data:
                    st.session_state.power_rankings_data = saved_data
                else:
                    st.session_state.power_rankings_data = {}
            
            if 'weekly_results' not in st.session_state:
                # Try to load saved weekly results
                saved_results = load_weekly_results()
                if saved_results:
                    st.session_state.weekly_results = saved_results
                else:
                    st.session_state.weekly_results = []
            
            # Section 1: Bulk data entry for team stats
            st.subheader("Team Season Stats")
            st.markdown("""
            Paste team data in the format: `Team, FPtsF, Weeks Played`  
            Example:
            ```
            Baltimore Orioles, 450.5, 10
            Boston Red Sox, 380.2, 10
            New York Yankees, 410.8, 10
            ```
            *This will overwrite previous data for all teams included in the paste.*
            """)
            
            # Text area for bulk data entry
            bulk_data = st.text_area("Paste Team Data", height=200)
            
            if st.button("Process Team Data", use_container_width=True):
                if bulk_data:
                    # Process the pasted data
                    lines = bulk_data.strip().split('\n')
                    processed_count = 0
                    errors = []
                    
                    for line in lines:
                        try:
                            parts = [part.strip() for part in line.split(',')]
                            if len(parts) >= 3:
                                team_name = parts[0]
                                total_points = float(parts[1])
                                weeks_played = int(parts[2])
                                
                                # Update the session state - store as fptsf to match Fantrax API format
                                st.session_state.power_rankings_data[team_name] = {
                                    'fptsf': total_points,  # Store as fptsf to match the API format
                                    'weeks_played': weeks_played
                                }
                                processed_count += 1
                            else:
                                errors.append(f"Invalid format: {line}")
                        except Exception as e:
                            errors.append(f"Error processing line: {line}. {str(e)}")
                    
                    if processed_count > 0:
                        # Save to persistent storage
                        if save_power_rankings_data(st.session_state.power_rankings_data):
                            st.success(f"Successfully processed and saved {processed_count} team(s)")
                        else:
                            st.warning(f"Processed {processed_count} team(s), but couldn't save to file")
                    
                    if errors:
                        st.error("Errors encountered:")
                        for error in errors:
                            st.write(f"- {error}")
            
            # Section 2: Bulk data entry for weekly results
            st.markdown("---")
            st.subheader("Weekly Results")
            st.markdown("""
            Paste weekly results in the format: `Team, Week Number, Record(W-L-D)`  
            Example:
            ```
            Baltimore Orioles, 5, 2-1-0
            Boston Red Sox, 5, 1-2-0
            New York Yankees, 5, 3-0-0
            ```
            *This will add to previous weekly data. The record should represent the Win-Loss-Draw counts from 3 weekly matchups.*
            """)
            
            # Text area for bulk weekly results
            weekly_results_data = st.text_area("Paste Weekly Results", height=200)
            
            if st.button("Process Weekly Results", use_container_width=True):
                if weekly_results_data:
                    # Process the pasted data
                    lines = weekly_results_data.strip().split('\n')
                    processed_count = 0
                    errors = []
                    
                    for line in lines:
                        try:
                            parts = [part.strip() for part in line.split(',')]
                            if len(parts) >= 3:
                                team_name = parts[0]
                                week_number = int(parts[1])
                                result = parts[2]
                                
                                # Validate record format (W-L-D)
                                try:
                                    # Check if it's in the old format (Win/Loss)
                                    if result.lower() in ['win', 'loss']:
                                        # For backward compatibility
                                        record = "1-0-0" if result.lower() == 'win' else "0-1-0"
                                        weekly_status = result.capitalize()
                                    else:
                                        # Parse as W-L-D record
                                        record = result
                                        record_parts = record.split('-')
                                        if len(record_parts) != 3:
                                            errors.append(f"Invalid record format '{result}'. Use 'W-L-D' format (e.g., '2-1-0'): {line}")
                                            continue
                                        
                                        wins = int(record_parts[0])
                                        losses = int(record_parts[1])
                                        draws = int(record_parts[2])
                                        
                                        # Determine overall status based on record
                                        if wins > losses:
                                            weekly_status = "Win"
                                        elif losses > wins:
                                            weekly_status = "Loss"
                                        else:
                                            weekly_status = "Tie"
                                except ValueError:
                                    errors.append(f"Invalid record values in '{result}'. Use numbers in W-L-D format: {line}")
                                    continue
                                
                                # Add to the session state with the full record
                                st.session_state.weekly_results.append({
                                    'team': team_name,
                                    'week': week_number,
                                    'result': weekly_status,  # For backward compatibility
                                    'record': record,  # Store the full record
                                    'weekly_wins': wins if 'wins' in locals() else (1 if weekly_status == 'Win' else 0),
                                    'weekly_losses': losses if 'losses' in locals() else (1 if weekly_status == 'Loss' else 0),
                                    'weekly_draws': draws if 'draws' in locals() else (1 if weekly_status == 'Tie' else 0)
                                })
                                processed_count += 1
                            else:
                                errors.append(f"Invalid format: {line}")
                        except Exception as e:
                            errors.append(f"Error processing line: {line}. {str(e)}")
                    
                    if processed_count > 0:
                        # Save to persistent storage
                        if save_weekly_results(st.session_state.weekly_results):
                            st.success(f"Successfully processed and saved {processed_count} weekly result(s)")
                        else:
                            st.warning(f"Processed {processed_count} weekly result(s), but couldn't save to file")
                    
                    if errors:
                        st.error("Errors encountered:")
                        for error in errors:
                            st.write(f"- {error}")
            
            # Display current data
            if st.checkbox("Show Current Data"):
                st.write("Season Stats:", st.session_state.power_rankings_data)
                st.write("Weekly Results:", st.session_state.weekly_results)
                
                # Add option to clear data
                if st.button("Clear All Data", type="secondary"):
                    st.session_state.power_rankings_data = {}
                    st.session_state.weekly_results = []
                    
                    # Remove the data files
                    try:
                        if os.path.exists('data/team_season_stats.csv'):
                            os.remove('data/team_season_stats.csv')
                        if os.path.exists('data/weekly_results.csv'):
                            os.remove('data/weekly_results.csv')
                        st.success("All power rankings data has been cleared from memory and storage")
                    except Exception as e:
                        st.warning(f"Data cleared from memory but error deleting files: {str(e)}")

            st.markdown("---")
            st.markdown("### About")
            try:
                # Use a smaller version of the same image for the sidebar
                sidebar_img = Image.open('attached_assets/331073D2-5049-4D62-B0E8-56A215C5C224.jpeg')
                
                # Display the image with Streamlit's image function
                st.image(sidebar_img, width=150)
            except Exception as e:
                # Fallback to text if image can't be loaded
                st.markdown(
                    """
                    <div style="width: 100%;">
                        <div style="border-radius: 10px; padding: 8px; 
                             background: rgba(26, 28, 35, 0.7); text-align: center; margin: 0 auto; 
                             box-shadow: 0 0 15px rgba(0, 204, 255, 0.2);">
                            <h3 style="margin: 0; font-family: 'Arial Black', sans-serif; font-size: 1.2rem; 
                                      color: #00ccff; text-shadow: 0 0 5px #00ccff, 0 0 10px #00ccff;
                                      display: flex; justify-content: center; align-items: center;">
                                ABL <span style="color: #ff3030; text-shadow: 0 0 5px #ff3030, 0 0 10px #ff3030; margin: 0 5px;">⚾</span>
                            </h3>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            st.markdown("Advanced Baseball League (ABL) analytics platform providing comprehensive insights and analysis.")
            
            # Add debugging information
            st.markdown("---")
            st.markdown("### Debug Info")
            st.write(f"Streamlit version: {st.__version__}")
            st.write(f"Current directory: {os.getcwd()}")
            import sys
            st.write(f"Python version: {sys.version}")
    except Exception as e:
        st.error(f"Error in main UI setup: {str(e)}")
        import traceback
        st.write(traceback.format_exc())

    try:
        # Use the Current API
        data = fetch_api_data()
        
        if data:
            # Store standings data in session state for power rankings input
            if 'standings_data' not in st.session_state:
                st.session_state.standings_data = data['standings_data']
            
            # Session state for power rankings data should be already initialized in the sidebar section
            # but just in case there was an error, let's check again
            if 'power_rankings_data' not in st.session_state:
                st.session_state.power_rankings_data = {}
            
            if 'weekly_results' not in st.session_state:
                st.session_state.weekly_results = []
            
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🏠 League Info",
                "👥 Team Rosters",
                "🏆 Power Rankings",
                "🌟 MVP Race",
                "🔥 Dump Deadline",
                "📚 Handbook", 
                "🏆 DDI Rankings"
            ])

            with tab1:
                league_info.render(data['league_data'])

            with tab2:
                rosters.render(data['roster_data'])

            with tab3:
                # Pass session state data to power_rankings component
                power_rankings_data = st.session_state.power_rankings_data if 'power_rankings_data' in st.session_state else {}
                weekly_results = st.session_state.weekly_results if 'weekly_results' in st.session_state else []
                
                # Call modified render with custom data
                power_rankings.render(
                    data['standings_data'], 
                    power_rankings_data=power_rankings_data,
                    weekly_results=weekly_results
                )

            with tab4:
                mvp_race.render()

            with tab5:
                dump_deadline.render()

            with tab6:
                prospects.render(data['roster_data'])

            with tab7:
                # Get the power rankings data from the power_rankings component
                if 'power_rankings_calculated' in st.session_state and st.session_state.power_rankings_calculated is not None:
                    # Use the calculated power rankings
                    power_rankings_df = st.session_state.power_rankings_calculated
                    ddi_df = ddi.render(data['roster_data'], power_rankings_df)
                    
                    # Store DDI data in session state for other components to use
                    st.session_state.ddi_data_calculated = ddi_df
                    
                    # Check if we should take a weekly snapshot (Sunday or first run)
                    if should_take_weekly_snapshot():
                        with st.sidebar:
                            snapshot_container = st.empty()
                            # Save Power Rankings history
                            if save_rankings_history(power_rankings_df, ranking_type="power"):
                                snapshot_container.success("✅ Power Rankings snapshot saved!")
                            else:
                                snapshot_container.error("❌ Failed to save Power Rankings snapshot")
                            
                            # Save DDI Rankings history if available
                            if 'ddi_data_calculated' in st.session_state and st.session_state.ddi_data_calculated is not None:
                                ddi_rankings_df = st.session_state.ddi_data_calculated
                                if save_rankings_history(ddi_rankings_df, ranking_type="ddi"):
                                    snapshot_container.success("✅ DDI Rankings snapshot saved!")
                                else:
                                    snapshot_container.error("❌ Failed to save DDI Rankings snapshot")
                else:
                    # Just pass the roster data without power rankings
                    ddi_df = ddi.render(data['roster_data'])
                    
                    # Store DDI data in session state for other components to use
                    st.session_state.ddi_data_calculated = ddi_df
        else:
            st.error("Unable to fetch data from the API. Please check your connection and try again.")

    except Exception as e:
        st.error(f"An error occurred while loading data: {str(e)}")
        st.info("Please try refreshing the page or check your connection.")

if __name__ == "__main__":
    main()