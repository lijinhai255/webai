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
import ssl

# Xunfei API credentials
APPID = "414dfd51"        # 替换为您的讯飞应用ID
APISecret = "OTJmYjQ4YmMzMTVkY2E5MTE5Y2RlY2Mx"  # 替换为您的讯飞API密钥
APIKey = "bb6f62671318f6009c8c7ba61e088495"       # 替换为您的讯飞API Key
CERT_PATH = "/path/to/your/certificate.pem"  # 替换为证书文件路径

class XunfeiSTT:
    def __init__(self):
        self.last_error = None          # 新增属性：记录最后一次错误
        self.text_queue = queue.Queue()
        self.recognition = websocket.WebSocketApp(
            "wss://iat-api.xfyun.cn/v1/voice_recognition",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.is_running = False
        self.cert_chain = None  # 证书链
    
    def _load_certificate(self):
        """加载证书文件（包含私钥）"""
        try:
            with open(CERT_PATH, "r") as f:
                self.cert_chain = f.read()
        except Exception as e:
            self.last_error = f"证书加载失败: {str(e)}"
    
    def _generate_signature(self, canonical):
        """生成带证书链的HMAC-SHA256r1签名"""
        if not self.cert_chain:
            raise ValueError("证书未加载或格式错误")
        
        cert_data = self.cert_chain.encode('utf-8')
        try:
            cert = ssl.PEMCertificate(cert_data)
        except Exception as e:
            self.last_error = f"证书解析失败: {str(e)}"
            raise
        
        if not hasattr(cert, 'private_key'):
            self.last_error = "证书不包含私钥"
            raise ValueError("证书不包含私钥")
        
        try:
            signer = ssl.Signer(
                cert.private_key,
                signature_algorithm=hashlib.sha256()
            )
        except Exception as e:
            self.last_error = f"签名生成失败: {str(e)}"
            raise
        
        try:
            signer.update(canonical.encode('utf-8'))
            signature = signer.sign()
        except Exception as e:
            self.last_error = f"签名计算失败: {str(e)}"
            raise
        
        return base64.b64encode(signature).decode('utf-8')
    
    def on_open(self, ws):
        if self.last_error:
            return
        
        timestamp = datetime.datetime.now().isoformat('T') + 'Z'
        headers_dict = {
            "date": timestamp,
            "host": "iat-api.xfyun.cn",
            "x-appid": APPID,
            "content-type": "application/json"
        }
        sorted_headers = sorted(headers_dict.items(), key=lambda x: x[0])
        canonical = "\n".join([f"{k}:{v}"]) + "\n"
        
        try:
            self._load_certificate()
            signature = self._generate_signature(canonical)
        except Exception as e:
            self.last_error = f"请求签名失败: {str(e)}"
            return
        
        authorization = f"api_key={APIKey},algorithm=HMAC-SHA256r1,headers=date,host,x-appid,content-type,signature={signature}"
        
        try:
            ws.send(
                json.dumps({
                    "header": {
                        "appid": APPID,
                        "timestamp": timestamp,
                        "signature": signature
                    },
                    "body": {"engine_type": "online"}
                }),
                header=headers_dict
            )
        except Exception as e:
            self.last_error = f"WebSocket连接失败: {str(e)}"
    
    def on_message(self, ws, message):
        if self.last_error:
            return
        
        try:
            result = json.loads(message)
            if "result" in result and "sentence" in result["result"]:
                self.text_queue.put(result["result"]["sentence"])
            else:
                self.last_error = f"识别结果解析失败: {message}"
        except Exception as e:
            self.last_error = f"消息处理失败: {str(e)}"
    
    def on_error(self, ws, error):
        self.last_error = f"WebSocket错误: {str(error)}"
        self.is_running = False
    
    def on_close(self, ws):
        self.last_error = "语音识别连接已关闭"
        self.is_running = False
    
    def start_listening(self):
        if self.is_running:
            return
        
        try:
            self.recognition.run_forever()
        except Exception as e:
            self.last_error = f"语音识别启动失败: {str(e)}"
    
    def stop_listening(self):
        if self.recognition.sock:
            self.recognition.close()

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
        voice_button = st.button("🎤 开始/停止语音识别", key="voice_control", on_click=lambda: stt.toggle_listening())
    
    # 显示语音识别状态
    with col2:
        st.markdown(
            "<div style='font-weight:bold; margin-bottom: 5px;'>👂 语音识别状态:</div>",
            unsafe_allow_html=True
        )
        # 安全访问 last_error 属性
        error_msg = stt.last_error if hasattr(stt, 'last_error') and stt.last_error else "无错误"
        st.text(error_msg)
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