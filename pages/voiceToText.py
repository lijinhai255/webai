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
APPID = "414dfd51"        # 替换为您的讯飞应用ID
APISecret = "OTJmYjQ4YmMzMTVkY2E5MTE5Y2RlY2Mx"  # 替换为您的讯飞API密钥
APIKey = "bb6f62671318f6009c8c7ba61e088495"       # 替换为您的讯飞API Key

# XunfeiSTT 类的改进版本
class XunfeiSTT:
    def __init__(self):
        # ... (保持原有属性)
        self.cert_chain = None  # 新增证书链属性
    
    def _load_certificate(self):
        """加载证书文件（包含私钥）"""
        try:
            with open(CERT_PATH, "r") as f:
                self.cert_chain = f.read()
        except Exception as e:
            raise ValueError(f"证书加载失败: {str(e)}")
    
    def _generate_signature(self, canonical):
        """生成带证书链的HMAC-SHA256r1签名"""
        # 解析证书和私钥
        cert_data = self.cert_chain.encode('utf-8')
        cert = ssl.PEMCertificate(cert_data)
        
        if not hasattr(cert, 'private_key'):
            raise ValueError("证书文件不包含私钥")
        
        # 创建签名对象
        signer = crypto.Signer(
            cert.private_key,
            signature_algorithm=hashlib.sha256()
        )
        signer.update(canonical.encode('utf-8'))
        signature = signer.sign()
        return base64.b64encode(signature).decode('utf-8')
    
    def send_request(self, data):
        # 修正时间戳格式
        timestamp = datetime.datetime.now().isoformat('T') + 'Z'
        
        # 构建规范请求头
        headers_dict = {
            "date": timestamp,
            "host": "iat-api.xfyun.cn",
            "x-appid": APPID,
            "content-type": "application/json"
        }
        sorted_headers = sorted(headers_dict.items(), key=lambda x: x[0])
        canonical = "\n".join([f"{k}:{v}"]) + "\n"
        
        # 生成签名
        self._load_certificate()  # 确保证书已加载
        signature = self._generate_signature(canonical)
        authorization = f"api_key={APIKey},algorithm=HMAC-SHA256r1,headers=date,host,x-appid,content-type,signature={signature}"
        
        # 发送请求
        self.recognition.send(
            json.dumps({
                "header": {
                    "appid": APPID,
                    "timestamp": timestamp,
                    "signature": signature
                },
                "body": data
            }),
            headers={
                "Authorization": authorization,
                "Date": timestamp,
                "Host": "iat-api.xfyun.cn",
                "X-Appid": APPID,
                "Content-Type": "application/json"
            }
        )
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