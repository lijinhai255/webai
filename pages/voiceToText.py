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

# Xunfei API credentials - 请替换为您的实际凭证
APPID = "f815c988"
APISecret = "ODMwNTc2NDNiOGZiZGZjMTkzNzdhNTc3"
APIKey = "657bfe10ef10741f60de4dc728c53353"

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        self.ws = None
        
    def create_url(self):
        now = datetime.datetime.now()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        signature_origin = f"host: iat-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                               digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        params = {
            "authorization": authorization,
            "date": date,
            "host": "iat-api.xfyun.cn"
        }
        return f"{self.ws_url}?{urlencode(params)}"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data["code"] != 0:
                st.error(f"Error: {data['message']}")
                return
            
            result = data["data"]["result"]
            if result.get("ws"):
                text = "".join([w["cw"][0]["w"] for w in result["ws"]])
                self.text_queue.put(text)
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")

    def on_error(self, ws, error):
        st.error(f"WebSocket error: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        self.is_running = False
        st.warning("语音识别连接已关闭")

    def on_open(self, ws):
        def send_data():
            params = {
                "common": {"app_id": APPID},
                "business": {
                    "language": "zh_cn",
                    "domain": "iat",
                    "accent": "mandarin",
                    "vad_eos": 3000,
                    "dwa": "wpgs"
                },
                "data": {
                    "status": 0,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw"
                }
            }
            try:
                ws.send(json.dumps(params))
            except Exception as e:
                st.error(f"Error sending initial parameters: {str(e)}")

        threading.Thread(target=send_data).start()

    def start_listening(self):
        """启动语音识别"""
        try:
            websocket.enableTrace(True)
            self.ws = websocket.WebSocketApp(
                self.create_url(),
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            self.is_running = True
            self.ws.run_forever()
        except Exception as e:
            st.error(f"Error starting WebSocket: {str(e)}")
            self.is_running = False

    def stop_listening(self):
        """停止语音识别"""
        if self.ws:
            self.ws.close()
        self.is_running = False

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化语音识别和模型
    if 'stt' not in st.session_state:
        st.session_state.stt = XunfeiSTT()
    if 'chat_glm' not in st.session_state:
        st.session_state.chat_glm = ChatGLM4()
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 添加语音识别控制按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🎤 开始/停止语音识别"):