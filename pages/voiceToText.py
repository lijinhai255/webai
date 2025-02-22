import streamlit as st
import streamlit.components.v1 as components
from langchain.schema import HumanMessage
from LLM.chat_glm4 import ChatGLM4

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化模型
    if 'chat_glm' not in st.session_state:
        st.session_state.chat_glm = ChatGLM4()
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 添加HTML组件用于语音识别
    components.html(
        """
        <div style="display: flex; align-items: center; gap: 10px;">
            <button id="startButton" onclick="startSpeechRecognition()" style="
                padding: 10px 20px;
                background-color: #ff4b4b;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            ">
                🎤 开始录音
            </button>
            <div id="status" style="color: #666;"></div>
        </div>
        <div id="result" style="margin-top: 10px; color: #333;"></div>

        <script>
        let recognition;
        let isRecording = false;

        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'zh-CN';  // 设置为中文

            recognition.onstart = function() {
                document.getElementById('status').textContent = '正在录音...';
                document.getElementById('startButton').textContent = '🛑 停止录音';
                document.getElementById('startButton').style.backgroundColor = '#4CAF50';
                isRecording = true;
            };

            recognition.onend = function() {
                document.getElementById('status').textContent = '录音已停止';
                document.getElementById('startButton').textContent = '🎤 开始录音';
                document.getElementById('startButton').style.backgroundColor = '#ff4b4b';
                isRecording = false;
            };

            recognition.onresult = function(event) {
                let final_transcript = '';
                let interim_transcript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        final_transcript += event.results[i][0].transcript;
                        // 将结果发送到Streamlit
                        window.parent.postMessage({
                            type: 'speech_recognition',
                            text: final_transcript
                        }, '*');
                    } else {
                        interim_transcript += event.results[i][0].transcript;
                    }
                }

                document.getElementById('result').innerHTML = 
                    (interim_transcript ? '临时结果: ' + interim_transcript : '') +
                    (final_transcript ? '<br>最终结果: ' + final_transcript : '');
            };

            recognition.onerror = function(event) {
                document.getElementById('status').textContent = '错误: ' + event.error;
            };
        }

        function startSpeechRecognition() {
            if (!recognition) {
                alert('您的浏览器不支持语音识别功能');
                return;
            }

            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
        </script>
        """,
        height=150,
    )

    # 文本输入框
    user_input = st.chat_input("输入文字或使用语音...")

    # 处理文本输入
    if user_input:
        process_input(user_input)

    # 显示聊天历史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

def process_input(text):
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
        for chunk in st.session_state.chat_glm.stream([HumanMessage(content=text)]):
            response_text += str(chunk)
            response_placeholder.markdown(response_text)
        
        # 添加助手响应到历史记录
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text
        })

# 添加JavaScript回调处理器
def handle_speech_input():
    components.html(
        """
        <script>
        window.addEventListener('message', function(e) {
            if (e.data.type === 'speech_recognition') {
                // 将识别结果发送到Streamlit后端
                window.parent.Streamlit.setComponentValue(e.data.text);
            }
        });
        </script>
        """,
        height=0,
    )

if __name__ == "__main__":
    main()
    handle_speech_input()