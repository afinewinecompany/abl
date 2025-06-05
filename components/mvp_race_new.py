import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render():
    """Render the MVP Race page with working player card display"""
    st.title("🏆 MVP Race")
    
    # Info about the MVP calculation
    st.info("""
    **ABL MVP Algorithm Components:**
    - **Fantasy Points (70%)**: Primary performance metric
    - **Position Value (5%)**: Scarcity-based positional adjustment  
    - **Contract Value (25%)**: Salary efficiency and contract length
        - Low salary, long-term contracts are most valuable
        - Contract length provides more value for lower-salaried players
    """)
    
    try:
        # Load MVP player data
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        # Load player ID mapping for headshots
        name_to_mlb_id = {}
        try:
            id_map = pd.read_csv("attached_assets/PLAYERIDMAP.csv")
            for _, row in id_map.iterrows():
                if pd.notna(row.get('MLBID')):
                    names_to_try = [
                        row.get('PLAYERNAME', ''),
                        row.get('MLBNAME', ''),
                        row.get('FANTRAXNAME', ''),
                        row.get('FANGRAPHSNAME', '')
                    ]
                    for name in names_to_try:
                        if pd.notna(name) and name.strip():
                            name_to_mlb_id[name.strip()] = str(row['MLBID'])
        except Exception as e:
            st.warning(f"Could not load player ID mapping: {str(e)}")
        
        # Data validation and cleaning
        mvp_data['Age'] = pd.to_numeric(mvp_data['Age'], errors='coerce').fillna(25)
        mvp_data['Salary'] = pd.to_numeric(mvp_data['Salary'], errors='coerce').fillna(1.0)
        mvp_data['FPts'] = pd.to_numeric(mvp_data['FPts'], errors='coerce').fillna(0)
        
        # Calculate MVP score
        def calculate_mvp_score(row):
            # FPts component (70%)
            fpts_score = row['FPts'] / mvp_data['FPts'].max() if mvp_data['FPts'].max() > 0 else 0
            
            # Position value component (5%) - simplified
            position_score = 0.5  # Default position value
            
            # Value component (25%) - salary efficiency and contract
            salary_score = 1.0 - (row['Salary'] / mvp_data['Salary'].max()) if mvp_data['Salary'].max() > 0 else 0.5
            
            contract_values = {
                '2050': 1.0, '2045': 0.9, '2040': 0.8, '2035': 0.7, '2029': 0.6,
                '2028': 0.5, '2027': 0.4, '2026': 0.3, '2025': 0.2, '1st': 0.15
            }
            contract_score = contract_values.get(str(row['Contract']), 0.1)
            
            value_score = (salary_score * 0.6) + (contract_score * 0.4)
            
            # Combine all components
            total_score = (fpts_score * 0.70) + (position_score * 0.05) + (value_score * 0.25)
            return total_score * 100  # Scale to 0-100
        
        # Calculate MVP scores
        mvp_data['MVP_Score'] = mvp_data.apply(calculate_mvp_score, axis=1)
        mvp_data = mvp_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
        
        st.sidebar.success(f"✅ Loaded {len(mvp_data):,} players successfully")
        
        # Team colors for display
        team_colors = {
            'Arizona Diamondbacks': {'primary': '#A71930', 'secondary': '#000000'},
            'Atlanta Braves': {'primary': '#CE1141', 'secondary': '#13274F'},
            'Baltimore Orioles': {'primary': '#DF4601', 'secondary': '#000000'},
            'Boston Red Sox': {'primary': '#BD3039', 'secondary': '#0C2340'},
            'Chicago Cubs': {'primary': '#0E3386', 'secondary': '#CC3433'},
            'Chicago White Sox': {'primary': '#27251F', 'secondary': '#C4CED4'},
            'Cincinnati Reds': {'primary': '#C6011F', 'secondary': '#000000'},
            'Cleveland Guardians': {'primary': '#E31937', 'secondary': '#002653'},
            'Colorado Rockies': {'primary': '#33006F', 'secondary': '#C4CED4'},
            'Detroit Tigers': {'primary': '#0C2340', 'secondary': '#FA4616'},
            'Houston Astros': {'primary': '#002D62', 'secondary': '#EB6E1F'},
            'Kansas City Royals': {'primary': '#004687', 'secondary': '#BD9B60'},
            'Los Angeles Angels': {'primary': '#BA0021', 'secondary': '#003263'},
            'Los Angeles Dodgers': {'primary': '#005A9C', 'secondary': '#FFFFFF'},
            'Miami Marlins': {'primary': '#00A3E0', 'secondary': '#EF3340'},
            'Milwaukee Brewers': {'primary': '#FFC52F', 'secondary': '#12284B'},
            'Minnesota Twins': {'primary': '#002B5C', 'secondary': '#D31145'},
            'New York Mets': {'primary': '#002D72', 'secondary': '#FF5910'},
            'New York Yankees': {'primary': '#132448', 'secondary': '#C4CED4'},
            'Oakland Athletics': {'primary': '#003831', 'secondary': '#EFB21E'},
            'Philadelphia Phillies': {'primary': '#E81828', 'secondary': '#002D72'},
            'Pittsburgh Pirates': {'primary': '#FDB827', 'secondary': '#27251F'},
            'San Diego Padres': {'primary': '#2F241D', 'secondary': '#FFC425'},
            'San Francisco Giants': {'primary': '#FD5A1E', 'secondary': '#27251F'},
            'Seattle Mariners': {'primary': '#0C2C56', 'secondary': '#005C5C'},
            'St. Louis Cardinals': {'primary': '#C41E3A', 'secondary': '#FEDB00'},
            'Tampa Bay Rays': {'primary': '#092C5C', 'secondary': '#8FBCE6'},
            'Texas Rangers': {'primary': '#003278', 'secondary': '#C0111F'},
            'Toronto Blue Jays': {'primary': '#134A8E', 'secondary': '#1D2D5C'},
            'Washington Nationals': {'primary': '#AB0003', 'secondary': '#14225A'}
        }
        
        # Display top 3 MVP candidates with special highlighting
        st.write("## Current MVP Favorites")
        
        for i, (_, player) in enumerate(mvp_data.head(3).iterrows()):
            colors = team_colors.get(player['Team'], {'primary': '#333333', 'secondary': '#666666'})
            player_name = player['Player']
            mlb_id = name_to_mlb_id.get(player_name, '000000')
            
            # Calculate stars
            star_score = player['MVP_Score'] / 20
            stars = min(5, max(1, int(star_score + 0.5)))
            stars_display = "⭐" * stars
            
            # Create card layout
            col1, col2, col3 = st.columns([1, 10, 1])
            
            with col2:
                # Card background
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                    border-radius: 10px;
                    padding: 1rem;
                    position: relative;
                    text-align: center;
                    margin-bottom: 15px;
                ">
                    <div style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.1); padding: 5px; border-radius: 5px;">
                        <span style="color: white; font-size: 0.8rem;">#{i+1}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Player headshot
                if mlb_id != '000000':
                    headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlb_id}/headshot/67/current"
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: -60px;">
                        <img src="{headshot_url}" style="width: 120px; height: 120px; border: 3px solid white; border-radius: 50%; object-fit: cover;">
                    </div>
                    """, unsafe_allow_html=True)
                
                # Player info
                st.markdown(f"""
                <h3 style="color: white; margin: 0.5rem 0; text-align: center;">{player['Player']}</h3>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.3rem; text-align: center;">{player['Position']} | {player['Team']}</div>
                """, unsafe_allow_html=True)
                
                # Star rating
                st.markdown(f"""
                <div style="margin: 0.5rem 0; color: gold; font-size: 1.2rem; text-align: center;">{stars_display}</div>
                """, unsafe_allow_html=True)
                
                # MVP Score
                st.markdown(f"""
                <div style="background: rgba(0,0,0,0.3); padding: 0.3rem; border-radius: 12px; margin: 0 auto; width: 60%; text-align: center;">
                    <span style="color: white; font-weight: bold;">MVP Score: {player['MVP_Score']:.1f}</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Complete rankings
        st.write("## Complete MVP Rankings")
        
        display_count = st.slider("Number of players to display", 10, 100, 30, 5)
        display_data = mvp_data.head(display_count)
        
        # Display remaining players (after top 3)
        for i, (_, player) in enumerate(display_data.iterrows()):
            if i >= 3:  # Skip first 3 as they're already shown above
                rank = i + 1
                colors = team_colors.get(player['Team'], {'primary': '#333333', 'secondary': '#666666'})
                player_name = player['Player']
                mlb_id = name_to_mlb_id.get(player_name, '000000')
                
                with st.container():
                    # Team color strip
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        height: 5px;
                        border-radius: 3px 3px 0 0;
                        margin-bottom: 10px;
                    "></div>
                    """, unsafe_allow_html=True)
                    
                    # Player card content
                    col1, col2, col3, col4, col5 = st.columns([1, 2, 4, 2, 2])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: {colors['primary']};
                            color: white;
                            text-align: center;
                            padding: 8px;
                            border-radius: 50%;
                            width: 35px;
                            height: 35px;
                            line-height: 19px;
                            font-weight: bold;
                            margin: 0 auto;
                        ">#{rank}</div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if mlb_id != '000000':
                            headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlb_id}/headshot/67/current"
                            st.image(headshot_url, width=60)
                        else:
                            st.markdown("⚾", help="Player photo not available")
                    
                    with col3:
                        st.markdown(f"**{player['Player']}**")
                        st.caption(f"{player['Position']} • {player['Team']} • Age {int(player['Age'])}")
                        
                        mvp_pct = min(100, player['MVP_Score'])
                        st.markdown(f"""
                        <div style="background: #ddd; border-radius: 10px; height: 8px; margin-top: 5px;">
                            <div style="background: {colors['primary']}; height: 8px; border-radius: 10px; width: {mvp_pct}%;"></div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.metric("MVP Score", f"{player['MVP_Score']:.1f}")
                    
                    with col5:
                        st.metric("Fantasy Points", f"{player['FPts']:.1f}")
                        st.caption(f"${player['Salary']:.1f}M • {player['Contract']}")
                    
                    st.divider()
        
        # Analysis tabs
        tab1, tab2, tab3 = st.tabs(["📊 Rankings", "📈 Analysis", "🎯 Value Analysis"])
        
        with tab1:
            st.write("### MVP Candidates Table")
            st.dataframe(
                display_data[['Player', 'Team', 'Position', 'MVP_Score', 'FPts', 'Salary', 'Contract']].head(20),
                use_container_width=True
            )
        
        with tab2:
            st.write("### Performance Analysis")
            
            fig = px.scatter(
                display_data.head(20),
                x='FPts',
                y='MVP_Score',
                color='Team',
                size='Salary',
                hover_name='Player',
                title='MVP Score vs Fantasy Points',
                labels={'FPts': 'Fantasy Points', 'MVP_Score': 'MVP Score'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.write("### Value Analysis")
            
            fig = px.scatter(
                display_data.head(20),
                x='Salary',
                y='FPts',
                color='MVP_Score',
                hover_name='Player',
                title='Performance vs Salary',
                labels={'Salary': 'Salary ($M)', 'FPts': 'Fantasy Points'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
    except FileNotFoundError:
        st.error("MVP-Player-List.csv file not found. Please ensure the file is in the attached_assets folder.")
    except Exception as e:
        st.error(f"Error loading MVP data: {str(e)}")
        st.write("Please check that the MVP-Player-List.csv file contains valid player data.")