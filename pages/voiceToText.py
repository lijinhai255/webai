import streamlit as st

html_content = """
<div id="test">
  <h1>Hello World!</h1>
</div>
"""
st.html(html_content, unsafe_allow_html=True)