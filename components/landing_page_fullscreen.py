import streamlit as st
import time

def render():
    """
    Render a full-screen animated baseball field landing page with player position links.
    """
    # Use session state to keep track of whether the user has entered the app
    if 'entered_app' not in st.session_state:
        st.session_state.entered_app = False
    
    # Check if user wants to enter the app
    if st.session_state.entered_app:
        return False
    
    # Hide Streamlit's default menu and footer
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Apply custom CSS for the full-screen baseball field
    st.markdown("""
    <style>
        /* Reset and full-screen setup */
        .stApp {
            background-color: #1a1c23 !important;
        }
        
        section[data-testid="stSidebar"] {
            display: none;
        }
        
        div[data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding: 0 !important;
        }
        
        div[data-testid="stAppViewContainer"] > div {
            padding: 0 !important;
        }
        
        /* Baseball field overlay */
        .baseball-field-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            background: radial-gradient(circle at center, #387c3f 60%, #1f4321 100%);
            z-index: -1;
        }
        
        /* Title styling */
        h1.title {
            text-align: center;
            color: white;
            margin: 20px 0;
            padding: 0;
            font-size: 3rem;
            font-weight: 700;
            animation: glow 3s ease-in-out infinite alternate;
            text-shadow: 0 0 10px rgba(255,255,255,0.5);
        }
        
        @keyframes glow {
            from {
                text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #ff3030;
            }
            to {
                text-shadow: 0 0 15px #fff, 0 0 25px #ff3030, 0 0 35px #ff3030;
            }
        }
        
        /* Baseball diamond with infield dirt */
        .baseball-diamond {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(45deg);
            width: 450px;
            height: 450px;
            background: #b38b5c;
            border: 10px solid #a87a4d;
            z-index: 0;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.3);
        }
        
        /* Bases */
        .base {
            position: absolute;
            width: 30px;
            height: 30px;
            background: white;
            border: 3px solid #e0e0e0;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
            z-index: 2;
        }
        
        .home-plate {
            bottom: 0;
            left: 50%;
            transform: translateX(-50%) rotate(45deg);
            margin-bottom: -15px;
        }
        
        .first-base {
            top: 0;
            right: 0;
            transform: translate(50%, -50%);
        }
        
        .second-base {
            top: 0;
            left: 50%;
            transform: translateX(-50%) rotate(45deg) translateY(-50%);
        }
        
        .third-base {
            top: 0;
            left: 0;
            transform: translate(-50%, -50%);
        }
        
        /* Pitcher's mound */
        .pitchers-mound {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 50px;
            height: 50px;
            background: #a87a4d;
            border: 3px solid #96693f;
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            z-index: 1;
        }
        
        /* Base paths */
        .base-path {
            position: absolute;
            background: #d0c198;
            z-index: 0;
        }
        
        .home-to-first {
            bottom: 0;
            right: 0;
            width: 50%;
            height: 10px;
            transform-origin: bottom right;
            transform: rotate(-45deg);
        }
        
        .first-to-second {
            top: 0;
            right: 0;
            width: 10px;
            height: 50%;
            transform-origin: top right;
            transform: rotate(-45deg);
        }
        
        .second-to-third {
            top: 0;
            left: 0;
            width: 50%;
            height: 10px;
            transform-origin: top left;
            transform: rotate(-45deg);
        }
        
        .third-to-home {
            bottom: 0;
            left: 0;
            width: 10px;
            height: 50%;
            transform-origin: bottom left;
            transform: rotate(-45deg);
        }
        
        /* Player position containers */
        .player-position {
            position: fixed;
            z-index: 10;
            width: 120px;
            height: 120px;
        }
        
        .pitcher-position {
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .first-base-position {
            top: 50%;
            right: 20%;
            transform: translateY(-50%);
        }
        
        .second-base-position {
            top: 25%;
            right: 35%;
        }
        
        .third-base-position {
            top: 50%;
            left: 20%;
            transform: translateY(-50%);
        }
        
        .shortstop-position {
            top: 25%;
            left: 35%;
        }
        
        /* Position buttons */
        .position-button {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            border: 4px solid white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
            font-weight: bold;
            padding: 0;
        }
        
        @keyframes pulse {
            0% {
                transform: scale(1);
                box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
            }
            50% {
                transform: scale(1.05);
                box-shadow: 0 0 25px rgba(255, 0, 0, 0.5);
            }
            100% {
                transform: scale(1);
                box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
            }
        }
        
        .position-button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
        }
        
        .position-icon {
            font-size: 2rem;
            margin-bottom: 5px;
        }
        
        .position-text {
            font-size: 0.9rem;
            text-align: center;
            line-height: 1.2;
        }
        
        /* Enter app button */
        .enter-app-container {
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
        }
        
        .enter-app-button {
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            font-weight: bold;
            font-size: 1.2rem;
            padding: 1rem 2.5rem;
            border-radius: 50px;
            border: none;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.5);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .enter-app-button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 35px rgba(255, 0, 0, 0.7);
        }
        
        /* Outfield grass texture lines */
        .grass-lines {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                90deg,
                transparent,
                transparent 40px,
                rgba(0, 0, 0, 0.05) 40px,
                rgba(0, 0, 0, 0.05) 80px
            );
            z-index: -1;
            opacity: 0.7;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the baseball field HTML structure
    field_html = """
    <div class="baseball-field-overlay"></div>
    <div class="grass-lines"></div>
    
    <h1 class="title">⚾ ABL Analytics Field</h1>
    
    <!-- Baseball diamond -->
    <div class="baseball-diamond">
        <div class="base home-plate"></div>
        <div class="base first-base"></div>
        <div class="base second-base"></div>
        <div class="base third-base"></div>
        <div class="pitchers-mound"></div>
        <div class="base-path home-to-first"></div>
        <div class="base-path first-to-second"></div>
        <div class="base-path second-to-third"></div>
        <div class="base-path third-to-home"></div>
    </div>
    
    <!-- Player positions -->
    <div class="player-position pitcher-position">
        <button id="power-rankings-btn" class="position-button">
            <span class="position-icon">🏆</span>
            <span class="position-text">Power<br>Rankings</span>
        </button>
    </div>
    
    <div class="player-position first-base-position">
        <button id="league-info-btn" class="position-button">
            <span class="position-icon">🏠</span>
            <span class="position-text">League<br>Info</span>
        </button>
    </div>
    
    <div class="player-position second-base-position">
        <button id="team-rosters-btn" class="position-button">
            <span class="position-icon">👥</span>
            <span class="position-text">Team<br>Rosters</span>
        </button>
    </div>
    
    <div class="player-position third-base-position">
        <button id="handbook-btn" class="position-button">
            <span class="position-icon">📚</span>
            <span class="position-text">Handbook</span>
        </button>
    </div>
    
    <div class="player-position shortstop-position">
        <button id="projected-rankings-btn" class="position-button">
            <span class="position-icon">📈</span>
            <span class="position-text">Projected<br>Rankings</span>
        </button>
    </div>
    
    <!-- Enter app button -->
    <div class="enter-app-container">
        <button id="enter-app-btn" class="enter-app-button">ENTER APP</button>
    </div>
    
    <script>
        // Function to handle position button clicks
        function handlePositionClick(tabIndex) {
            // Add visual feedback on click
            this.style.transform = 'scale(1.2)';
            this.style.boxShadow = '0 0 35px rgba(255, 0, 0, 0.8)';
            
            // Store the selected tab and trigger the enter app action
            const streamlitDoc = window.parent.document;
            
            // Store tab index in session storage for app.py to read
            sessionStorage.setItem('selectedTab', tabIndex);
            
            // Find and click the hidden enter app button
            setTimeout(() => {
                const enterAppBtn = streamlitDoc.querySelector('button[kind="primary"]');
                if (enterAppBtn) {
                    enterAppBtn.click();
                }
            }, 300);
        }
        
        // Set up event listeners when the DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Add click handlers for all position buttons
            document.getElementById('power-rankings-btn').addEventListener('click', function() {
                handlePositionClick.call(this, 2);
            });
            
            document.getElementById('league-info-btn').addEventListener('click', function() {
                handlePositionClick.call(this, 0);
            });
            
            document.getElementById('team-rosters-btn').addEventListener('click', function() {
                handlePositionClick.call(this, 1);
            });
            
            document.getElementById('handbook-btn').addEventListener('click', function() {
                handlePositionClick.call(this, 3);
            });
            
            document.getElementById('projected-rankings-btn').addEventListener('click', function() {
                handlePositionClick.call(this, 4);
            });
            
            // Add click handler for the enter app button
            document.getElementById('enter-app-btn').addEventListener('click', function() {
                // Visual feedback
                this.style.transform = 'scale(1.1)';
                this.style.boxShadow = '0 0 40px rgba(255, 0, 0, 0.8)';
                
                // Find and click the Streamlit button
                setTimeout(() => {
                    const streamlitDoc = window.parent.document;
                    const enterAppBtn = streamlitDoc.querySelector('button[kind="primary"]');
                    if (enterAppBtn) {
                        enterAppBtn.click();
                    }
                }, 300);
            });
        });
    </script>
    """
    
    # Render the baseball field
    st.markdown(field_html, unsafe_allow_html=True)
    
    # Hidden button that will be triggered by JavaScript
    st.markdown('<div style="display:none;">', unsafe_allow_html=True)
    if st.button("ENTER APP", type="primary", key="hidden_enter"):
        st.session_state.entered_app = True
        time.sleep(0.3)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown