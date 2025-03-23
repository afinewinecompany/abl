import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects, projected_rankings
from utils import fetch_api_data

# This must be the first Streamlit command
st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simplified CSS for a cleaner look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1rem;
        background: rgba(14, 17, 23, 0.95);
    }
    
    h1 {
        color: #ffffff;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
        font-size: 2.2em;
        font-weight: 700;
    }
    
    h2, h3, h4 {
        color: #fafafa;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Responsive styles */
    @media screen and (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        h1 {
            font-size: 1.8em !important;
            padding: 0.5rem !important;
        }
        
        /* Make data tables scrollable horizontally */
        .stDataFrame {
            max-width: 100%;
            overflow-x: auto;
            padding: 0.5rem !important;
        }
        
        [data-testid="stDataFrameResizable"] td, 
        [data-testid="stDataFrameResizable"] th {
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
            white-space: nowrap;
        }
    }
    
    /* Cleaner DataFrames and Tables */
    .stDataFrame {
        background: #1a1c23;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Table headers */
    [data-testid="stDataFrameResizable"] th {
        background: rgba(30, 100, 255, 0.1) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 0.7rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Table cells */
    [data-testid="stDataFrameResizable"] td {
        background: transparent !important;
        color: #fafafa !important;
        padding: 0.7rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #2e3137;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #3d4046;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar - make it more visible */
    [data-testid="stSidebar"] {
        background-color: #1a1c23;
        padding: 1rem;
    }
    
    /* Status indicators - simplified */
    .status-active {
        color: #ff3030 !important;
    }
    
    .status-reserve {
        color: #ffffff !important;
    }
    
    .status-minors {
        color: #3080ff !important;
    }
    
    /* Hide the Streamlit hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    # Fetch all data using the utility function
    data = fetch_api_data()
    
    # Simplified sidebar navigation
    with st.sidebar:
        st.title("⚾ ABL Analytics")
        
        # Page navigation
        st.subheader("Navigation")
        page = st.radio("", [
            "League Overview", 
            "Team Rosters", 
            "Power Rankings", 
            "Prospect Handbook", 
            "Projected Rankings"
        ])
        
        # Refresh button
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.experimental_rerun()
            
        # About section
        st.markdown("---")
        st.markdown("""
        ### About
        Advanced Baseball League (ABL) analytics platform providing insights and analysis.
        """)
    
    # Main content area
    if data:
        # Display the selected page
        if page == "League Overview":
            st.header("League Overview")
            league_info.render(data['league_data'])
            
        elif page == "Team Rosters":
            st.header("Team Rosters")
            rosters.render(data['roster_data'])
            
        elif page == "Power Rankings":
            st.header("Power Rankings")
            power_rankings.render(data['standings_data'])
            
        elif page == "Prospect Handbook":
            st.header("Prospect Handbook")
            prospects.render(data['roster_data'])
            
        elif page == "Projected Rankings":
            st.header("Projected Rankings")
            projected_rankings.render(data['roster_data'])
    else:
        st.error("Unable to load data. Please try refreshing.")

if __name__ == "__main__":
    main()