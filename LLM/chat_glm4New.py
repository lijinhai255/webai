from langchain.llms.base import LLM
from zhipuai import ZhipuAI
from langchain_core.messages.ai import AIMessage
from typing import List, Optional, Union, AsyncGenerator
from src.knowledge_base import LocalKnowledgeBase
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ChatGLM4(LLM):
    history: List[dict] = []
    client: Optional[ZhipuAI] = None
    _api_key: Optional[str] = None
    knowledge_base: Optional[LocalKnowledgeBase] = None

    def __init__(self, knowledge_base_config: str = "config/config.yaml"):
        super().__init__()
        self._initialize_client()
        self._initialize_knowledge_base(knowledge_base_config)
        
        # 添加初始化验证
        if self.knowledge_base:
            logger.info("知识库初始化成功，文档数量：%d", 
                      len(self.knowledge_base.documents))
        else:
            logger.warning("知识库未启用")


    def _initialize_client(self):
        """初始化智普AI客户端"""
        self._api_key = os.getenv("zhipuai_api_key")
        
        if not self._api_key or self._api_key == "EMPTY":
            logger.error("ZhipuAI API key not configured")
            raise ValueError("Missing ZhipuAI API key in environment variables")
            
        self.client = ZhipuAI(api_key=self._api_key)

    def _initialize_knowledge_base(self, config_path: str="config/config.yaml"):
        """初始化知识库"""
        try:
            self.knowledge_base = LocalKnowledgeBase(config_path)
            logger.info("Knowledge base initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            self.knowledge_base = None

    def _format_prompt_with_knowledge(self, prompt: str) -> str:
        """结合知识库内容格式化提示词"""
        if not self.knowledge_base or not self.knowledge_base.vector_store:
            return prompt

        try:
            # 显式禁用进度条
            docs = self.knowledge_base.vector_store.similarity_search(
                query=prompt,
                k=3,
                **{'show_progress_bar': False}  # 明确指定参数
            )
            context = "\n".join([
                f"[来源：{doc.metadata.get('source', '未知')}]\n{doc.page_content}"
                for doc in docs
            ])
            return f"""基于以下信息回答问题（禁用进度条）：
            
    {context}

    问题：{prompt}"""
        except Exception as e:
            logger.error(f"知识检索失败: {str(e)}")
            return prompt
    def _format_prompt(self, prompt: Union[str, List[dict]]) -> str:
        """统一处理输入格式"""
        if isinstance(prompt, list):
            return prompt[-1].content
        return str(prompt)

    def invoke(self, prompt, config={}, history=None) -> AIMessage:
        try:
            # 使用知识库增强提示词
            processed_prompt = self._format_prompt_with_knowledge(prompt)
            history = history or []
            
            trimmed_history = history[-5:] + [{"role": "user", "content": processed_prompt}]
            
            response = self.client.chat.completions.create(
                model="ChatGLM4",
                messages=trimmed_history,
                temperature=config.get("temperature", 0.7)
            )
            
            result = response.choices[0].message.content
            return AIMessage(content=result)
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return AIMessage(content="服务暂时不可用，请稍后再试")

    @property
    def _llm_type(self) -> str:
        return "ChatGLM4"

    def _call(self, prompt, config=None, history=None):
        return self.invoke(prompt, config or {}, history)

    def stream(self, prompt, config={}, history=None) -> AsyncGenerator[str, None]:
        try:
            processed_prompt = self._format_prompt_with_knowledge(prompt)
            history = history or []
            trimmed_history = history[-5:] + [{"role": "user", "content": processed_prompt}]

            response = self.client.chat.completions.create(
                model="glm-4",
                messages=trimmed_history,
                stream=True,
                temperature=config.get("temperature", 0.7)
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"流式请求失败: {str(e)}")
            yield "服务暂时不可用，请稍后再试"

    async def async_generate(
        self, user_text: str, history: List[dict] = []
    ) -> str:
        """增强版异步生成（带知识库验证、上下文追踪和流式进度）"""
        try:
            # 第一阶段：初始化上下文和日志
            logger.info(f"处理请求：{user_text}")
            raw_prompt = self._format_prompt(user_text)
            logger.debug(f"原始提示词: {raw_prompt}")

            # 第二阶段：知识库增强
            processed_prompt = self._format_prompt_with_knowledge(user_text)
            if processed_prompt == raw_prompt:
                logger.warning("知识库未增强，可能原因：1.知识库未加载 2.检索无结果")

            # 第三阶段：构建完整对话历史
            trimmed_history = history[-5:] + [{"role": "user", "content": processed_prompt}]
            
            # 第四阶段：调用流式API并处理响应
            logger.info("调用GLM-4 API（流式模式）...")
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=trimmed_history,
                stream=True,
                temperature=0.7  # 可根据需要调整
            )

            # 逐块处理流式响应并拼接结果
            result_parts = []
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content.strip()
                    result_parts.append(content)
                    # 实时输出进度（每50字符打印一次）
                    if len(''.join(result_parts)) % 100 == 0:
                        print(f"生成进度: {''.join(result_parts)[-100:]}")
                else:
                    # 防止空响应导致的死循环
                    if not content:
                        break
            
            final_result = ''.join(result_parts).strip() or "无有效内容"
            # 日志记录完整结果
            if len(final_result) > 50:
                logger.info(f"生成结果: {final_result[:50]}...")
            else:
                logger.info(f"生成结果: {final_result}")
            print("生成结果: ", final_result)
            return final_result

        except Exception as e:
            # 记录完整异常信息
            logger.error(f"生成流程异常: {str(e)}", exc_info=True)
            return "请求处理失败，请检查日志"