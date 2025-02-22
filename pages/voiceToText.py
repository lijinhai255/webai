import streamlit as st

# 从 static 目录加载完整的 HTML 文件
html_content = open("static/index.html").read()

# 使用 st.components.html 渲染 HTML
st.components.html(html_content, height=800)