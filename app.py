import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects, projected_rankings, handbook
from api_client import FantraxAPI
from data_processor import DataProcessor

st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        padding: 1rem 2rem;
        background: #0e1117;
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
    st.title("⚾ ABL Analytics")

    # Initialize API client
    api_client = FantraxAPI()
    data_processor = DataProcessor()

    # Streamlined sidebar
    with st.sidebar:
        st.markdown("### 🔄 League Controls")
        if st.button("Refresh Data", use_container_width=True):
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("""
        ### About ABL Analytics
        Advanced Baseball League (ABL) analytics platform providing comprehensive insights and analysis.
        """)

    try:
        # Fetch all required data
        league_data = api_client.get_league_info()
        roster_data = api_client.get_team_rosters()
        standings_data = api_client.get_standings()
        player_ids = api_client.get_player_ids()

        # Process data
        processed_league_data = data_processor.process_league_info(league_data)
        processed_roster_data = data_processor.process_rosters(roster_data, player_ids)
        processed_standings_data = data_processor.process_standings(standings_data)

        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 League Info",
            "👥 Team Rosters",
            "🏆 Power Rankings",
            "📚 Rules & Info",
            "📈 Projected Rankings"
        ])

        with tab1:
            league_info.render(processed_league_data)

        with tab2:
            rosters.render(processed_roster_data)

        with tab3:
            power_rankings.render(processed_standings_data)

        with tab4:
            handbook.render(processed_roster_data)

        with tab5:
            projected_rankings.render(processed_roster_data)

    except Exception as e:
        st.error(f"An error occurred while loading data. Please try refreshing.")

if __name__ == "__main__":
    main()