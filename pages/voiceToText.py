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

# Xunfei API credentials
APPID = "your_appid"
APISecret = "your_api_secret"
APIKey = "your_api_key"

class XunfeiSTT:
    def __init__(self):
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.text_queue = queue.Queue()
        self.is_running = False
        
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
        data = json.loads(message)
        if data["code"] != 0:
            print(f"Error: {data['message']}")
            return
        
        result = data["data"]["result"]
        if result.get("ws"):
            text = "".join([w["cw"][0]["w"] for w in result["ws"]])
            self.text_queue.put(text)

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")
        self.is_running = False

    def on_open(self, ws):
        def send_data():
            params = {
                "common": {"app_id": APPID},
                "business": {
                    "language": "zh_cn",
                    "domain": "iat",
                    "accent": "mandarin"
                },
                "data": {
                    "status": 0,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw"
                }
            }
            ws.send(json.dumps(params))

        threading.Thread(target=send_data).start()

    def start_listening(self):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            self.create_url(),
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.is_running = True
        ws.run_forever()

def query_model(text):
    # Replace this with your actual model API call
    # This is just a mock response
    return f"Answer to: {text}"

def main():
    st.title("Real-time Speech Recognition and Q&A")
    
    stt = XunfeiSTT()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Start/Stop button for speech recognition
    if st.button("Toggle Speech Recognition"):
        if not stt.is_running:
            threading.Thread(target=stt.start_listening).start()
            st.success("Speech recognition started")
        else:
            stt.is_running = False
            st.warning("Speech recognition stopped")

    # Text input for manual questions
    text_input = st.text_input("Or type your question here:")
    if text_input:
        st.session_state.messages.append({"role": "user", "content": text_input})
        answer = query_model(text_input)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Check for new speech recognition results
    if stt.is_running:
        try:
            while True:
                text = stt.text_queue.get_nowait()
                st.session_state.messages.append({"role": "user", "content": text})
                answer = query_model(text)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.experimental_rerun()
        except queue.Empty:
            pass

if __name__ == "__main__":
    main()