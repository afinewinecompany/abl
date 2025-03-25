import streamlit as st
import pandas as pd
import os
from components import league_info, rosters, standings, power_rankings, prospects, transactions, ddi
# Projected Rankings removed as it's no longer relevant for this season
from utils import fetch_api_data, fetch_fantrax_data
from fantrax_integration import fantrax_client

# This must be the first Streamlit command
st.set_page_config(
    page_title="ABL Analytics",
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
        st.title("⚾ ABL Analytics")

        # Add error notification box
        err_placeholder = st.empty()

        # Streamlined sidebar
        with st.sidebar:
            st.markdown("### 🔄 League Controls")
            if st.button("Refresh Data", use_container_width=True):
                st.experimental_rerun()
                
            # Add data source selector
            data_source = st.radio("Data Source", ["Current API", "Fantrax API"])

            st.markdown("---")
            st.markdown("""
            ### About ABL Analytics
            Advanced Baseball League (ABL) analytics platform providing comprehensive insights and analysis.
            """)
            
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
        # Fetch appropriate data based on selected data source
        if data_source == "Current API":
            data = fetch_api_data()
            
            if data:
                # Create tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🏠 League Info",
                    "👥 Team Rosters",
                    "🏆 Power Rankings",
                    "📚 Handbook", 
                    "🏆 DDI Rankings"
                ])

                with tab1:
                    league_info.render(data['league_data'])

                with tab2:
                    rosters.render(data['roster_data'])

                with tab3:
                    power_rankings.render(data['standings_data'])

                with tab4:
                    prospects.render(data['roster_data'])

                with tab5:
                    ddi.render(data['roster_data'])
            else:
                st.info("No data available from the current API. Try switching to the Fantrax API.")
        else:
            # Using Fantrax API
            fantrax_data = fetch_fantrax_data()
            
            if fantrax_data:
                # Create tabs for different sections with Fantrax data
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🏠 League Info",
                    "👥 Team Rosters",
                    "🏆 Power Rankings",
                    "📚 Handbook",
                    "📋 Transactions"
                ])

                with tab1:
                    # Display league info from Fantrax
                    st.header("League Information")
                    league_data = fantrax_data['league_data']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("League Name", league_data.get('name', 'N/A'))
                    with col2:
                        st.metric("Sport", league_data.get('sport', 'N/A'))
                    with col3:
                        st.metric("Season", league_data.get('season', 'N/A'))
                        
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Scoring Type", league_data.get('scoring_type', 'N/A'))
                    with col2:
                        st.metric("Teams", league_data.get('teams_count', 'N/A'))
                    with col3:
                        st.metric("Current Week", league_data.get('current_week', 'N/A'))
                    
                    # Add Standings section to League Info tab
                    st.header("League Standings")
                    standings_data = fantrax_data['standings_data']
                    
                    if not standings_data.empty:
                        # Sort standings by rank
                        standings_data = standings_data.sort_values('rank') if 'rank' in standings_data.columns else standings_data
                        
                        # Display standings table with enhanced formatting
                        st.dataframe(
                            standings_data,
                            column_config={
                                "team": st.column_config.TextColumn("Team"),
                                "rank": st.column_config.NumberColumn("Rank", format="%d"),
                                "wins": st.column_config.NumberColumn("Wins", format="%d"),
                                "losses": st.column_config.NumberColumn("Losses", format="%d"),
                                "ties": st.column_config.NumberColumn("Ties", format="%d"),
                                "win_percentage": st.column_config.NumberColumn("Win %", format="%.3f"),
                                "points_for": st.column_config.NumberColumn("Points For", format="%.1f"),
                                "points_against": st.column_config.NumberColumn("Points Against", format="%.1f"),
                                "streak": "Streak"
                            },
                            hide_index=True
                        )
                        
                        # Add Current Matchups section
                        st.header("Current Matchups")
                        matchups = fantrax_data['current_matchups']
                        
                        if matchups:
                            matchup_df = pd.DataFrame(matchups)
                            st.dataframe(
                                matchup_df,
                                column_config={
                                    "away_team": "Away Team",
                                    "away_score": st.column_config.NumberColumn("Away Score", format="%.1f"),
                                    "home_team": "Home Team", 
                                    "home_score": st.column_config.NumberColumn("Home Score", format="%.1f"),
                                    "winner": "Winner",
                                    "score_difference": st.column_config.NumberColumn("Difference", format="%.1f")
                                },
                                hide_index=True
                            )
                        else:
                            st.info("No current matchups available")
                    else:
                        st.info("No standings data available")

                with tab2:
                    # Display rosters from Fantrax
                    st.header("Team Rosters")
                    roster_data = fantrax_data['roster_data']
                    
                    # Team selector
                    teams = sorted(roster_data['team'].unique()) if not roster_data.empty else []
                    if teams:
                        selected_team = st.selectbox("Select Team", teams)
                        team_roster = roster_data[roster_data['team'] == selected_team]
                        
                        # Display active and injured players
                        st.subheader("Active Players")
                        active_players = team_roster[team_roster['status'] == 'Active']
                        st.dataframe(active_players[['player_name', 'position', 'team', 'injured', 'suspended']])
                        
                        st.subheader("Injured Players")
                        injured_players = team_roster[team_roster['status'] == 'Injured']
                        st.dataframe(injured_players[['player_name', 'position', 'team', 'injured', 'suspended']])
                    else:
                        st.info("No roster data available")

                with tab3:
                    # Use the standings component for a better visualization
                    standings_data = fantrax_data['standings_data']
                    
                    if not standings_data.empty:
                        # Rename columns to match what the standings component expects
                        if 'team' in standings_data.columns and 'team_name' not in standings_data.columns:
                            standings_data = standings_data.rename(columns={'team': 'team_name'})
                        if 'win_percentage' in standings_data.columns and 'winning_pct' not in standings_data.columns:
                            standings_data = standings_data.rename(columns={'win_percentage': 'winning_pct'})
                        
                        # Add games_back if missing
                        if 'games_back' not in standings_data.columns:
                            standings_data['games_back'] = 0.0
                            
                        # Use the standings component for nice visualizations
                        standings.render(standings_data)
                    else:
                        st.info("No standings data available")

                with tab4:
                    prospects.render(fantrax_data['roster_data'])

                with tab5:
                    st.title("Transactions")
                    
                    # Debug information for transactions tab
                    st.sidebar.markdown("### Debug Information")
                    st.sidebar.write(f"fantrax_data keys: {list(fantrax_data.keys())}")
                    
                    # Check if transactions key exists in the data
                    if 'transactions' in fantrax_data:
                        transactions_data = fantrax_data['transactions']
                        st.sidebar.write(f"transactions_data type: {type(transactions_data)}")
                        st.sidebar.write(f"transactions_data length: {len(transactions_data)}")
                        
                        if transactions_data and len(transactions_data) > 0:
                            st.sidebar.write(f"First transaction keys: {list(transactions_data[0].keys()) if transactions_data and isinstance(transactions_data[0], dict) else 'No keys found'}")
                            st.sidebar.write(f"Sample transaction: {transactions_data[0]}")
                        else:
                            st.sidebar.warning("Transactions list is empty")
                            
                            # Let's try to fetch some basic transactions directly for debugging
                            try:
                                st.info("Attempting to fetch transactions directly...")
                                direct_transactions = fantrax_client.get_transactions(limit=10)
                                st.sidebar.write(f"Direct fetch - transactions count: {len(direct_transactions)}")
                                
                                if direct_transactions and len(direct_transactions) > 0:
                                    # Use these transactions instead
                                    transactions_data = direct_transactions
                                    st.success(f"Successfully fetched {len(transactions_data)} transactions directly.")
                                    st.sidebar.write(f"First direct transaction: {direct_transactions[0]}")
                            except Exception as e:
                                st.error(f"Failed to fetch transactions directly: {str(e)}")
                        
                        # Use the transactions component with filtering capabilities
                        transactions.render(transactions_data)
                    else:
                        st.error("Transactions data not found in Fantrax data")
                        try:
                            st.info("Attempting to fetch transactions directly...")
                            direct_transactions = fantrax_client.get_transactions(limit=10)
                            
                            if direct_transactions and len(direct_transactions) > 0:
                                st.success(f"Successfully fetched {len(direct_transactions)} transactions directly.")
                                transactions.render(direct_transactions)
                            else:
                                st.warning("No transactions found when fetching directly.")
                        except Exception as e:
                            st.error(f"Failed to fetch transactions directly: {str(e)}")
            else:
                st.error("Failed to fetch data from Fantrax API. Please check your connection or try again later.")

    except Exception as e:
        st.error(f"An error occurred while loading data: {str(e)}")
        st.info("Try switching to a different data source.")

if __name__ == "__main__":
    main()