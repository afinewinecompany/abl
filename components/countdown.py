import streamlit as st
from datetime import datetime
import pytz

def render_countdown():
    """Render countdown timer and content blur until release time"""
    # Set release time to March 19th, 12:00 PM Eastern Time
    eastern = pytz.timezone('US/Eastern')
    release_time = eastern.localize(datetime(2025, 3, 19, 12, 0))
    current_time = datetime.now(eastern)
    
    # Calculate time remaining
    time_remaining = release_time - current_time
    
    # Check if content should be shown
    if current_time >= release_time:
        return False  # Content should be shown
        
    # If before release time, show countdown
    hours = time_remaining.days * 24 + time_remaining.seconds // 3600
    minutes = (time_remaining.seconds % 3600) // 60
    seconds = time_remaining.seconds % 60
    
    st.markdown("""
        <style>
        .content-blur {
            filter: blur(10px);
            pointer-events: none;
            user-select: none;
        }
        .countdown-container {
            background: linear-gradient(135deg, #1a1c23 0%, #2d2f36 100%);
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        }
        .countdown-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #ff4d4d 0%, #4169E1 50%, #ff4d4d 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% auto;
            animation: gradient 3s linear infinite;
        }
        .countdown-timer {
            font-size: 3.5rem;
            font-weight: 700;
            color: white;
            font-family: monospace;
            margin: 1rem 0;
        }
        .countdown-info {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        </style>
        
        <div class="countdown-container">
            <div class="countdown-title">Content Locked</div>
            <div class="countdown-timer">
                {:02d}:{:02d}:{:02d}
            </div>
            <div class="countdown-info">
                Content will be available on March 19th at 12:00 PM ET
            </div>
        </div>
    """.format(hours, minutes, seconds), unsafe_allow_html=True)
    
    return True  # Content should be blurred
