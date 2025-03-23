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
            margin: 15px 0;
            padding: 0;
            font-size: min(3rem, 10vw);
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
            width: min(450px, 85vw, 85vh);
            height: min(450px, 85vw, 85vh);
            background: #b38b5c;
            border: min(10px, 2vw) solid #a87a4d;
            z-index: 0;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.3);
        }
        
        /* Base containers for positioning */
        .base-container {
            position: absolute;
            width: min(120px, 23vw, 23vh);
            height: min(120px, 23vw, 23vh);
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            transform-origin: center center;
        }
        
        .home-plate-container {
            bottom: 0;
            left: 50%;
            transform: translateX(-50%) rotate(-45deg) translateY(20%);
        }
        
        .first-base-container {
            top: 0;
            right: 0;
            transform: translate(30%, -30%) rotate(-45deg);
        }
        
        .second-base-container {
            top: 0;
            left: 50%;
            transform: translateX(-50%) translateY(-30%) rotate(-45deg);
        }
        
        .third-base-container {
            top: 0;
            left: 0;
            transform: translate(-30%, -30%) rotate(-45deg);
        }
        
        .pitchers-mound-container {
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
        }
        
        /* Bases */
        .base {
            position: absolute;
            width: min(30px, 6vw, 6vh);
            height: min(30px, 6vw, 6vh);
            background: white;
            border: min(3px, 0.5vw) solid #e0e0e0;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
            z-index: 2;
        }
        
        .home-plate {
            bottom: 20%;
            left: 50%;
            transform: translateX(-50%) rotate(45deg);
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
            width: min(50px, 9vw, 9vh);
            height: min(50px, 9vw, 9vh);
            background: #a87a4d;
            border: min(3px, 0.5vw) solid #96693f;
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
            height: min(10px, 1.5vw);
            transform-origin: bottom right;
            transform: rotate(-45deg);
        }
        
        .first-to-second {
            top: 0;
            right: 0;
            width: min(10px, 1.5vw);
            height: 50%;
            transform-origin: top right;
            transform: rotate(-45deg);
        }
        
        .second-to-third {
            top: 0;
            left: 0;
            width: 50%;
            height: min(10px, 1.5vw);
            transform-origin: top left;
            transform: rotate(-45deg);
        }
        
        .third-to-home {
            bottom: 0;
            left: 0;
            width: min(10px, 1.5vw);
            height: 50%;
            transform-origin: bottom left;
            transform: rotate(-45deg);
        }
        
        /* Base buttons styling */
        .base-button {
            width: min(100px, 20vw, 20vh);
            height: min(100px, 20vw, 20vh);
            border-radius: 50%;
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            border: min(4px, 0.8vw) solid white;
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
            position: relative;
            z-index: 20;
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
        
        .base-button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
        }
        
        .position-icon {
            font-size: clamp(1.2rem, 4vw, 2rem);
            margin-bottom: min(5px, 1vw);
        }
        
        .position-text {
            font-size: clamp(0.6rem, 2vw, 0.9rem);
            text-align: center;
            line-height: 1.2;
        }
        
        /* Mobile optimization for base buttons */
        @media (max-width: 767px) {
            .base-container {
                width: min(100px, 20vw, 20vh);
                height: min(100px, 20vw, 20vh);
            }
            
            .base-button {
                width: min(80px, 18vw, 18vh);
                height: min(80px, 18vw, 18vh);
            }
            
            .home-plate-container {
                transform: translateX(-50%) rotate(-45deg) translateY(30%);
            }
            
            .first-base-container {
                transform: translate(30%, -30%) rotate(-45deg);
            }
            
            .second-base-container {
                transform: translateX(-50%) translateY(-30%) rotate(-45deg);
            }
            
            .third-base-container {
                transform: translate(-30%, -30%) rotate(-45deg);
            }
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
                transparent min(40px, 5vw),
                rgba(0, 0, 0, 0.05) min(40px, 5vw),
                rgba(0, 0, 0, 0.05) min(80px, 10vw)
            );
            z-index: -1;
            opacity: 0.7;
        }
        
        /* Better touch handling for mobile */
        @media (pointer: coarse) {
            .base-button {
                animation: none;
            }
            .base-button:active {
                transform: scale(1.1);
                box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the baseball field HTML structure
    field_html = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <div class="baseball-field-overlay"></div>
    <div class="grass-lines"></div>
    
    <h1 class="title">⚾ ABL Analytics</h1>
    
    <!-- Baseball diamond -->
    <div class="baseball-diamond">
        <!-- Home plate with League Info -->
        <div class="base-container home-plate-container">
            <div class="base home-plate"></div>
            <button id="league-info-btn" class="base-button home-button">
                <span class="position-icon">🏠</span>
                <span class="position-text">League<br>Info</span>
            </button>
        </div>
        
        <!-- First base with Team Rosters -->
        <div class="base-container first-base-container">
            <div class="base first-base"></div>
            <button id="team-rosters-btn" class="base-button first-button">
                <span class="position-icon">👥</span>
                <span class="position-text">Team<br>Rosters</span>
            </button>
        </div>
        
        <!-- Second base with Power Rankings -->
        <div class="base-container second-base-container">
            <div class="base second-base"></div>
            <button id="power-rankings-btn" class="base-button second-button">
                <span class="position-icon">🏆</span>
                <span class="position-text">Power<br>Rankings</span>
            </button>
        </div>
        
        <!-- Third base with Handbook -->
        <div class="base-container third-base-container">
            <div class="base third-base"></div>
            <button id="handbook-btn" class="base-button third-button">
                <span class="position-icon">📚</span>
                <span class="position-text">Handbook</span>
            </button>
        </div>
        
        <!-- Pitcher's mound with Projected Rankings -->
        <div class="base-container pitchers-mound-container">
            <div class="pitchers-mound"></div>
            <button id="projected-rankings-btn" class="base-button mound-button">
                <span class="position-icon">📈</span>
                <span class="position-text">Projected<br>Rankings</span>
            </button>
        </div>
        
        <!-- Base paths -->
        <div class="base-path home-to-first"></div>
        <div class="base-path first-to-second"></div>
        <div class="base-path second-to-third"></div>
        <div class="base-path third-to-home"></div>
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
                try {
                    // Multiple ways to find the button
                    let enterAppBtn = streamlitDoc.querySelector('button[kind="primary"]');
                    
                    if (!enterAppBtn) {
                        // Try finding it by key
                        enterAppBtn = streamlitDoc.querySelector('[data-testid="stButton"]');
                    }
                    
                    if (!enterAppBtn) {
                        // Try finding by content
                        const buttons = streamlitDoc.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.textContent.includes('ENTER APP')) {
                                enterAppBtn = btn;
                                break;
                            }
                        }
                    }
                    
                    if (enterAppBtn) {
                        console.log("Found button, clicking now");
                        enterAppBtn.click();
                    } else {
                        console.error("Could not find the hidden button");
                        // Force app entry by direct state manipulation
                        window.parent.sessionStorage.setItem('entered_app', 'true');
                        window.parent.location.reload();
                    }
                } catch (err) {
                    console.error("Error clicking button:", err);
                }
            }, 300);
        }
        
        // Utility function to detect if we're on a mobile device
        function isMobileDevice() {
            return (typeof window.orientation !== "undefined") || (navigator.userAgent.indexOf('IEMobile') !== -1);
        }
        
        // Set up event listeners when the DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Helper function to add both click and touch events
            function addClickAndTouchEvents(element, handler) {
                // For desktop clicks
                element.addEventListener('click', handler);
                
                // For mobile touches
                if (isMobileDevice()) {
                    element.addEventListener('touchstart', function(e) {
                        // Prevent default to avoid double-firing on some devices
                        e.preventDefault();
                        handler.call(this, e);
                    });
                }
            }
            
            // Add handlers for all base buttons
            addClickAndTouchEvents(document.getElementById('power-rankings-btn'), function() {
                handlePositionClick.call(this, 2);
            });
            
            addClickAndTouchEvents(document.getElementById('league-info-btn'), function() {
                handlePositionClick.call(this, 0);
            });
            
            addClickAndTouchEvents(document.getElementById('team-rosters-btn'), function() {
                handlePositionClick.call(this, 1);
            });
            
            addClickAndTouchEvents(document.getElementById('handbook-btn'), function() {
                handlePositionClick.call(this, 3);
            });
            
            addClickAndTouchEvents(document.getElementById('projected-rankings-btn'), function() {
                handlePositionClick.call(this, 4);
            });
        });
    </script>
    """
    
    # Render the baseball field
    st.markdown(field_html, unsafe_allow_html=True)
    
    # Hidden button that will be triggered by JavaScript (completely hidden from view)
    st.markdown('<div style="display:none; position:absolute; visibility:hidden; height:0; width:0; overflow:hidden;">', unsafe_allow_html=True)
    if st.button("ENTER APP", type="primary", key="hidden_enter"):
        st.session_state.entered_app = True
        time.sleep(0.3)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown