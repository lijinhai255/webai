import streamlit as st
from streamlit.components.v1 import html

html_content = open("static/index.html").read()
st.html(html_content, height=800)