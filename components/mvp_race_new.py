import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render():
    """Render the MVP Race page with simplified implementation"""
    
    st.title("🏆 MVP Race Tracker")
    
    st.write("""
    ## Armchair Baseball League Most Valuable Player
    
    This tool analyzes player performance, value, and impact to determine the MVP race leaders.
    Each player is evaluated based on their performance (FPts), position value, and overall team value.
    
    ### MVP Score Components:
    - **FPts (70%)**: Fantasy points scoring is the primary performance metric
    - **Position (5%)**: Position value based on scarcity and fantasy points production
    - **Value (25%)**: Combined measure of salary and contract length
        - Low salary, long-term contracts are most valuable
        - Contract length provides more value for lower-salaried players
    """)
    
    try:
        # Load MVP player data
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        # Data validation and cleaning
        mvp_data['Age'] = pd.to_numeric(mvp_data['Age'], errors='coerce').fillna(25)
        mvp_data['Salary'] = pd.to_numeric(mvp_data['Salary'], errors='coerce').fillna(1.0)
        mvp_data['FPts'] = pd.to_numeric(mvp_data['FPts'], errors='coerce').fillna(0)
        mvp_data['FP/G'] = pd.to_numeric(mvp_data['FP/G'], errors='coerce').fillna(0)
        
        # Clean string fields
        mvp_data['Player'] = mvp_data['Player'].fillna('Unknown Player')
        mvp_data['Team'] = mvp_data['Team'].fillna('FA')
        mvp_data['Position'] = mvp_data['Position'].fillna('UT')
        mvp_data['Contract'] = mvp_data['Contract'].fillna('1st')
        
        # Remove rows with missing critical data
        mvp_data = mvp_data.dropna(subset=['Player'])
        
        st.success(f"✅ Loaded {len(mvp_data):,} players successfully")
        
        # Calculate MVP Score based on the three components
        def calculate_mvp_score(row):
            # Component 1: Fantasy Points (70%) - normalized to 0-1 scale
            fpts_score = row['FPts'] / mvp_data['FPts'].max()
            
            # Component 2: Position Value (5%) - based on positional scarcity
            position_values = {
                'C': 1.0, 'SS': 0.9, '2B': 0.8, '3B': 0.7, 'CF': 0.6,
                'LF': 0.5, 'RF': 0.5, '1B': 0.4, 'SP': 0.8, 'RP': 0.3, 'UT': 0.6
            }
            # Get primary position (first one listed)
            primary_pos = row['Position'].split(',')[0].strip() if pd.notna(row['Position']) else 'UT'
            position_score = position_values.get(primary_pos, 0.5)
            
            # Component 3: Value Score (25%) - combination of salary and contract
            # Lower salary is better, longer contracts are better
            salary_score = 1.0 - (row['Salary'] / mvp_data['Salary'].max())
            
            contract_values = {
                '2050': 1.0, '2045': 0.9, '2040': 0.8, '2035': 0.7, '2029': 0.6,
                '2028': 0.5, '2027': 0.4, '2026': 0.3, '2025': 0.2, '1st': 0.15
            }
            contract_score = contract_values.get(str(row['Contract']), 0.1)
            
            # Combine salary and contract for value score
            value_score = (salary_score * 0.6) + (contract_score * 0.4)
            
            # Calculate final MVP Score (weighted combination)
            mvp_score = (fpts_score * 0.70) + (position_score * 0.05) + (value_score * 0.25)
            
            return mvp_score * 100  # Scale to 0-100
        
        mvp_data['MVP_Score'] = mvp_data.apply(calculate_mvp_score, axis=1)
        mvp_data = mvp_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
        
        # Display top MVP candidates as cards
        st.write("## Current MVP Favorites")
        
        top_10 = mvp_data.head(10)
        
        for i, (_, player) in enumerate(top_10.iterrows()):
            with st.container():
                # Create columns for the card layout
                col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
                
                with col1:
                    st.markdown(f"### #{i+1}")
                
                with col2:
                    st.markdown(f"**{player['Player']}**")
                    st.caption(f"{player['Position']} • {player['Team']} • Age {int(player['Age'])}")
                
                with col3:
                    st.metric("MVP Score", f"{player['MVP_Score']:.1f}")
                
                with col4:
                    st.metric("Fantasy Points", f"{player['FPts']:.1f}")
                    st.caption(f"${player['Salary']:.1f}M • {player['Contract']}")
                
                st.divider()
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Rankings", "📈 Analysis", "🎯 Value Analysis"])
        
        with tab1:
            st.write("### Complete MVP Rankings")
            
            # Display filters
            col1, col2 = st.columns(2)
            
            with col1:
                teams = sorted(mvp_data['Team'].unique())
                selected_team = st.selectbox("Filter by Team", ["All Teams"] + teams)
            
            with col2:
                # Get all positions
                all_positions = []
                for pos_list in mvp_data['Position'].str.split(','):
                    if pd.notna(pos_list):
                        all_positions.extend([p.strip() for p in pos_list])
                unique_positions = sorted(list(set(all_positions)))
                selected_position = st.selectbox("Filter by Position", ["All Positions"] + unique_positions)
            
            # Apply filters
            filtered_data = mvp_data.copy()
            
            if selected_team != "All Teams":
                filtered_data = filtered_data[filtered_data['Team'] == selected_team]
            
            if selected_position != "All Positions":
                filtered_data = filtered_data[filtered_data['Position'].str.contains(selected_position, na=False)]
            
            # Display filtered results
            display_columns = ['Player', 'Team', 'Position', 'FPts', 'Salary', 'Contract', 'Age']
            st.dataframe(
                filtered_data[display_columns].head(50),
                use_container_width=True,
                hide_index=True
            )
        
        with tab2:
            st.write("### MVP Score Component Analysis")
            
            # Calculate individual component scores for visualization
            mvp_data['FPts_Component'] = (mvp_data['FPts'] / mvp_data['FPts'].max()) * 70
            mvp_data['Position_Component'] = mvp_data['Position'].apply(lambda pos: {
                'C': 5.0, 'SS': 4.5, '2B': 4.0, '3B': 3.5, 'CF': 3.0,
                'LF': 2.5, 'RF': 2.5, '1B': 2.0, 'SP': 4.0, 'RP': 1.5, 'UT': 3.0
            }.get(pos.split(',')[0].strip() if pd.notna(pos) else 'UT', 2.5))
            
            # Value component calculation for visualization
            salary_normalized = 1.0 - (mvp_data['Salary'] / mvp_data['Salary'].max())
            contract_scores = mvp_data['Contract'].apply(lambda c: {
                '2050': 1.0, '2045': 0.9, '2040': 0.8, '2035': 0.7, '2029': 0.6,
                '2028': 0.5, '2027': 0.4, '2026': 0.3, '2025': 0.2, '1st': 0.15
            }.get(str(c), 0.1))
            mvp_data['Value_Component'] = ((salary_normalized * 0.6) + (contract_scores * 0.4)) * 25
            
            # MVP Score Component Breakdown (Top 15 players)
            top_15 = mvp_data.head(15)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Fantasy Points (70%)',
                x=top_15['Player'],
                y=top_15['FPts_Component'],
                marker_color='#1f77b4'
            ))
            
            fig.add_trace(go.Bar(
                name='Position Value (5%)',
                x=top_15['Player'],
                y=top_15['Position_Component'],
                marker_color='#ff7f0e'
            ))
            
            fig.add_trace(go.Bar(
                name='Contract Value (25%)',
                x=top_15['Player'],
                y=top_15['Value_Component'],
                marker_color='#2ca02c'
            ))
            
            fig.update_layout(
                title='MVP Score Component Breakdown (Top 15 Players)',
                xaxis_title='Player',
                yaxis_title='Component Score',
                barmode='stack',
                height=500,
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Age vs MVP Score scatter
            fig2 = px.scatter(
                mvp_data.head(50),
                x='Age',
                y='MVP_Score',
                size='Salary',
                color='Team',
                hover_name='Player',
                hover_data=['FPts', 'Position', 'Contract'],
                title='Age vs MVP Score (Top 50 Players)',
                labels={'Age': 'Player Age', 'MVP_Score': 'MVP Score'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            st.write("### Value Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # MVP Score vs Salary
                fig3 = px.scatter(
                    mvp_data.head(100),
                    x='Salary',
                    y='MVP_Score',
                    size='FPts',
                    color='Contract',
                    hover_name='Player',
                    hover_data=['FPts', 'Position', 'Age'],
                    title='MVP Score vs Salary',
                    labels={'Salary': 'Salary ($ Millions)', 'MVP_Score': 'MVP Score'}
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                # Contract distribution pie chart
                contract_counts = mvp_data.head(100)['Contract'].value_counts()
                fig4 = px.pie(
                    values=contract_counts.values,
                    names=contract_counts.index,
                    title='Contract Distribution (Top 100 Players)'
                )
                st.plotly_chart(fig4, use_container_width=True)
            
            # Value insights
            st.write("#### MVP Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Best Value MVP Candidates**")
                # Players with high MVP Score but lower salaries
                mvp_data['Value_Ratio'] = mvp_data['MVP_Score'] / (mvp_data['Salary'] + 0.1)
                best_value = mvp_data.nlargest(8, 'Value_Ratio')[['Player', 'Team', 'MVP_Score', 'Salary', 'Contract']]
                
                for _, player in best_value.iterrows():
                    st.write(f"**{player['Player']}** ({player['Team']})")
                    st.write(f"MVP: {player['MVP_Score']:.1f} • ${player['Salary']}M • {player['Contract']}")
                    st.write("---")
            
            with col2:
                st.write("**Highest MVP Scores**")
                top_mvp = mvp_data.head(8)[['Player', 'Team', 'MVP_Score', 'FPts']]
                
                for _, player in top_mvp.iterrows():
                    st.write(f"**{player['Player']}** ({player['Team']})")
                    st.write(f"MVP: {player['MVP_Score']:.1f} • {player['FPts']:.1f} FPts")
                    st.write("---")
            
            with col3:
                st.write("**Position Leaders**")
                # Top MVP by position
                position_leaders = []
                for pos in ['C', 'SS', '2B', '3B', '1B', 'OF', 'SP', 'RP']:
                    if pos == 'OF':
                        pos_data = mvp_data[mvp_data['Position'].str.contains('LF|RF|CF', na=False)]
                    else:
                        pos_data = mvp_data[mvp_data['Position'].str.contains(pos, na=False)]
                    
                    if not pos_data.empty:
                        leader = pos_data.iloc[0]
                        st.write(f"**{pos}:** {leader['Player']}")
                        st.write(f"MVP: {leader['MVP_Score']:.1f}")
                        st.write("---")
    
    except FileNotFoundError:
        st.error("MVP-Player-List.csv file not found. Please ensure the file is in the attached_assets folder.")
    except Exception as e:
        st.error(f"Error loading MVP data: {str(e)}")
        st.write("Please check that the MVP-Player-List.csv file contains valid player data.")