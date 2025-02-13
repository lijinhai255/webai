import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取 OpenAI API 密钥 & 自定义 API 地址
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")  # 默认值为 "EMPTY"

# 确保 API 地址和密钥已正确加载

# 初始化 LangChain ChatOpenAI 实例
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    temperature=0.7,
)
