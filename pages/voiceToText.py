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
import pyaudio
import wave
from urllib.parse import urlencode
from langchain.schema import HumanMessage
# Assuming ChatGLM4 is a custom module you have access to
from LLM.chatglm4 import ChatGLM4

# Your Xunfei API credentials
APPID = "f815c988"
APISecret = "ODMwNTc2NDNiOGZiZGZjMTkzNzdhNTc3"
APIKey = "657bfe10ef10741f60de4dc728c53353"

class XunfeiSTT:
    def __init__(self):
        self.wsurl = "wss://iat-api.xfyun.cn/v2/iat"
        self.textqueue = queue.Queue()
        self.isrunning = False
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        # Initialize other necessary attributes and methods

    # Define other methods for the XunfeiSTT class

def process_input(text, chatglm):
    """处理输入文本并获取模型响应"""
    if not text.strip():
        return

    # 添加用户输入到历史记录
    st.session_state.chathistory.append({
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
        for chunk in chatglm.stream([HumanMessage(content=text)]):
            response_text += str(chunk)
            response_placeholder.markdown(response_text)

        # 添加助手响应到历史记录
        st.session_state.chathistory.append({
            "role": "assistant",
            "content": response_text
        })

def main():
    # Initialize the chatbot model
    chatglm = ChatGLM4()

    # Initialize the XunfeiSTT class
    xunfei_stt = XunfeiSTT()

    # Streamlit UI elements
    st.title("ChatGLM4 with Xunfei Voice Recognition")
    input_text = st.text_input("Type your message or use voice input", key="input")
    submit_button = st.button("Send")

    # Check if the 'Send' button is clicked or voice input is detected
    if submit_button or xunfei_stt.textqueue is not None:
        process_input(input_text, chatglm)

    # Initialize session state for chat history if not already present
    if 'chathistory' not in st.session_state:
        st.session_state.chathistory = []

if __name__ == "__main__":
    main()
