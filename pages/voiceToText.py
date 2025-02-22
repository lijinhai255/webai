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
APPID = "your_appid"        # 替换为您的讯飞应用ID
APISecret = "your_api_secret"  # 替换为您的讯飞API密钥
APIKey = "your_api_key"       # 替换为您的讯飞API Key

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        self.recognition = None
        self.last_error = ""

    def start_listening(self):
        """启动语音识别"""
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
        """停止语音识别"""
        if self.recognition and self.recognition.readyState == 1:
            self.recognition.send(json.dumps({"type": "stop"}))
            self.is_running = False
            st.warning("⚠️ 语音识别已停止")

    def on_open(self, ws):
        """WebSocket连接建立"""
        st.success("✅ WebSocket连接成功")
        self.send_request({
            "common": {
                "appid": APPID,
                "version": "20200614",
                "scene": "stt"
            },
            "business": {
                "aue": "raw",
                "auf": "audio/L16;rate=16000"
            }
        })

    def send_request(self, data):
        """发送请求到讯飞服务器"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        sign = self._generate_signature(data, timestamp)
        headers = {
            "Authorization": f"api_key={APIKey},algorithm=hmac-sha256,headers=date,{sign},signature={self._calculate_signature(data, timestamp)}",
            "Date": timestamp,
            "Content-Type": "application/json"
        }
        self.recognition.send(json.dumps({
            "header": {
                "appid": APPID,
                "timestamp": timestamp,
                "sign": sign
            },
            "body": data
        }))
    
    def _generate_signature(self, data, timestamp):
        """生成签名"""
        sign_str = f"{timestamp}\n{json.dumps(data)}\n"
        return hmac.new(
            bytes(APISecret, 'utf-8'),
            bytes(sign_str, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _calculate_signature(self, data, timestamp):
        """完整签名计算"""
        raw = f"{timestamp}\n{json.dumps(data)}\n"
        return base64.b64encode(hmac.new(
            bytes(APIKey, 'utf-8'),
            bytes(raw, 'utf-8'),
            hashlib.sha256
        ).digest()).decode('utf-8')

    def on_message(self, ws, message):
        """处理服务器响应"""
        try:
            res = json.loads(message)
            if res["header"]["status"] == 0:
                if res["body"]["result"]["has_voice"]:
                    self.text_queue.put(res["body"]["result"]["text"])
                else:
                    st.warning("⚠️ 未检测到语音")
            else:
                self.last_error = f"识别错误: {res['header']['desc']}"
                st.error(self.last_error)
        except Exception as e:
            self.last_error = f"消息解析失败: {str(e)}"
            st.error(self.last_error)

    def on_error(self, ws, error):
        """处理连接错误"""
        self.last_error = f"WebSocket错误: {str(error)}"
        st.error(self.last_error)
        self.stop_listening()

    def on_close(self, ws, close_status_code, close_reason):
        """处理连接关闭"""
        st.warning("⚠️ 语音识别连接已关闭")
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
        voice_button = st.button("🎤 开始/停止语音识别", key="voice_control")
        if voice_button:
            if stt.is_running:
                stt.stop_listening()
            else:
                stt.start_listening()
    
    # 显示语音识别状态
    with col2:
        st.text("语音识别状态:", style="font-weight:bold")
        st.text(f"最后错误: {stt.last_error}" if stt.last_error else "无错误")
        st.text(f"识别结果队列: {stt.text_queue.qsize()}")
    
    # 文本输入框
    user_input = st.chat_input("输入文字或使用语音...", key='user_input')
    
    # 处理输入文本
    def process_input(text):
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

    # 处理语音识别结果
    def process_speech():
        while True:
            try:
                text = stt.text_queue.get_nowait()
                if not text.strip():
                    continue
                process_input(text)
                st.experimental_rerun()
            except queue.Empty:
                break
    
    # 主循环处理
    if voice_button:
        if stt.is_running:
            st.warning("⚠️ 语音识别正在进行...")
        else:
            st.success("✅ 语音识别已就绪")
    
    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
    
    # 启动语音处理线程
    if stt.is_running and not hasattr(process_speech, "thread"):
        process_thread = threading.Thread(target=process_speech)
        process_thread.daemon = True
        process_thread.start()
        process_speech.thread = process_thread

if __name__ == "__main__":
    main()