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
    
    # Baseball field CSS
    st.markdown("""
    <style>
        /* Hide main app components initially */
        div.block-container {
            padding-top: 0;
        }
        
        /* Baseball field container */
        .baseball-field-container {
            position: relative;
            margin: 0 auto;
            width: 100%;
            max-width: 800px;
            height: 650px;
            perspective: 1000px;
        }
        
        /* Baseball field */
        .baseball-field {
            position: relative;
            width: 100%;
            height: 100%;
            background: linear-gradient(#2b8a3e, #2b8a3e);
            border-radius: 50% 50% 0 0;
            overflow: hidden;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);
            transform-style: preserve-3d;
            transform: rotateX(30deg);
            transition: transform 0.5s ease-in-out;
        }
        
        .baseball-field:hover {
            transform: rotateX(25deg);
        }
        
        /* Infield dirt */
        .infield {
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 70%;
            height: 70%;
            background: #b9895c;
            border-radius: 50% 50% 0 0;
            overflow: hidden;
        }
        
        /* Bases */
        .base {
            position: absolute;
            width: 30px;
            height: 30px;
            background: white;
            border: 2px solid #333;
            transform: rotate(45deg);
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        
        .home-plate {
            bottom: 5%;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 40px;
            background: white;
            clip-path: polygon(0 30%, 50% 0, 100% 30%, 100% 100%, 0 100%);
            transform: none;
            box-shadow: 0 0 15px rgba(255,255,255,0.5);
        }
        
        .first-base {
            bottom: 35%;
            right: 25%;
        }
        
        .second-base {
            bottom: 55%;
            left: 50%;
            transform: translateX(-50%) rotate(45deg);
        }
        
        .third-base {
            bottom: 35%;
            left: 25%;
        }
        
        /* Pitcher's mound */
        .pitchers-mound {
            position: absolute;
            bottom: 30%;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 40px;
            background: #b9895c;
            border: 3px solid #987654;
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        
        /* Base paths */
        .base-path {
            position: absolute;
            background: #c9a97c;
            height: 15px;
        }
        
        .home-to-first {
            width: 25%;
            bottom: 20%;
            right: 30%;
            transform: rotate(45deg);
        }
        
        .first-to-second {
            width: 25%;
            bottom: 45%;
            right: 38%;
            transform: rotate(135deg);
        }
        
        .second-to-third {
            width: 25%;
            bottom: 45%;
            left: 38%;
            transform: rotate(45deg);
        }
        
        .third-to-home {
            width: 25%;
            bottom: 20%;
            left: 30%;
            transform: rotate(135deg);
        }
        
        /* Outfield grass patterns */
        .grass-pattern {
            position: absolute;
            background: rgba(255, 255, 255, 0.05);
            width: 100%;
            height: 20px;
        }
        
        .grass-pattern:nth-child(odd) {
            background: rgba(0, 0, 0, 0.05);
        }
        
        /* Field positions with players (as circles) */
        .player {
            position: absolute;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            text-decoration: none;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
            border: 3px solid white;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            z-index: 10;
            font-size: 14px;
            text-align: center;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            animation: pulse 2s infinite;
        }
        
        .player:hover {
            transform: scale(1.15);
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.6);
            z-index: 20;
        }
        
        /* Player positions */
        .pitcher {
            bottom: 32%;
            left: 50%;
            transform: translateX(-50%);
            animation-delay: 0s;
        }
        
        .first-baseman {
            bottom: 35%;
            right: 32%;
            animation-delay: 0.2s;
        }
        
        .second-baseman {
            bottom: 45%;
            right: 38%;
            animation-delay: 0.4s;
        }
        
        .third-baseman {
            bottom: 35%;
            left: 32%;
            animation-delay: 0.6s;
        }
        
        .shortstop {
            bottom: 45%;
            left: 38%;
            animation-delay: 0.8s;
        }
        
        /* Title and enter button styles */
        .field-title {
            font-size: 3rem;
            color: white;
            text-align: center;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5), 0 0 20px rgba(255, 0, 0, 0.6);
            margin-bottom: 2rem;
            animation: glow 2s infinite alternate;
        }
        
        .enter-button {
            display: block;
            margin: 2rem auto;
            padding: 1rem 2rem;
            background: linear-gradient(145deg, #ff3030, #d42a2a);
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);
            transition: all 0.3s ease;
            text-align: center;
            max-width: 200px;
            text-decoration: none;
        }
        
        .enter-button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
        }
        
        /* Animations */
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
        
        @keyframes glow {
            from {
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5), 0 0 20px rgba(255, 0, 0, 0.6);
            }
            to {
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5), 0 0 30px rgba(255, 0, 0, 0.9);
            }
        }
        
        /* Clouds in the sky */
        .cloud {
            position: absolute;
            width: 100px;
            height: 50px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 50px;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
            animation: float-cloud 20s infinite linear;
            top: 10%;
            opacity: 0.7;
        }
        
        .cloud:before, .cloud:after {
            content: '';
            position: absolute;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 50%;
        }
        
        .cloud:before {
            width: 50px;
            height: 50px;
            top: -20px;
            left: 15px;
        }
        
        .cloud:after {
            width: 70px;
            height: 70px;
            top: -30px;
            right: 15px;
        }
        
        .cloud:nth-child(1) {
            left: 10%;
            animation-duration: 30s;
        }
        
        .cloud:nth-child(2) {
            left: 50%;
            top: 5%;
            transform: scale(1.5);
            animation-duration: 35s;
            animation-delay: -15s;
        }
        
        .cloud:nth-child(3) {
            right: 10%;
            animation-duration: 25s;
            animation-delay: -5s;
        }
        
        @keyframes float-cloud {
            0% {
                transform: translateX(-150px);
            }
            100% {
                transform: translateX(calc(100vw + 150px));
            }
        }
        
        /* Ball animation */
        .baseball {
            position: absolute;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            border: 1px solid #888;
            box-shadow: 0 0 10px rgba(255,255,255,0.5);
            z-index: 5;
            display: none;
        }
        
        .curve-path {
            position: absolute;
            border: 2px dashed rgba(255,255,255,0.3);
            border-radius: 50%;
            width: 200px;
            height: 100px;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1;
            display: none;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .baseball-field-container {
                height: 500px;
            }
            
            .player {
                width: 45px;
                height: 45px;
                font-size: 11px;
            }
            
            .field-title {
                font-size: 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # JavaScript for animations and interactivity
    st.markdown("""
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Add animation for ball throwing when hovering over pitcher
            const pitcher = document.querySelector('.pitcher');
            const baseball = document.querySelector('.baseball');
            const curvePath = document.querySelector('.curve-path');
            
            if (pitcher && baseball && curvePath) {
                pitcher.addEventListener('mouseenter', function() {
                    baseball.style.display = 'block';
                    curvePath.style.display = 'block';
                    
                    // Animate the ball
                    baseball.style.transition = 'none';
                    baseball.style.bottom = '32%';
                    baseball.style.left = '50%';
                    baseball.style.transform = 'translate(-50%, 0)';
                    
                    setTimeout(() => {
                        baseball.style.transition = 'all 1s cubic-bezier(.17,.67,.83,.67)';
                        baseball.style.bottom = '5%';
                        baseball.style.transform = 'translate(-50%, 0) rotate(720deg)';
                    }, 100);
                });
                
                pitcher.addEventListener('mouseleave', function() {
                    setTimeout(() => {
                        baseball.style.display = 'none';
                        curvePath.style.display = 'none';
                    }, 1000);
                });
            }
            
            // Make players throw animations when clicked
            document.querySelectorAll('.player').forEach(player => {
                player.addEventListener('click', function(e) {
                    // Don't navigate immediately, play animation first
                    e.preventDefault();
                    const href = this.getAttribute('href');
                    
                    this.style.transform = 'scale(1.2) translateY(-10px)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                        setTimeout(() => {
                            window.location.href = href;
                        }, 300);
                    }, 300);
                });
            });
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Main title
    st.markdown('<h1 class="field-title">⚾ ABL Analytics Field</h1>', unsafe_allow_html=True)
    
    # Enter app button (center of the screen)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("ENTER APP", key="enter_app", use_container_width=True):
            st.session_state.entered_app = True
            time.sleep(0.5)  # Small delay for transition
            st.experimental_rerun()
    
    # Create the baseball field HTML
    field_html = """
    <div class="baseball-field-container">
        <div class="baseball-field">
            <!-- Sky elements -->
            <div class="cloud"></div>
            <div class="cloud"></div>
            <div class="cloud"></div>
            
            <!-- Infield dirt -->
            <div class="infield"></div>
            
            <!-- Base paths -->
            <div class="base-path home-to-first"></div>
            <div class="base-path first-to-second"></div>
            <div class="base-path second-to-third"></div>
            <div class="base-path third-to-home"></div>
            
            <!-- Bases -->
            <div class="base home-plate"></div>
            <div class="base first-base"></div>
            <div class="base second-base"></div>
            <div class="base third-base"></div>
            
            <!-- Pitcher's mound -->
            <div class="pitchers-mound"></div>
            
            <!-- Ball and path elements for animation -->
            <div class="baseball"></div>
            <div class="curve-path"></div>
            
            <!-- Players linking to app sections -->
            <a class="player pitcher" data-section="power_rankings">
                🏆<br>Power Rankings
            </a>
            <a class="player first-baseman" data-section="league_info">
                🏠<br>League Info
            </a>
            <a class="player second-baseman" data-section="team_rosters">
                👥<br>Team Rosters
            </a>
            <a class="player third-baseman" data-section="handbook">
                📚<br>Handbook
            </a>
            <a class="player shortstop" data-section="projected_rankings">
                📈<br>Projected
            </a>
        </div>
    </div>
    
    <script>
        // Set up click handlers for each player position to set the active tab
        document.addEventListener('DOMContentLoaded', function() {
            const players = document.querySelectorAll('.player');
            players.forEach(player => {
                player.addEventListener('click', function() {
                    const section = this.getAttribute('data-section');
                    // Store the selected section in localStorage
                    localStorage.setItem('selectedSection', section);
                    
                    // Trigger the enter app button click
                    document.querySelector('button[data-testid="baseButton-primary"]').click();
                });
            });
        });
    </script>
    """
    
    # Display the baseball field
    st.markdown(field_html, unsafe_allow_html=True)
    
    # Add JavaScript to select tabs based on player selection
    st.markdown("""
    <script>
        // Function to click the appropriate tab based on selected section
        function clickSelectedTab() {
            const selectedSection = localStorage.getItem('selectedSection');
            if (!selectedSection) return;
            
            // Map sections to tab indices
            const sectionToIndex = {
                'league_info': 0,
                'team_rosters': 1,
                'power_rankings': 2,
                'handbook': 3,
                'projected_rankings': 4
            };
            
            const index = sectionToIndex[selectedSection];
            if (index !== undefined) {
                // Find all tabs and click the one at the specified index
                const tabs = document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs && tabs.length > index) {
                    setTimeout(() => {
                        tabs[index].click();
                        // Clear the selection after use
                        localStorage.removeItem('selectedSection');
                    }, 500);
                }
            }
        }
        
        // Run when DOM is fully loaded
        document.addEventListener('DOMContentLoaded', clickSelectedTab);
        
        // Also run when the page is shown after animation
        window.addEventListener('load', function() {
            setTimeout(clickSelectedTab, 1000);
        });
    </script>
    """, unsafe_allow_html=True)
    
    return True  # Return True to indicate the landing page is being shown