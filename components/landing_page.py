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
    
    st.markdown("""
    <style>
        /* Custom CSS for the landing page */
        .glowing-title {
            font-size: 3rem;
            color: white;
            text-align: center;
            font-weight: bold;
            text-shadow: 
                0 0 10px rgba(255, 30, 30, 0.6),
                0 0 20px rgba(30, 100, 255, 0.6);
            animation: glow 2s infinite alternate;
        }
        
        @keyframes glow {
            from {
                text-shadow: 
                    0 0 10px rgba(255, 30, 30, 0.6),
                    0 0 20px rgba(30, 100, 255, 0.6);
            }
            to {
                text-shadow: 
                    0 0 15px rgba(255, 30, 30, 0.8),
                    0 0 30px rgba(30, 100, 255, 0.8);
            }
        }
        
        /* Player button styling */
        .player-button {
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
            animation: pulse 2s infinite !important;
        }
        
        .player-button:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.6) !important;
        }
        
        .player-icon {
            font-size: 1.8rem !important;
            margin-bottom: 5px !important;
        }
        
        .player-text {
            font-size: 0.75rem !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
            line-height: 1.2 !important;
        }
        
        /* Field background */
        .field-container {
            background: linear-gradient(#2b8a3e, #1b5a2e);
            border-radius: 30px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }
        
        /* Diamond shape for infield */
        .diamond-shape {
            background: #b9895c;
            width: 300px;
            height: 300px;
            margin: 0 auto;
            transform: rotate(45deg);
            position: absolute;
            top: 40%;
            left: 50%;
            margin-left: -150px;
            margin-top: -150px;
            transform-origin: center;
            z-index: 0;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
        }
        
        /* Base paths */
        .base-path {
            position: absolute;
            background: #c9a97c;
            height: 12px;
            width: 120px;
            z-index: 0;
        }
        
        .home-to-first {
            bottom: 42%;
            right: 43%;
            transform: rotate(45deg);
        }
        
        .first-to-second {
            top: 42%;
            right: 43%;
            transform: rotate(-45deg);
        }
        
        .second-to-third {
            top: 42%;
            left: 43%;
            transform: rotate(45deg);
        }
        
        .third-to-home {
            bottom: 42%;
            left: 43%;
            transform: rotate(-45deg);
        }
        
        /* Button positioning container */
        .buttons-container {
            position: relative;
            z-index: 1;
            min-height: 500px;
        }
        
        /* Animation for pulse effect */
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.4);
            }
            70% {
                box-shadow: 0 0 0 15px rgba(255, 0, 0, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);
            }
        }
        
        /* Enter app button styling */
        .enter-app-button {
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
        
        .enter-app-button:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6) !important;
        }
        
        /* Home plate styling */
        .home-plate {
            width: 40px;
            height: 40px;
            background: white;
            clip-path: polygon(0 30%, 50% 0, 100% 30%, 100% 100%, 0 100%);
            margin: 0 auto;
            box-shadow: 0 0 15px rgba(255,255,255,0.5);
            position: relative;
            z-index: 1;
        }
        
        /* Bases styling */
        .base {
            width: 25px;
            height: 25px;
            background: white;
            border: 2px solid #333;
            transform: rotate(45deg);
            position: absolute;
            box-shadow: 0 0 10px rgba(255,255,255,0.5);
            z-index: 0;
        }
        
        .first-base {
            bottom: 38%;
            right: 33%;
        }
        
        .second-base {
            top: 25%;
            left: 50%;
            margin-left: -12px;
        }
        
        .third-base {
            bottom: 38%;
            left: 33%;
        }
        
        /* Pitcher's mound */
        .pitchers-mound {
            width: 40px;
            height: 40px;
            background: #b9895c;
            border: 3px solid #a87a4d;
            border-radius: 50%;
            position: absolute;
            top: 45%;
            left: 50%;
            margin-left: -20px;
            margin-top: -20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            z-index: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title with animation
    st.markdown('<h1 class="glowing-title">⚾ ABL Analytics Field</h1>', unsafe_allow_html=True)

    # Baseball field container with diamond, base paths, bases, and pitcher's mound
    st.markdown('''
    <div class="field-container">
        <div class="diamond-shape"></div>
        <div class="base-path home-to-first"></div>
        <div class="base-path first-to-second"></div>
        <div class="base-path second-to-third"></div>
        <div class="base-path third-to-home"></div>
        <div class="base first-base"></div>
        <div class="base second-base"></div>
        <div class="base third-base"></div>
        <div class="pitchers-mound"></div>
        <div class="buttons-container">
    ''', unsafe_allow_html=True)
    
    # Create the baseball field layout with native Streamlit components for better compatibility
    # Pitcher (Power Rankings) in the center
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 30px;">', unsafe_allow_html=True)
        if st.button("🏆\nPower\nRankings", key="power_rankings", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 2  # Power Rankings tab index
            time.sleep(0.3)
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Second Baseman and Shortstop (Team Rosters and Projected Rankings)
    col1, col2, col3, col4, col5 = st.columns([0.5, 1, 1, 1, 0.5])
    with col2:
        if st.button("👥\nTeam\nRosters", key="team_rosters", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 1  # Team Rosters tab index
            time.sleep(0.3)
            st.experimental_rerun()
    with col4:
        if st.button("📈\nProjected\nRankings", key="projected_rankings", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 4  # Projected Rankings tab index
            time.sleep(0.3)
            st.experimental_rerun()
    
    # First Baseman and Third Baseman (League Info and Handbook)
    col1, col2, col3, col4, col5 = st.columns([0.7, 1, 0.6, 1, 0.7])
    with col2:
        if st.button("🏠\nLeague\nInfo", key="league_info", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 0  # League Info tab index
            time.sleep(0.3)
            st.experimental_rerun()
    with col4:
        if st.button("📚\nHandbook", key="handbook", use_container_width=True):
            st.session_state.entered_app = True
            st.session_state.selected_tab = 3  # Handbook tab index
            time.sleep(0.3)
            st.experimental_rerun()
    
    # Home plate at the bottom
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="home-plate"></div>', unsafe_allow_html=True)
    
    # Close the field container
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Enter app button (centered at the bottom)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("ENTER APP", key="enter_app", use_container_width=True, type="primary"):
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.experimental_rerun()
    
    # Additional custom CSS to style buttons directly
    st.markdown("""
    <style>
        /* Make buttons circular */
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
            animation: pulse 2s infinite !important;
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