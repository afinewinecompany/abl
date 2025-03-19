import streamlit as st
from typing import Dict

def render(league_data: Dict):
    """Render league information section"""
    # Add welcome section with animations
    st.markdown("""
        <style>
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .welcome-container {
            background: linear-gradient(135deg, #1a1c23 0%, #2d2f36 50%, #1a1c23 100%);
            background-size: 200% 200%;
            animation: gradientBG 10s ease infinite;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            text-align: center;
        }
        .welcome-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: white;
            margin-bottom: 1rem;
            animation: fadeInUp 1s ease;
        }
        .welcome-text {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            animation: fadeInUp 1s ease 0.3s forwards;
            opacity: 0;
        }
        </style>

        <div class="welcome-container">
            <div class="welcome-title">Welcome to your Dynasty Analytics Dashboard</div>
            <div class="welcome-text">
                Here you can find your Roster, In Season Power Rank, Prospect Handbook, and Preseason Projected Rank!
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.header("League Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("League Name", league_data['name'])
        st.metric("Season", league_data['season'])

    with col2:
        st.metric("Number of Teams", league_data['teams'])
        st.metric("Sport", league_data['sport'])

    with col3:
        st.metric("Draft Type", league_data['scoring_type'])
        st.metric("Scoring Period", league_data['scoring_period'])

    st.divider()