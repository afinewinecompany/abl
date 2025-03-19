import streamlit as st

def render():
    """Render loading animation"""
    st.markdown("""
        <style>
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background: linear-gradient(135deg, #1a1c23 0%, #2d2f36 100%);
        }
        .baseball {
            width: 60px;
            height: 60px;
            background: white;
            border-radius: 50%;
            position: relative;
            animation: bounce 1s ease-in-out infinite;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .baseball::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid #cc0000;
            border-style: double;
            box-sizing: border-box;
            animation: rotate 2s linear infinite;
        }
        .loading-text {
            margin-top: 2rem;
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            text-align: center;
        }
        </style>
        <div class="loading-container">
            <div class="baseball"></div>
            <div class="loading-text">Loading ABL Data...</div>
        </div>
    """, unsafe_allow_html=True)
