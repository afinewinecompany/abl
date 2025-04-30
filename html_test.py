import streamlit as st

st.title("HTML Test")

# Test simple HTML container
html_code = """
<div style="background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 5px; text-align: center; width: 100%; margin-top: 0.5rem;">
    <p style="margin: 0; color: white;">MVP Score: 82.1</p>
</div>
"""

st.markdown("### Test Basic HTML Container")
st.markdown(html_code, unsafe_allow_html=True)

# Test with different background
html_code2 = """
<div style="background: rgba(0,100,255,0.1); padding: 0.5rem; border-radius: 8px; text-align: center; width: 100%; margin-top: 1rem; border: 1px solid rgba(0,100,255,0.2);">
    <p style="margin: 0; color: white; font-weight: bold;">MVP Score: 82.1</p>
</div>
"""

st.markdown("### Test HTML Container with Different Styling")
st.markdown(html_code2, unsafe_allow_html=True)

# Test with more complex HTML
html_code3 = """
<div style="background: linear-gradient(135deg, #4a0072 0%, #9c0063 100%); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h3 style="color: white; margin: 0; font-size: 1.2rem;">Player Name</h3>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.9rem;">SP | LAD</p>
        </div>
        <div style="text-align: right;">
            <div style="background: rgba(0,0,0,0.3); padding: 0.3rem 0.6rem; border-radius: 12px;">
                <p style="margin: 0; color: white; font-weight: bold;">Score: 82.1</p>
            </div>
        </div>
    </div>
    <div style="margin-top: 0.8rem; background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 5px; text-align: center;">
        <p style="margin: 0; color: white;">Contract: 2035</p>
    </div>
</div>
"""

st.markdown("### Test Complex HTML Container")
st.markdown(html_code3, unsafe_allow_html=True)