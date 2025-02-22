
import streamlit as st
from streamlit.components.v1 import html

# 读取外部HTML文件
with open("static/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# 渲染HTML内容
html(html_content, height=600)