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
        let speechInput = null;

        // 初始化语音识别
        function initRecognition() {
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'zh-CN';

                recognition.onstart = () => {
                    console.log('录音开始');
                    updateUI(true);
                };

                recognition.onerror = (event) => {
                    console.error('录音错误:', event.error);
                    updateUI(false, `错误: ${event.error}`);
                };

                recognition.onresult = (event) => {
                    processTranscript(event.results);
                };

                recognition.onend = () => {
                    console.log('录音结束');
                    updateUI(false);
                };
            } else {
                alert('浏览器不支持语音识别功能，请使用Chrome浏览器');
            }
        }

        // 更新界面状态
        function updateUI(isRecording, errorMessage = '') {
            document.getElementById('status').textContent = errorMessage || 
                (isRecording ? '正在录音...' : '录音已停止');
            
            document.getElementById('startButton').textContent = 
                isRecording ? '🛑 停止录音' : '🎤 开始录音';
            document.getElementById('startButton').style.backgroundColor = 
                isRecording ? '#4CAF50' : '#ff4b4b';
        }

        // 处理识别结果
        function processTranscript(results) {
            let final_transcript = '';
            results.forEach(result => {
                if (result.isFinal) {
                    final_transcript += result[0].transcript;
                }
            });
            
            // 显示实时结果
            document.getElementById('result').innerHTML = `
                <div>临时结果: ${interimResult}</div>
                <div>最终结果: ${final_transcript}</div>
            `;
            
            // 发送最终结果到后端
            if (final_transcript.trim()) {
                window.parent.postMessage({
                    type: 'speech_recognition',
                    text: final_transcript
                }, '*');
            }
        }

        function startSpeechRecognition() {
            if (!recognition) initRecognition();
            
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        // 初始化隐藏输入框用于接收语音结果
        window.onload = () => {
            speechInput = document.createElement('input');
            speechInput.style.display = 'none';
            speechInput.id = 'voice-input';
            document.body.appendChild(speechInput);
            
            // 监听消息事件
            window.addEventListener('message', (e) => {
                if (e.data.type === 'speech_recognition') {
                    speechInput.value = e.data.text;
                    st.session_state.speech_text = e.data.text;
                    st.experimental_rerun();
                }
            });
        }
        </script>
        """,
        height=250,
    )

    # 绑定隐藏输入框到文本输入处理
    if st.session_state.get('speech_text'):
        process_input(st.session_state['speech_text'])
        st.session_state['speech_text'] = None

    # 文本输入框（包含隐藏的语音输入）
    user_input = st.chat_input("输入文字或使用语音...", 
                             key='user_input',
                             help="按回车发送或点击麦克风按钮说话")

    # 处理输入文本
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

if __name__ == "__main__":
    main()