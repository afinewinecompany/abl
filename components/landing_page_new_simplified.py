import streamlit as st
import time

def render():
    """
    Render a simplified baseball-themed landing page with Streamlit native components.
    This approach avoids JavaScript issues by using Streamlit's built-in components.
    """
    # If we've already entered the app, don't show the landing page
    if st.session_state.get('entered_app', False):
        return False
    
    # Initialize the selected tab in session state if it doesn't exist
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = 0
    
    # Hide Streamlit default styling
    hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0;
            padding-bottom: 0;
            max-width: 100%;
        }
        
        /* Apply baseball theme styling */
        .stApp {
            background: radial-gradient(circle at center, #1a3c6e 0%, #0a1b33 100%) !important;
        }
        
        /* Style for headers */
        h1, h2 {
            color: white !important;
            text-align: center;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.8), 0 0 20px rgba(255, 0, 0, 0.5);
        }
        
        /* Animation for title */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .animate-title {
            animation: pulse 4s infinite;
            display: inline-block;
        }
        
        /* Custom button styling */
        div[data-testid="column"] div[data-testid="stButton"] {
            width: 100%;
            margin-bottom: 10px;
        }
        
        div[data-testid="column"] div[data-testid="stButton"] button {
            width: 100%;
            background: linear-gradient(145deg, #e63946, #d62828);
            color: white;
            border: none;
            border-radius: 15px;
            height: 120px;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        div[data-testid="column"] div[data-testid="stButton"] button:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
        }
        
        div[data-testid="column"] div[data-testid="stButton"] button p {
            margin: 0;
            padding: 5px 0;
        }
        
        .button-icon {
            font-size: 32px;
            margin-bottom: 8px;
        }
        
        /* Baseball animation container */
        .baseball-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            overflow: hidden;
        }
        
        /* Flying baseball */
        .baseball {
            position: absolute;
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 50%;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            animation: flyingBall 15s infinite linear;
        }
        
        @keyframes flyingBall {
            0% {
                top: 120%;
                left: -10%;
                transform: scale(0.2);
            }
            20% {
                top: 20%;
                left: 30%;
                transform: scale(1);
            }
            40% {
                top: 40%;
                left: 70%;
                transform: scale(0.5);
            }
            60% {
                top: 70%;
                left: 40%;
                transform: scale(0.8);
            }
            80% {
                top: 10%;
                left: 80%;
                transform: scale(0.4);
            }
            100% {
                top: 120%;
                left: 110%;
                transform: scale(0.3);
            }
        }
    </style>
    
    <!-- Baseball animation elements -->
    <div class="baseball-container">
        <div class="baseball"></div>
    </div>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Title with animation
    st.markdown('<h1 class="animate-title">⚾ ABL Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<h2>Advanced Baseball League Analysis</h2>', unsafe_allow_html=True)
    
    # Add some space
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Add additional CSS for responsive buttons
    st.markdown("""
    <style>
        /* Responsive grid for buttons */
        @media (max-width: 768px) {
            /* On tablets and smaller screens, make buttons stack better */
            div[data-testid="column"] {
                min-width: 50% !important;
                width: 50% !important;
            }
        }
        
        @media (max-width: 576px) {
            /* On mobile phones, use a single column layout */
            div[data-testid="column"] {
                min-width: 100% !important;
                width: 100% !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a fixed 3-column layout - CSS will handle responsive adjustments
    use_columns = 3
    
    cols = st.columns(use_columns)
    
    # League Info button
    with cols[0]:
        if st.button('<p class="button-icon">🏠</p><p>League Info</p>', key="btn1", use_container_width=True, help="View League Information", type="primary"):
            st.session_state.selected_tab = 0
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.rerun()
    
    # Team Rosters button
    with cols[1 % use_columns]:
        if st.button('<p class="button-icon">👥</p><p>Team Rosters</p>', key="btn2", use_container_width=True, help="View Team Rosters", type="primary"):
            st.session_state.selected_tab = 1
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.rerun()
    
    # Power Rankings button
    with cols[2 % use_columns]:
        if st.button('<p class="button-icon">🏆</p><p>Power Rankings</p>', key="btn3", use_container_width=True, help="View Power Rankings", type="primary"):
            st.session_state.selected_tab = 2
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.rerun()
    
    # Handbook button
    with cols[0]:
        if st.button('<p class="button-icon">📚</p><p>Handbook</p>', key="btn4", use_container_width=True, help="View Prospect Handbook", type="primary"):
            st.session_state.selected_tab = 3
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.rerun()
    
    # Projected Rankings button
    with cols[1 % use_columns]:
        if st.button('<p class="button-icon">📈</p><p>Projected Rankings</p>', key="btn5", use_container_width=True, help="View Projected Rankings", type="primary"):
            st.session_state.selected_tab = 4
            st.session_state.entered_app = True
            time.sleep(0.3)
            st.rerun()
    
    return True  # Return True to indicate the landing page is being shown