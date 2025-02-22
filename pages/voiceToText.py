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
        self.recognition = None          # 改为显式声明
        self.is_running = False
        self.cert_chain = None          # 证书链
        
        self._initialize_certificate()  # 新增证书初始化
    
    def _initialize_certificate(self):
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
        
        try:
            cert = ssl.PEMCertificate(self.cert_chain.encode())
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
    
    def connect(self):
        """建立WebSocket连接（重命名run_forever为connect）"""
        if self.is_running:
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
            self._initialize_certificate()
            signature = self._generate_signature(canonical)
        except Exception as e:
            self.last_error = f"请求签名失败: {str(e)}"
            return
        
        authorization = f"api_key={APIKey},algorithm=HMAC-SHA256r1,headers=date,host,x-appid,content-type,signature={signature}"
        
        try:
            self.recognition = websocket.WebSocketApp(
                "wss://iat-api.xfyun.cn/v1/voice_recognition",
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
        except Exception as e:
            self.last_error = f"WebSocket初始化失败: {str(e)}"
            return
        
        self.is_running = True
    
    def on_open(self, ws):
        """WebSocket连接建立回调"""
        if self.last_error:
            return
        
        try:
            self.send_authentication_header(ws)
        except Exception as e:
            self.last_error = f"身份验证失败: {str(e)}"
    
    def send_authentication_header(self, ws):
        """发送身份验证头"""
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
            signature = self._generate_signature(canonical)
        except Exception as e:
            raise RuntimeError(f"签名生成失败: {str(e)}")
        
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
            raise RuntimeError(f"发送认证请求失败: {str(e)}")
    
    def on_message(self, ws, message):
        """处理接收消息"""
        if self.last_error:
            return
        
        try:
            result = json.loads(message)
            if "result" in result and "sentence" in result["result"]:
                self.text_queue.put(result["result"]["sentence"])
            else:
                self.last_error = f"无效响应格式: {message}"
        except json.JSONDecodeError as e:
            self.last_error = f"JSON解析失败: {str(e)}"
        except Exception as e:
            self.last_error = f"消息处理失败: {str(e)}"
    
    def on_error(self, ws, error):
        """处理连接错误"""
        self.last_error = f"WebSocket错误: {str(error)}"
        self.is_running = False
    
    def on_close(self, ws):
        """处理连接关闭"""
        self.last_error = "语音识别连接已关闭"
        self.is_running = False
    
    def start_listening(self):
        """启动监听（对外接口）"""
        if not self.is_running:
            self.connect()
    
    def stop_listening(self):
        """停止监听（对外接口）"""
        if self.recognition and self.recognition.sock:
            self.recognition.close()
            self.is_running = False

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化服务
    stt = XunfeiSTT()
    chat_glm = ChatGLM4()
    
    # 使用lru_cache缓存会话状态
    @st.cache(maxsize=None)
    def load_config():
        return {
            "chat_history": [],
            "speech_errors": []
        }
    
    st.session_state.chat_history = load_config()["chat_history"]
    st.session_state.speech_errors = load_config()["speech_errors"]
    
    # 添加语音识别控制按钮
    voice_button = st.button("🎤 开始/停止语音识别", key="voice_control", 
                             on_click=lambda: stt.toggle_listening())
    
    # 显示状态信息
    with st.sidebar:
        st.markdown("### 📊 状态监控")
        st.text(f"错误日志: {stt.last_error or '无'}")
        st.text(f"识别队列: {stt.text_queue.qsize()}")
    
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
    
    # 启动后台线程
    if not hasattr(process_speech, 'running'):
        process_thread = threading.Thread(target=process_speech)
        process_thread.daemon = True
        process_thread.start()
        process_speech.running = True

    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

if __name__ == "__main__":
    main()