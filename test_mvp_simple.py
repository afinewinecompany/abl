import streamlit as st
import pandas as pd

def test_mvp_simple():
    """Simple test version of MVP Race to identify the issue"""
    st.title("🏆 MVP Race Test")
    
    try:
        # Load MVP data
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        st.success(f"✅ Loaded {len(mvp_data)} players")
        
        # Show basic data
        st.write("### Top 10 Players by Fantasy Points")
        top_players = mvp_data.nlargest(10, 'FPts')[['Player', 'Team', 'Position', 'FPts', 'Salary']]
        st.dataframe(top_players)
        
        # Show data summary
        st.write("### Data Summary")
        st.write(f"Total Players: {len(mvp_data)}")
        st.write(f"Columns: {list(mvp_data.columns)}")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    test_mvp_simple()