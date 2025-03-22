import streamlit as st
import time

def render():
    """
    Render an animated baseball field landing page with links to different sections of the app.
    """
    # Use session state to keep track of whether the user has entered the app
    if 'entered_app' not in st.session_state:
        st.session_state.entered_app = False
    
    # Check if user wants to enter the app
    if st.session_state.entered_app:
        return False
    
    # Apply custom CSS for the baseball field
    st.markdown("""
    <style>
        .stApp {
            background-color: #1a1c23;
        }
        
        h1.title {
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            animation: glow 3s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from {
                text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #ff3030;
            }
            to {
                text-shadow: 0 0 15px #fff, 0 0 25px #ff3030, 0 0 35px #ff3030;
            }
        }
        
        /* Baseball field background */
        .field-bg {
            background-color: #387c3f;
            border-radius: 20px;
            padding: 30px;
            margin: 20px auto;
            max-width: 800px;
            position: relative;
            min-height: 500px;
            border: 5px solid #34703a;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title with animation
    st.markdown("<h1 class='title'>⚾ ABL Analytics Field</h1>", unsafe_allow_html=True)
    
    # Create the baseball field background container
    st.markdown("<div class='field-bg'></div>", unsafe_allow_html=True)
    
    # Create player positions as buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        # Pitcher position - Power Rankings
        if st.button("🏆 Power Rankings", key="power_rankings", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 2  # Power Rankings tab index
            time.sleep(0.3)
            st.experimental_rerun()
    
    col1, col2, col3, col4, col5 = st.columns([0.5, 1, 1, 1, 0.5])
    with col2:
        # Second base - Team Rosters
        if st.button("👥 Team Rosters", key="team_rosters", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 1  # Team Rosters tab index
            time.sleep(0.3)
            st.experimental_rerun()
    with col4:
        # Shortstop - Projected Rankings
        if st.button("📈 Projected Rankings", key="projected_rankings", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 4  # Projected Rankings tab index
            time.sleep(0.3)
            st.experimental_rerun()
    
    col1, col2, col3, col4, col5 = st.columns([0.7, 1, 0.6, 1, 0.7])
    with col2:
        # First base - League Info
        if st.button("🏠 League Info", key="league_info", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 0  # League Info tab index
            time.sleep(0.3)
            st.experimental_rerun()
    with col4:
        # Third base - Handbook
        if st.button("📚 Handbook", key="handbook", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 3  # Handbook tab index
            time.sleep(0.3)
            st.experimental_rerun()
    
    # Add ENTER APP button at bottom
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("ENTER APP", type="primary", use_container_width=True):
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.experimental_rerun()
    
    # Add CSS to style the buttons to look like baseball positions
    st.markdown("""
    <style>
        /* Style all regular buttons as circular baseball-themed buttons */
        button[data-testid="baseButton-secondary"] {
            border-radius: 50% !important;
            width: 120px !important;
            height: 120px !important;
            border: 3px solid white !important;
            background: linear-gradient(145deg, #ff3030, #d42a2a) !important;
            color: white !important;
            font-weight: bold !important;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.3) !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 !important;
            margin: 0 auto !important;
            min-height: unset !important;
            line-height: 1.2 !important;
        }
        
        button[data-testid="baseButton-secondary"]:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.6) !important;
        }
        
        /* Make ENTER APP button special */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(145deg, #ff3030, #d42a2a) !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 1.2rem !important;
            padding: 0.8rem 2rem !important;
            border-radius: 30px !important;
            border: none !important;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.4) !important;
            transition: all 0.3s ease !important;
            margin-top: 20px !important;
        }
        
        button[data-testid="baseButton-primary"]:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown