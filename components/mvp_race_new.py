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
        mvp_data['Age'] = pd.to_numeric(mvp_data['Age'], errors='coerce')
        mvp_data['Salary'] = pd.to_numeric(mvp_data['Salary'], errors='coerce')
        mvp_data['FPts'] = pd.to_numeric(mvp_data['FPts'], errors='coerce')
        mvp_data['FP/G'] = pd.to_numeric(mvp_data['FP/G'], errors='coerce')
        
        # Remove rows with missing critical data
        mvp_data = mvp_data.dropna(subset=['Player', 'FPts'])
        
        st.success(f"✅ Loaded {len(mvp_data):,} players successfully")
        
        # Calculate simplified MVP Score (just based on FPts for now)
        mvp_data['MVP_Score'] = mvp_data['FPts']
        mvp_data = mvp_data.sort_values('MVP_Score', ascending=False).reset_index(drop=True)
        
        # Display top MVP candidates
        st.write("## Current MVP Favorites")
        
        top_10 = mvp_data.head(10)
        
        for i, (_, player) in enumerate(top_10.iterrows()):
            with st.container():
                col1, col2, col3 = st.columns([1, 6, 2])
                
                with col1:
                    st.markdown(f"### #{i+1}")
                
                with col2:
                    st.markdown(f"**{player['Player']}** ({player['Team']})")
                    st.write(f"{player['Position']} • ${player['Salary']}M • {player['Contract']}")
                
                with col3:
                    st.metric("Fantasy Points", f"{player['FPts']:.1f}")
                
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
            st.write("### Performance Analysis")
            
            # Fantasy Points distribution
            fig = px.histogram(
                mvp_data.head(100),
                x='FPts',
                nbins=20,
                title='Fantasy Points Distribution (Top 100 Players)',
                labels={'FPts': 'Fantasy Points', 'count': 'Number of Players'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Age vs Performance scatter
            fig2 = px.scatter(
                mvp_data.head(50),
                x='Age',
                y='FPts',
                size='Salary',
                color='Team',
                hover_name='Player',
                title='Age vs Performance (Top 50 Players)',
                labels={'Age': 'Player Age', 'FPts': 'Fantasy Points'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            st.write("### Value Analysis")
            
            # Salary vs Performance
            fig3 = px.scatter(
                mvp_data.head(100),
                x='Salary',
                y='FPts',
                size='Age',
                color='Contract',
                hover_name='Player',
                title='Salary vs Performance Analysis',
                labels={'Salary': 'Salary ($ Millions)', 'FPts': 'Fantasy Points'}
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Value insights
            st.write("#### Value Insights")
            
            # Best value players (high FPts, low salary)
            mvp_data['Value_Score'] = mvp_data['FPts'] / (mvp_data['Salary'] + 1)  # +1 to avoid division by zero
            best_value = mvp_data.nlargest(10, 'Value_Score')[['Player', 'Team', 'FPts', 'Salary', 'Value_Score']]
            
            st.write("**Best Value Players (Fantasy Points per $ Salary):**")
            st.dataframe(best_value, use_container_width=True, hide_index=True)
    
    except FileNotFoundError:
        st.error("MVP-Player-List.csv file not found. Please ensure the file is in the attached_assets folder.")
    except Exception as e:
        st.error(f"Error loading MVP data: {str(e)}")
        st.write("Please check that the MVP-Player-List.csv file contains valid player data.")