import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects, projected_rankings
from utils import fetch_api_data

# This must be the first Streamlit command
st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add baseball particles animation and loading mascot
st.markdown("""
    <style>
    .stApp {
        background: rgba(26, 28, 35, 0.95);
        backdrop-filter: blur(5px);
    }
    #tsparticles {
        position: fixed;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: -1;
    }

    /* Loading Animation Styles */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }

    @keyframes swing {
        0% { transform: rotate(-5deg); }
        50% { transform: rotate(5deg); }
        100% { transform: rotate(-5deg); }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: none;
        opacity: 0;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: rgba(26, 28, 35, 0.95);
        z-index: 9999;
        transition: opacity 0.3s ease-in-out;
    }

    .mascot {
        width: 100px;
        height: 100px;
        position: relative;
        margin-bottom: 20px;
    }

    .baseball {
        width: 50px;
        height: 50px;
        background: white;
        border-radius: 50%;
        position: relative;
        animation: bounce 1s infinite;
    }

    .baseball::before,
    .baseball::after {
        content: '';
        position: absolute;
        background: #red;
        height: 2px;
        width: 100%;
        top: 50%;
        left: 0;
        transform: translateY(-50%);
    }

    .baseball::after {
        transform: translateY(-50%) rotate(90deg);
    }

    .bat {
        width: 10px;
        height: 60px;
        background: #8B4513;
        position: absolute;
        bottom: 0;
        left: 50%;
        transform-origin: bottom center;
        animation: swing 2s infinite;
    }

    .loading-text {
        color: white;
        font-size: 1.2rem;
        margin-top: 20px;
        font-family: 'Inter', sans-serif;
    }

    .loading-dots::after {
        content: '...';
        animation: dots 1.5s steps(4, end) infinite;
    }

    @keyframes dots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60% { content: '...'; }
        80%, 100% { content: ''; }
    }

    </style>
    <div id="loading-animation" class="loading-container">
        <div class="mascot">
            <div class="baseball"></div>
            <div class="bat"></div>
        </div>
        <div class="loading-text">
            Loading<span class="loading-dots"></span>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.9.3/tsparticles.bundle.min.js"></script>
    <div id="tsparticles"></div>
    <script>
    // Function to show/hide loading animation
    function toggleLoading(show) {
        const loader = document.getElementById('loading-animation');
        if (show) {
            loader.style.display = 'flex';
            // Use requestAnimationFrame to ensure display change is processed before opacity
            requestAnimationFrame(() => {
                loader.style.opacity = '1';
            });
        } else {
            loader.style.opacity = '0';
            // Wait for opacity transition to complete before hiding
            setTimeout(() => {
                loader.style.display = 'none';
            }, 300); // Match transition duration
        }
    }

    window.addEventListener('DOMContentLoaded', (event) => {
        tsParticles.load("tsparticles", {
            fpsLimit: 60,
            particles: {
                number: {
                    value: 40,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: ["#ffffff"]
                },
                shape: {
                    type: "circle"
                },
                opacity: {
                    value: 0.25,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 5,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 2,
                        size_min: 1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: "#ffffff",
                    opacity: 0.1,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: "none",
                    random: true,
                    straight: false,
                    out_mode: "bounce",
                    bounce: true,
                    attract: {
                        enable: true,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: "window",
                events: {
                    onhover: {
                        enable: true,
                        mode: ["grab", "bubble", "repulse"]
                    },
                    onclick: {
                        enable: true,
                        mode: "push"
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 200,
                        line_linked: {
                            opacity: 0.3
                        }
                    },
                    bubble: {
                        distance: 300,
                        size: 12,
                        duration: 2,
                        opacity: 0.2,
                        speed: 2
                    },
                    repulse: {
                        distance: 150,
                        duration: 0.4
                    },
                    push: {
                        particles_nb: 4
                    },
                    attract: {
                        distance: 200,
                        duration: 0.4,
                        factor: 5
                    }
                }
            },
            retina_detect: true,
            background: {
                color: "transparent",
                position: "50% 50%",
                repeat: "no-repeat",
                size: "cover"
            }
        });
    });
    </script>
""", unsafe_allow_html=True)

def main():
    st.title("⚾ ABL Analytics")

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
        # Fetch all data using the utility function
        data = fetch_api_data()

        if data:
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏠 League Info",
                "👥 Team Rosters",
                "🏆 Power Rankings",
                "📚 Handbook",
                "📈 Projected Rankings"
            ])

            with tab1:
                league_info.render(data['league_data'])

            with tab2:
                rosters.render(data['roster_data'])

            with tab3:
                power_rankings.render(data['standings_data'])

            with tab4:
                prospects.render(data['roster_data'])

            with tab5:
                projected_rankings.render(data['roster_data'])
        else:
            st.info("Using mock data for development...")

    except Exception as e:
        st.error(f"An error occurred while loading data: {str(e)}")
        st.info("Using mock data for development...")

if __name__ == "__main__":
    main()