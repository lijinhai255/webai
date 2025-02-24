#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import io
from LLM.chat_glm4 import ChatGLM4
from src.knowledge_base import LocalKnowledgeBase
import logging 
import numpy as np
print(np.__version__)  # Should show 1.x version

if __name__ == "__main__":
    # 初始化知识库
    kb = LocalKnowledgeBase("config/config.yaml")
    
    # 执行查询
    results = kb.query("Vue组件封装与开发",  score_threshold=0.3)
    
    # 打印结果
    for doc, score in results:
        print(f"相关度: {score:.2f}")
        print(f"内容: {doc.page_content[:200]}...")
        print(f"来源: {doc.metadata['source']}")
        print("-" * 80)