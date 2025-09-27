#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量数据库知识对话工具
将向量数据库中的知识作为LLM的上下文，实现基于知识库的对话
"""
import os
import sys
import json
import logging
from typing import List, Dict
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需的模块
from src.llm_analysis.llm_analyzer import LLMAnalyzer
from src.storage.vector_db import FAISSPersistence

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorKnowledgeChat:
    """基于向量数据库的知识对话类"""
    
    # 修改第40行左右的代码
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434/api/generate", 
                 model: str = "deepseek-r1:7b",
                 index_path: str = 'vector_index.faiss',
                 metadata_path: str = 'vector_metadata.json',
                 embedding_model: str = 'all-MiniLM-L6-v2',
                 top_k_docs: int = 3,
                 timeout: int = 120,
                 max_retries: int = 3,
                 retry_delay: int = 5):
        """初始化向量知识对话工具
        
        Args:
            ollama_url: Ollama API的URL地址
            model: 使用的LLM模型名称
            index_path: FAISS索引文件路径
            metadata_path: 元数据文件路径
            embedding_model: 用于向量生成的模型
            top_k_docs: 搜索时返回的最大相关文档数
            timeout: API请求超时时间（秒）
            max_retries: API请求最大重试次数
            retry_delay: API请求重试间隔（秒）
        """
        # 初始化LLM分析器
        self.analyzer = LLMAnalyzer(use_real_llm=True, ollama_url=ollama_url, model=model)
        
        # 初始化向量数据库
        self.vector_db = FAISSPersistence(
            index_path=index_path,
            metadata_path=metadata_path,
            embedding_model=embedding_model
        )
        
        self.top_k_docs = top_k_docs
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conversation_history = []
        
        # 打印初始化信息
        stats = self.vector_db.get_statistics()
        logger.info(f"向量数据库初始化完成，包含 {stats.get('total_documents', 0)} 个文档")
        logger.info(f"使用模型: {model}")
    
    def build_prompt(self, query: str, relevant_docs: List[Dict]) -> str:
        """构建包含上下文和查询的完整提示词
        
        Args:
            query: 用户的查询
            relevant_docs: 检索到的相关文档
            
        Returns:
            完整的提示词字符串
        """
        # 构建上下文信息
        context = "基于以下提供的知识，回答用户的问题。如果你无法从提供的知识中找到答案，请如实告知。\n\n"
        context += "相关知识：\n"
        
        for i, doc in enumerate(relevant_docs):
            title = doc.get('title', f'文档{i+1}')
            content = doc.get('content', '')
            publish_time = doc.get('publish_time', '未知')
            
            # 限制每篇文档的内容长度
            max_content_len = 500
            if len(content) > max_content_len:
                content = content[:max_content_len] + "..."
            
            context += f"【文档{i+1}】标题：{title}\n发布时间：{publish_time}\n内容：{content}\n\n"
        
        # 添加对话历史（最近5轮）
        if self.conversation_history:
            recent_history = self.conversation_history[-5:]
            context += "历史对话：\n"
            for i, (q, a) in enumerate(recent_history):
                context += f"用户：{q}\n助手：{a}\n"
            context += "\n"
        
        # 添加用户当前查询
        context += f"用户问题：{query}\n"
        context += "请基于上述知识，用中文回答用户问题。"
        
        return context
    
    def search_relevant_docs(self, query: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """搜索与查询相关的文档
        
        Args:
            query: 用户的查询
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            
        Returns:
            相关文档列表
        """
        # 如果指定了日期范围，使用日期过滤
        if start_date and end_date:
            # 先按日期范围获取文档
            date_filtered_docs = self.vector_db.get_by_date_range(start_date, end_date, top_k=self.top_k_docs * 5)
            
            # 如果没有符合日期范围的文档，回退到普通搜索
            if not date_filtered_docs:
                logger.warning(f"没有找到 {start_date} 至 {end_date} 期间的文档，将使用全部文档进行搜索")
                return self.vector_db.search(query, top_k=self.top_k_docs)
            
            # 对于日期过滤后的文档，再次进行相似度排序
            # 这里简化处理，直接使用FAISS的搜索功能
            return self.vector_db.search(query, top_k=self.top_k_docs, start_date=start_date, end_date=end_date)
        else:
            # 直接搜索所有文档
            return self.vector_db.search(query, top_k=self.top_k_docs)
    
    def is_statistics_query(self, query: str) -> bool:
        """检测是否为统计类查询
        
        Args:
            query: 用户的查询
            
        Returns:
            是否为统计类查询
        """
        # 定义统计查询的关键词
        stats_keywords = [
            "多少个文档", "文档总数", "总共有多少", "有多少篇", 
            "文档数量", "数据库大小", "统计信息"
        ]
        
        # 检查查询中是否包含统计关键词
        for keyword in stats_keywords:
            if keyword in query:
                return True
        
        return False
    
    def generate_statistics_response(self) -> str:
        """生成统计信息的回答
        
        Returns:
            包含统计信息的回答文本
        """
        stats = self.vector_db.get_statistics()
        total_docs = stats.get('total_documents', 0)
        
        response = f"向量数据库中目前共有 {total_docs} 篇文档。\n\n"
        
        # 添加其他统计信息
        channels = stats.get('channels', {})
        if channels and len(channels) > 1:
            response += "按频道分布情况：\n"
            for channel, count in channels.items():
                response += f"- {channel}: {count} 篇文档\n"
        
        # 提供额外提示
        response += "\n提示：您可以输入 'stats' 命令查看更详细的统计信息。"
        
        return response
    
    def generate_response(self, query: str, start_date: str = None, end_date: str = None) -> str:
        """生成基于向量数据库知识的回答
        
        Args:
            query: 用户的查询
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            
        Returns:
            LLM生成的回答
        """
        # 检查是否为统计类查询
        if self.is_statistics_query(query):
            logger.info("检测到统计类查询，直接返回统计信息")
            answer = self.generate_statistics_response()
            self.conversation_history.append((query, answer))
            return answer
        
        # 搜索相关文档
        relevant_docs = self.search_relevant_docs(query, start_date, end_date)
        
        if not relevant_docs:
            logger.warning("未找到相关文档，将直接使用LLM回答")
            # 构建一个简单的提示词
            prompt = f"用户问题：{query}\n请用中文回答。"
        else:
            # 构建包含上下文的提示词
            prompt = self.build_prompt(query, relevant_docs)
            
            # 记录使用的相关文档
            logger.info(f"找到 {len(relevant_docs)} 篇相关文档")
            for i, doc in enumerate(relevant_docs):
                logger.info(f"  文档{i+1}: {doc.get('title', '无标题')} (相似度: {doc.get('distance', 0):.4f})")
        
        # 调用LLM生成回答
        try:
            # 这里我们复用LLMAnalyzer的_call_llm_api方法，但需要调整提示词和解析逻辑
            # 由于我们只需要生成回答，不需要提取摘要、关键词等，可以直接调用API
            import requests
            response = requests.post(
                self.analyzer.ollama_url,
                json={
                    "model": self.analyzer.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                },
                timeout=self.analyzer.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                # 保存对话历史
                self.conversation_history.append((query, answer))
                
                return answer
            else:
                logger.error(f"LLM API调用失败，状态码: {response.status_code}")
                return f"抱歉，我暂时无法回答这个问题。错误: {response.status_code}"
        except Exception as e:
            logger.error(f"生成回答时出错: {e}")
            return f"抱歉，我暂时无法回答这个问题。错误: {str(e)}"
    
    def start_chat(self):
        """启动交互式对话"""
        print("=" * 80)
        print("欢迎使用向量数据库知识对话工具！")
        print("说明：")
        print("  1. 输入您的问题进行对话")
        print("  2. 输入 'quit' 或 'exit' 退出对话")
        print("  3. 输入 'clear' 清空对话历史")
        print("  4. 输入 'stats' 查看向量数据库统计信息")
        print("  5. 可以使用 'date:2023-01-01,2023-12-31' 格式来限制日期范围")
        print("=" * 80)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n您的问题: ").strip()
                
                # 检查特殊命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("感谢使用，再见！")
                    break
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("对话历史已清空")
                    continue
                elif user_input.lower() == 'stats':
                    stats = self.vector_db.get_statistics()
                    print("\n向量数据库统计信息:")
                    print(f"  总文档数: {stats.get('total_documents', 0)}")
                    print(f"  索引大小: {stats.get('index_size', 0) / 1024:.2f} KB")
                    print(f"  元数据大小: {stats.get('metadata_size', 0) / 1024:.2f} KB")
                    print(f"  嵌入模型: {stats.get('embedding_model', 'unknown')}")
                    print("  按频道统计:")
                    for channel, count in stats.get('channels', {}).items():
                        print(f"    {channel}: {count} 篇")
                    continue
                
                # 检查是否包含日期范围
                start_date = None
                end_date = None
                if user_input.startswith('date:'):
                    try:
                        date_part = user_input[5:].strip()
                        if ',' in date_part:
                            start_date, end_date = date_part.split(',', 1)
                            # 获取实际的问题
                            query = input("请输入您的问题: ").strip()
                        else:
                            print("日期范围格式不正确，请使用 'date:开始日期,结束日期' 格式")
                            continue
                    except Exception:
                        print("日期范围解析失败，请使用 'date:开始日期,结束日期' 格式")
                        continue
                else:
                    query = user_input
                
                if not query:
                    continue
                
                # 生成回答
                print("正在思考...")
                answer = self.generate_response(query, start_date, end_date)
                
                # 显示回答
                print("\n助手回答:")
                print(answer)
                
            except KeyboardInterrupt:
                print("\n感谢使用，再见！")
                break
            except Exception as e:
                logger.error(f"对话过程中出错: {e}")
                print(f"抱歉，对话过程中出现错误: {str(e)}")

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description='向量数据库知识对话工具')
    parser.add_argument('--ollama-url', type=str, default='http://localhost:11434/api/generate', help='Ollama API的URL地址')
    parser.add_argument('--model', type=str, default='deepseek-r1:7b', help='使用的LLM模型名称')
    parser.add_argument('--index-path', type=str, default='vector_index.faiss', help='FAISS索引文件路径')
    parser.add_argument('--metadata-path', type=str, default='vector_metadata.json', help='元数据文件路径')
    # 修改第331行左右的代码
    parser.add_argument('--top-k', type=int, default=33, help='搜索时返回的最大相关文档数')
    
    args = parser.parse_args()
    
    # 创建对话实例并启动对话
    chat = VectorKnowledgeChat(
        ollama_url=args.ollama_url,
        model=args.model,
        index_path=args.index_path,
        metadata_path=args.metadata_path,
        top_k_docs=args.top_k
    )
    chat.start_chat()