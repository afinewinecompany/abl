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
        
        /* Field background - full screen */
        .field-container {
            background: linear-gradient(#2b8a3e, #1b5a2e);
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            padding: 0;
            margin: 0;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            z-index: 9999;
        }
        
        /* Hide default Streamlit elements when showing the field */
        header[data-testid="stHeader"], 
        footer, 
        .main > div:first-child,
        .block-container {
            display: none !important;
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
        
        /* Player positions styling */
        .player-position {
            position: absolute;
            z-index: 10;
        }
        
        .pitcher-position {
            top: 40%;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .first-baseman-position {
            bottom: 38%;
            right: 30%;
        }
        
        .second-baseman-position {
            top: 20%;
            right: 35%;
        }
        
        .third-baseman-position {
            bottom: 38%;
            left: 30%;
        }
        
        .shortstop-position {
            top: 20%;
            left: 35%;
        }
        
        /* Player button styling */
        .player-button {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            border: 3px solid white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
            transition: all 0.3s ease;
            cursor: pointer;
            animation: pulse 2s infinite;
            padding: 0;
            font-weight: bold;
        }
        
        .player-button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.6);
        }
        
        .player-icon {
            font-size: 2rem;
            margin-bottom: 5px;
        }
        
        .player-text {
            font-size: 0.9rem;
            text-align: center;
            line-height: 1.2;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
        
        /* Enter button container */
        .enter-button-container {
            position: absolute;
            bottom: 5%;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
        }
        
        /* Enter button styling */
        .enter-app-button {
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            font-weight: bold;
            font-size: 1.2rem;
            padding: 0.8rem 2rem;
            border-radius: 30px;
            border: none;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .enter-app-button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
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
    
    # Create player positions directly in HTML with absolute positioning
    positions_html = """
        <!-- Pitcher in center (Power Rankings) -->
        <div class="player-position pitcher-position">
            <button class="player-button" data-tab="2">
                <span class="player-icon">🏆</span>
                <span class="player-text">Power<br>Rankings</span>
            </button>
        </div>
        
        <!-- First Baseman (League Info) -->
        <div class="player-position first-baseman-position">
            <button class="player-button" data-tab="0">
                <span class="player-icon">🏠</span>
                <span class="player-text">League<br>Info</span>
            </button>
        </div>
        
        <!-- Second Baseman (Team Rosters) -->
        <div class="player-position second-baseman-position">
            <button class="player-button" data-tab="1">
                <span class="player-icon">👥</span>
                <span class="player-text">Team<br>Rosters</span>
            </button>
        </div>
        
        <!-- Third Baseman (Handbook) -->
        <div class="player-position third-baseman-position">
            <button class="player-button" data-tab="3">
                <span class="player-icon">📚</span>
                <span class="player-text">Handbook</span>
            </button>
        </div>
        
        <!-- Shortstop (Projected Rankings) -->
        <div class="player-position shortstop-position">
            <button class="player-button" data-tab="4">
                <span class="player-icon">📈</span>
                <span class="player-text">Projected<br>Rankings</span>
            </button>
        </div>
        
        <!-- Home plate -->
        <div class="home-plate"></div>
    """
    
    st.markdown(positions_html, unsafe_allow_html=True)
    
    # Add JavaScript to handle player button clicks
    js_code = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Set up click handlers for player buttons
            const playerButtons = document.querySelectorAll('.player-button');
            
            playerButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Store the tab index in sessionStorage (more reliable than localStorage in this context)
                    const tabIndex = this.getAttribute('data-tab');
                    sessionStorage.setItem('selectedTab', tabIndex);
                    
                    // Add visual feedback on click
                    this.style.transform = 'scale(1.2)';
                    
                    // Trigger navigating away from landing page by clicking the hidden ENTER APP button
                    setTimeout(() => {
                        // Find the primary button even if it's hidden
                        const primaryButton = document.querySelector('button[data-testid="baseButton-primary"]');
                        if (primaryButton) {
                            primaryButton.click();
                        } else {
                            console.error('Could not find primary button to click');
                        }
                    }, 300);
                });
            });
        });
    </script>
    """
    
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Visible "Enter App" button at the bottom
    enter_button_html = """
    <div class="enter-button-container">
        <button id="visible-enter-button" class="enter-app-button">ENTER APP</button>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const visibleEnterButton = document.getElementById('visible-enter-button');
            if (visibleEnterButton) {
                visibleEnterButton.addEventListener('click', function() {
                    // Add visual feedback
                    this.style.transform = 'scale(1.1)';
                    this.style.boxShadow = '0 0 30px rgba(255, 0, 0, 0.8)';
                    
                    // Find and click the hidden primary button
                    setTimeout(() => {
                        const primaryButton = document.querySelector('button[data-testid="baseButton-primary"]');
                        if (primaryButton) {
                            primaryButton.click();
                        } else {
                            console.error('Could not find primary button');
                        }
                    }, 300);
                });
            }
        });
    </script>
    """
    
    st.markdown(enter_button_html, unsafe_allow_html=True)
    
    # Close the field container
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Hidden but functional primary button that we'll click via JavaScript
    # Keep it outside the container so it doesn't mess with the layout
    st.markdown('<div style="display:none !important; position: absolute;">', unsafe_allow_html=True)
    if st.button("ENTER APP", key="enter_app_primary", use_container_width=True, type="primary"):
        st.session_state.entered_app = True
        time.sleep(0.3)
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown