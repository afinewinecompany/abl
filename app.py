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

# Add baseball particles animation
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
    .status-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(26, 28, 35, 0.8);
        padding: 0.5rem;
        font-size: 0.8rem;
        z-index: 1000;
        opacity: 0;
        transform: translateY(100%);
        transition: all 0.3s ease;
    }
    .status-container.visible {
        opacity: 1;
        transform: translateY(0);
    }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.9.3/tsparticles.bundle.min.js"></script>
    <div id="tsparticles"></div>
    <script>
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
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 League Info",
            "👥 Team Rosters",
            "🏆 Power Rankings",
            "📚 Handbook",
            "📈 Projected Rankings"
        ])

        # Create a status container at the bottom
        status_container = st.empty()

        # Update status message with loading
        status_container.markdown(
            '<div class="status-container visible">⌛ Loading data...</div>',
            unsafe_allow_html=True
        )

        try:
            # Fetch data
            data = fetch_api_data()

            # Update status for success
            status_container.markdown(
                '<div class="status-container visible">✅ Data loaded successfully!</div>',
                unsafe_allow_html=True
            )

            # Clear status after brief delay
            import time
            time.sleep(1)
            status_container.empty()

            if data:
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
            # Update status for error
            status_container.markdown(
                f'<div class="status-container visible">❌ Error: {str(e)}</div>',
                unsafe_allow_html=True
            )
            time.sleep(3)  # Show error message longer
            status_container.empty()
            st.error(f"An error occurred while loading data: {str(e)}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Using mock data for development...")

if __name__ == "__main__":
    main()