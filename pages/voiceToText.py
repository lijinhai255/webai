import streamlit as st

with open("static/index.html") as f:
    html_content = f.read()

st.markdown(html_content, unsafe_allow_html=True)