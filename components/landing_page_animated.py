import streamlit as st
import time

def render():
    """
    Render a fully animated baseball-themed landing page with buttons for each app page.
    """
    # If we've already entered the app, don't show the landing page
    if st.session_state.get('entered_app', False):
        return False
    
    # Initialize the selected tab in session state
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
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Apply custom CSS for the animated baseball-themed landing page
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
        
        /* Main background */
        .baseball-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: radial-gradient(circle at center, #1a3c6e 0%, #0a1b33 100%);
            overflow: hidden;
            z-index: -10;
        }
        
        /* Stadium lights */
        .stadium-light {
            position: fixed;
            width: 30vw;
            height: 100vh;
            background: radial-gradient(ellipse at center, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
            animation: lightFlicker 8s infinite alternate;
            z-index: -8;
        }
        
        .stadium-light:nth-of-type(1) {
            left: 10%;
            top: -30%;
            transform: rotate(30deg);
        }
        
        .stadium-light:nth-of-type(2) {
            right: 10%;
            top: -30%;
            transform: rotate(-30deg);
        }
        
        @keyframes lightFlicker {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 0.8; }
            75% { opacity: 0.7; }
        }
        
        /* Moving baseball */
        .baseball {
            position: fixed;
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 50%;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            z-index: -2;
            animation: flyingBall 15s infinite linear;
        }
        
        .baseball:before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: repeating-linear-gradient(
                to bottom,
                transparent 0px,
                transparent 5px,
                red 5px,
                red 7px
            );
            opacity: 0.2;
            animation: rotateBall 2s infinite linear;
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
        
        @keyframes rotateBall {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Title */
        .main-title {
            position: fixed;
            top: 10%;
            left: 50%;
            transform: translateX(-50%);
            font-size: min(60px, 10vw);
            font-weight: 900;
            color: white;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.8), 0 0 20px rgba(255, 0, 0, 0.5);
            text-align: center;
            z-index: 10;
            animation: titlePulse 4s infinite alternate;
        }
        
        @keyframes titlePulse {
            0% {
                transform: translateX(-50%) scale(1);
                text-shadow: 0 0 10px rgba(255, 0, 0, 0.8), 0 0 20px rgba(255, 0, 0, 0.5);
            }
            100% {
                transform: translateX(-50%) scale(1.05);
                text-shadow: 0 0 15px rgba(255, 0, 0, 1), 0 0 30px rgba(255, 0, 0, 0.7);
            }
        }
        
        .subtitle {
            position: fixed;
            top: calc(10% + min(70px, 12vw));
            left: 50%;
            transform: translateX(-50%);
            font-size: min(24px, 4vw);
            color: #f0f0f0;
            text-align: center;
            z-index: 10;
            opacity: 0;
            animation: fadeIn 1s 0.5s forwards;
        }
        
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        
        /* Navigation buttons container */
        .buttons-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -45%);
            width: min(800px, 90vw);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: min(30px, 4vw);
            z-index: 10;
        }
        
        @media (max-width: 767px) {
            .buttons-container {
                grid-template-columns: 1fr;
                width: min(400px, 85vw);
                top: 42%;
            }
        }
        
        /* Navigation buttons */
        .nav-button {
            position: relative;
            height: 130px;
            background: linear-gradient(145deg, #e63946, #d62828);
            color: white;
            border-radius: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            overflow: hidden;
            text-decoration: none;
            opacity: 0;
            animation: slideIn 0.5s forwards;
        }
        
        .nav-button:nth-child(1) { animation-delay: 0.1s; }
        .nav-button:nth-child(2) { animation-delay: 0.2s; }
        .nav-button:nth-child(3) { animation-delay: 0.3s; }
        .nav-button:nth-child(4) { animation-delay: 0.4s; }
        .nav-button:nth-child(5) { animation-delay: 0.5s; }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .nav-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
        }
        
        .nav-button:before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            transition: 0.5s;
        }
        
        .nav-button:hover:before {
            left: 100%;
        }
        
        .button-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .button-text {
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            padding: 0 10px;
        }
        
        /* Baseball Stitches Background Effect */
        .stitches {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -5;
            overflow: hidden;
        }
        
        .stitch {
            position: absolute;
            width: 60px;
            height: 15px;
            background: rgba(255, 0, 0, 0.15);
            border-radius: 10px;
            box-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
            animation: floatStitch 20s infinite linear;
        }
        
        @keyframes floatStitch {
            0% {
                transform: rotate(var(--rotation)) translate(0, 100vh) scale(var(--scale));
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: rotate(var(--rotation)) translate(0, -100vh) scale(var(--scale));
                opacity: 0;
            }
        }
        
        /* Stadium crowd noise effect */
        .crowd-container {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 15vh;
            overflow: hidden;
            z-index: -7;
        }
        
        .crowd {
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(ellipse at center, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 70%);
            opacity: 0.2;
            animation: crowdNoise 3s infinite alternate;
        }
        
        @keyframes crowdNoise {
            0%, 100% { transform: scaleY(1); opacity: 0.2; }
            50% { transform: scaleY(1.05); opacity: 0.25; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the baseball-themed HTML structure
    landing_html = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <!-- Main background -->
    <div class="baseball-bg"></div>
    
    <!-- Stadium lights -->
    <div class="stadium-light"></div>
    <div class="stadium-light"></div>
    
    <!-- Moving baseball -->
    <div class="baseball"></div>
    
    <!-- Stitches floating effect -->
    <div class="stitches" id="stitchesContainer"></div>
    
    <!-- Stadium crowd effect -->
    <div class="crowd-container">
        <div class="crowd"></div>
    </div>
    
    <!-- Title and subtitle -->
    <h1 class="main-title">⚾ ABL Analytics</h1>
    <p class="subtitle">Advanced Baseball League Analysis</p>
    
    <!-- Navigation buttons -->
    <div class="buttons-container">
        <div id="league-info-btn" class="nav-button">
            <div class="button-icon">🏠</div>
            <div class="button-text">League Info</div>
        </div>
        
        <div id="team-rosters-btn" class="nav-button">
            <div class="button-icon">👥</div>
            <div class="button-text">Team Rosters</div>
        </div>
        
        <div id="power-rankings-btn" class="nav-button">
            <div class="button-icon">🏆</div>
            <div class="button-text">Power Rankings</div>
        </div>
        
        <div id="handbook-btn" class="nav-button">
            <div class="button-icon">📚</div>
            <div class="button-text">Handbook</div>
        </div>
        
        <div id="projected-rankings-btn" class="nav-button">
            <div class="button-icon">📈</div>
            <div class="button-text">Projected Rankings</div>
        </div>
    </div>
    
    <script>
        // Create and initialize all elements on page load
        window.addEventListener('load', function() {
            // Create random baseball stitches in the background
            const stitchesContainer = document.getElementById('stitchesContainer');
            if (stitchesContainer) {
                const numStitches = 30;
                
                for (let i = 0; i < numStitches; i++) {
                    const stitch = document.createElement('div');
                    stitch.classList.add('stitch');
                    
                    // Random position, scale, rotation, and animation delay
                    const left = Math.random() * 100;
                    const delay = Math.random() * 20;
                    const rotation = Math.random() * 360;
                    const scale = 0.5 + Math.random() * 1;
                    
                    stitch.style.left = `${left}%`;
                    stitch.style.animationDelay = `${delay}s`;
                    stitch.style.setProperty('--rotation', `${rotation}deg`);
                    stitch.style.setProperty('--scale', scale);
                    
                    stitchesContainer.appendChild(stitch);
                }
            }
            
            // Set up event listeners for all navigation buttons
            setupNavButtons();
        });
        
        // Function to handle navigation button clicks
        function handleNavClick(tabIndex) {
            // Add visual feedback on click
            this.style.transform = 'scale(0.95)';
            this.style.boxShadow = '0 3px 10px rgba(0, 0, 0, 0.2)';
            
            // Store the selected tab and trigger the enter app action
            try {
                console.log("Navigation clicked, tab index:", tabIndex);
                
                // Store tab index in session storage for app.py to read
                window.parent.sessionStorage.setItem('selectedTab', tabIndex);
                
                // Find and click the hidden enter app button
                setTimeout(() => {
                    try {
                        const streamlitDoc = window.parent.document;
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
            } catch (err) {
                console.error("Error handling navigation:", err);
            }
        }
        
        // Utility function to detect if we're on a mobile device
        function isMobileDevice() {
            return (typeof window.orientation !== "undefined") || (navigator.userAgent.indexOf('IEMobile') !== -1);
        }
        
        // Setup navigation buttons
        function setupNavButtons() {
            // Helper function to add both click and touch events
            function addClickAndTouchEvents(elementId, tabIndex) {
                const element = document.getElementById(elementId);
                if (!element) {
                    console.error(`Button element not found: ${elementId}`);
                    return;
                }
                
                // For desktop clicks
                element.addEventListener('click', function(e) {
                    handleNavClick.call(this, tabIndex);
                });
                
                // For mobile touches
                if (isMobileDevice()) {
                    element.addEventListener('touchstart', function(e) {
                        // Prevent default to avoid double-firing on some devices
                        e.preventDefault();
                        handleNavClick.call(this, tabIndex);
                    });
                }
                
                console.log(`Event handlers added for: ${elementId}`);
            }
            
            // Add handlers for all navigation buttons
            addClickAndTouchEvents('league-info-btn', 0);
            addClickAndTouchEvents('team-rosters-btn', 1);
            addClickAndTouchEvents('power-rankings-btn', 2);
            addClickAndTouchEvents('handbook-btn', 3);
            addClickAndTouchEvents('projected-rankings-btn', 4);
        }
    </script>
    """
    
    # Render the baseball field
    st.markdown(landing_html, unsafe_allow_html=True)
    
    # Hidden button that will be triggered by JavaScript (completely hidden from view)
    st.markdown('<div style="display:none; position:absolute; visibility:hidden; height:0; width:0; overflow:hidden;">', unsafe_allow_html=True)
    if st.button("ENTER APP", type="primary", key="hidden_enter"):
        st.session_state.entered_app = True
        time.sleep(0.3)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown