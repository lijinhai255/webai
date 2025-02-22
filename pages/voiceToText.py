import streamlit as st
import websocket
import datetime
import hashlib
import base64
import hmac
import json
import time
import threading
import queue
from urllib.parse import urlencode
import requests
from langchain.schema import HumanMessage
from LLM.chat_glm4 import ChatGLM4

# Xunfei API credentials
APPID = "your_appid"
APISecret = "your_api_secret"
APIKey = "your_api_key"

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        
    # ... (保持 XunfeiSTT 类的其他方法不变)

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化语音识别和模型
    stt = XunfeiSTT()
    chat_glm = ChatGLM4()
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 添加语音识别控制按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🎤 开始/停止语音识别"):
            if not stt.is_running:
                threading.Thread(target=stt.start_listening).start()
                st.success("✅ 语音识别已启动")
            else:
                stt.is_running = False
                st.warning("⚠️ 语音识别已停止")

    # 文本输入框
    user_input = st.chat_input("输入文字或使用语音...")

    # 处理文本输入
    if user_input:
        process_input(user_input, chat_glm)

    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # 处理语音识别结果
    if stt.is_running:
        try:
            while True:
                text = stt.text_queue.get_nowait()
                process_input(text, chat_glm)
                st.experimental_rerun()
        except queue.Empty:
            pass

def process_input(text, chat_glm):
    """处理输入文本并获取模型响应"""
    # 添加用户输入到历史记录
    st.session_state.chat_history.append({
        "role": "user",
        "content": text
    })
    
    # 显示用户输入
    with st.chat_message("user"):
        st.markdown(text)

    # 获取模型响应
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_text = ""
        
        # 使用 ChatGLM4 的流式响应
        for chunk in chat_glm.stream([HumanMessage(content=text)]):
            response_text += str(chunk)
            response_placeholder.markdown(response_text)
        
        # 添加助手响应到历史记录
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text
        })

if __name__ == "__main__":
    main()