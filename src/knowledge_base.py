from pathlib import Path
from typing import Dict, Any, List
from langchain_huggingface import HuggingFaceEmbeddings  # 使用新版SDK
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import yaml
import logging
import os

logger = logging.getLogger(__name__)

class LocalKnowledgeBase:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._validate_config()
        self.embeddings = self._init_embeddings()
        self.vector_store = self._init_vector_store()

    @property
    def document_count(self) -> int:
        """获取文档总数（优化计数方式）"""
        return self.vector_store.index.ntotal if self.vector_store.index else 0

    @property
    def documents(self) -> List[Document]:
        """获取文档列表（优化获取方式）"""
        return self.vector_store.docstore._dict.values() if self.vector_store.docstore else []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """增强型配置加载"""
        config_path = Path(config_path).resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"配置文件读取失败: {str(e)}")
            raise

    def _validate_config(self):
        """增强型配置验证"""
        required_structure = {
            'knowledge_base': {
                'path': str,
                'glob_pattern': str,
                'chunk_size': int,
                'overlap': int
            },
            'vector_db': {
                'model_name': str,
                'persistence_path': str
            }
        }

        # 段落检查
        for section in required_structure:
            if section not in self.config:
                raise ValueError(f"缺少必要配置段落: [{section}]")

        # 字段检查
        for section, fields in required_structure.items():
            for field, field_type in fields.items():
                if field not in self.config[section]:
                    raise ValueError(f"段落 [{section}] 缺少字段: {field}")
                if not isinstance(self.config[section][field], field_type):
                    actual_type = type(self.config[section][field]).__name__
                    raise TypeError(
                        f"配置类型错误: [{section}.{field}] 应为 {field_type.__name__}, 实际是 {actual_type}"
                    )

    def _init_embeddings(self) -> HuggingFaceEmbeddings:
        """增强型模型初始化"""
        model_path = Path(self.config['vector_db']['model_name']).resolve()
        
        # 路径验证
        if not model_path.exists():
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        if not model_path.is_dir():
            raise NotADirectoryError(f"模型路径不是目录: {model_path}")
        if not any(model_path.glob("*.bin")) and not any(model_path.glob("pytorch_model.bin")):
            raise ValueError(f"模型目录缺少模型文件: {model_path}")

        try:
            return HuggingFaceEmbeddings(
                model_name=str(model_path),
                model_kwargs={"device": "cpu"},  # 显式指定设备
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 32
                }
            )
        except Exception as e:
            logger.error(f"模型初始化失败: {str(e)}")
            raise

    def _init_vector_store(self) -> FAISS:
        persistence_path = Path(self.config['vector_db']['persistence_path'])
        
        # 增强路径检查
        if not persistence_path.exists():
            logger.info(f"创建存储目录: {persistence_path}")
            persistence_path.mkdir(parents=True, exist_ok=True)

        # 检查文件完整性
        required_files = ["index.faiss", "index.pkl"]
        if all((persistence_path / f).exists() for f in required_files):
            try:
                return FAISS.load_local(
                    folder_path=str(persistence_path),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                logger.error(f"加载失败: {str(e)}")
                logger.info("尝试重建向量库...")
                return self._create_new_vector_store()
        else:
            logger.info("检测到不完整索引，将重建")
            return self._create_new_vector_store()
# knowledge_base.py
    def _create_new_vector_store(self) -> FAISS:
        """修复后的向量库创建方法"""
        try:
            # 文档加载
            loader = DirectoryLoader(
                self.config['knowledge_base']['path'],
                glob=self.config['knowledge_base']['glob_pattern'],
                loader_kwargs={'encoding': 'utf-8'}
            )
            documents = loader.load()
            
            # 文本分块
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config['knowledge_base']['chunk_size'],
                chunk_overlap=self.config['knowledge_base']['overlap']
            )
            splits = text_splitter.split_documents(documents)
            
            # 创建向量库（关键修复点）
            vector_store = FAISS.from_documents(
                documents=splits, 
                embedding=self.embeddings
            )
            
            # 确保保存目录存在
            persistence_path = Path(self.config['vector_db']['persistence_path'])
            persistence_path.mkdir(parents=True, exist_ok=True)
            
            # 保存向量库
            vector_store.save_local(
                folder_path=str(persistence_path),
                index_name="index"
            )
            return vector_store  # 确保返回变量
            
        except Exception as e:
            logger.error(f"创建向量库失败: {str(e)}")
            raise
    def query(
        self, 
        question: str, 
        top_k: int = 3,
        score_threshold: float = 0.6
    ) -> List[Document]:
        """增强型查询方法"""
        return self.vector_store.similarity_search_with_relevance_scores(
            query=question,
            k=top_k,
            score_threshold=score_threshold
        )

    def __repr__(self) -> str:
        return f"<LocalKnowledgeBase: {self.document_count} documents>"