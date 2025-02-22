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
from LLM.chat_glm4 import ChatGLM4

APPID = "f815c988"
APISecret = "ODMwNTc2NDNiOGZiZGZjMTkzNzdhNTc3"
APIKey = "657bfe10ef10741f60de4dc728c53353"

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        
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
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        st.warning("语音识别连接已关闭")

    def on_open(self, ws):
        def send_data():
            # 发送开始参数
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
                
                # 开始录音并发送音频数据
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1600,  # 50ms的数据
                    stream_callback=self.audio_callback
                )
                self.stream.start_stream()
                
            except Exception as e:
                st.error(f"Error sending initial parameters: {str(e)}")

        threading.Thread(target=send_data).start()

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.ws and self.is_running:
            try:
                # 发送音频数据
                self.ws.send(in_data, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                st.error(f"Error sending audio data: {str(e)}")
        return (in_data, pyaudio.paContinue)

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
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.ws:
            self.ws.close()

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
            if not st.session_state.stt.is_running:
                threading.Thread(target=st.session_state.stt.start_listening).start()
                st.success("✅ 语音识别已启动")
            else:
                st.session_state.stt.stop_listening()
                st.warning("⚠️ 语音识别已停止")

    # 显示语音识别状态
    if st.session_state.stt.is_running:
        st.info("🎤 正在录音...")

    # 文本输入框
    user_input = st.chat_input("输入文字或使用语音...")

    # 处理文本输入
    if user_input:
        process_input(user_input, st.session_state.chat_glm)

    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # 处理语音识别结果
    if st.session_state.stt.is_running:
        try:
            while True:
                text = st.session_state.stt.text_queue.get_nowait()
                if text.strip():  # 只处理非空文本
                    process_input(text, st.session_state.chat_glm)
                    st.experimental_rerun()
        except queue.Empty:
            pass

def process_input(text, chat_glm):
    """处理输入文本并获取模型响应"""
    if not text.strip():
        return
        
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