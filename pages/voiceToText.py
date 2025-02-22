# -*- coding: utf-8 -*-
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
from langchain.schema import HumanMessage
from LLM.chat_glm4 import ChatGLM4

# Xunfei API credentials
APPID = "f815c988"        # 替换为您的讯飞应用ID
APISecret = "ODMwNTc2NDNiOGZiZGZjMTkzNzdhNTc3"  # 替换为您的讯飞API密钥
APIKey = "657bfe10ef10741f60de4dc728c53353"       # 替换为您的讯飞API Key

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        self.recognition = None
        self.last_error = ""

    def start_listening(self):
        if self.is_running:
            return
        
        try:
            self.recognition = websocket.create_connection(
                self.ws_url,
                onopen=self.on_open,
                onmessage=self.on_message,
                onerror=self.on_error,
                onclose=self.on_close
            )
            self.is_running = True
            st.success("✅ 语音识别已启动")
        except Exception as e:
            self.last_error = f"连接失败: {str(e)}"
            st.error(self.last_error)

    def stop_listening(self):
        if self.recognition and self.recognition.readyState == 1:
            self.recognition.send(json.dumps({"type": "stop"}))
            self.is_running = False
            st.warning("⚠️ 语音识别已停止")

    def on_open(self, ws):
        st.success("✅ WebSocket连接成功")
        self.send_request({
            "common": {
                "appid": APPID,
                "version": "20231215",
                "scene": "stt"
            },
            "business": {
                "aue": "raw",
                "auf": "audio/L16;rate=16000"
            }
        })

    def send_request(self, data):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%3N")  # 毫秒级时间戳
        headers_dict = {
            "date": timestamp,
            "host": "iat-api.xfyun.cn",
            "x-appid": APPID
        }
        sorted_headers = sorted(headers_dict.items(), key=lambda x: x[0])
        canonical = "\n".join([f"{k}:{v}"]) + "\n"
        sign = hmac.new(
            bytes(APIKey, 'utf-8'),
            bytes(canonical, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        authorization = f"api_key={APIKey},algorithm=HMAC-SHA256,headers=date,host,x-appid,signature={sign}"
        
        request_body = {
            "header": {
                "appid": APPID,
                "timestamp": timestamp,
                "signature": sign
            },
            "body": data
        }
        
        self.recognition.send(
            json.dumps(request_body),
            headers={
                "Authorization": authorization,
                "Date": timestamp,
                "Host": "iat-api.xfyun.cn",
                "X-Appid": APPID,
                "Content-Type": "application/json"
            }
        )

    def on_message(self, ws, message):
        try:
            res = json.loads(message)
            if res.get("header", {}).get("status") == 0:
                if res.get("body", {}).get("result", {}).get("has_voice"):
                    self.text_queue.put(res["body"]["result"]["text"])
                else:
                    st.warning("⚠️ 未检测到语音")
            else:
                self.last_error = f"识别错误: {res.get('header', {}).get('desc', '未知错误')}"
                st.error(self.last_error)
        except Exception as e:
            self.last_error = f"消息解析失败: {str(e)}"
            st.error(self.last_error)

    def on_error(self, ws, error):
        self.last_error = f"WebSocket错误: {str(error)}"
        st.error(self.last_error)
        self.stop_listening()

    def on_close(self, ws, close_status_code, close_reason):
        st.warning(f"⚠️ 连接关闭: {close_reason}")
        self.is_running = False

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化服务
    stt = XunfeiSTT()
    chat_glm = ChatGLM4()
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.speech_errors = []  # 记录语音识别错误
    
    # 添加语音识别控制按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        voice_button = st.button("🎤 开始/停止语音识别", key="voice_control", disabled=not stt.is_running)
        if voice_button:
            if stt.is_running:
                stt.stop_listening()
            else:
                stt.start_listening()
    
    # 显示语音识别状态
    with col2:
        st.markdown(
            "<div style='font-weight:bold; margin-bottom: 5px;'>👂 语音识别状态:</div>",
            unsafe_allow_html=True
        )
        st.text(f"最后错误: {stt.last_error}" if stt.last_error else "无错误")
        st.text(f"识别结果队列: {stt.text_queue.qsize()}")
    
    # 文本输入框
    user_input = st.chat_input("输入文字或使用语音...", key='user_input')
    
    # 处理输入文本
    def process_input(text):
        st.session_state.chat_history.append({
            "role": "user",
            "content": text
        })
        
        with st.chat_message("user"):
            st.markdown(text)
        
        response_text = ""
        for chunk in chat_glm.stream([HumanMessage(content=text)]):
            response_text += chunk
            st.experimental_rerun()
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text
        })

    # 处理语音识别结果
    def process_speech():
        while True:
            try:
                text = stt.text_queue.get_nowait().strip()
                if not text:
                    continue
                process_input(text)
                st.experimental_rerun()
            except queue.Empty:
                break
    
    # 启动语音处理线程
    if stt.is_running and not hasattr(process_speech, "thread"):
        process_thread = threading.Thread(target=process_speech)
        process_thread.daemon = True
        process_thread.start()
        process_speech.thread = process_thread

    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

if __name__ == "__main__":
    main()