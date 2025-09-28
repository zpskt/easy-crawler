#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量数据库知识对话API服务
将向量数据库知识对话工具封装为REST API
"""
import argparse
import os
import sys

from flask import Flask, request, jsonify

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需的模块
from src.llm_analysis.llm_analyzer import LLMAnalyzer
from src.storage.vector_db import FAISSPersistence

# 初始化Flask应用
app = Flask(__name__)

# 全局变量存储对话实例和历史
chat_instances = {}

class VectorKnowledgeChatAPI:
    """向量知识对话API封装类"""
    def __init__(self, 
                 ollama_url="http://localhost:11434/api/generate", 
                 model="deepseek-r1:7b",
                 index_path='vector_index.faiss',
                 metadata_path='vector_metadata.json',
                 embedding_model='all-MiniLM-L6-v2',
                 top_k_docs=3,
                 timeout=120,
                 max_retries=3,
                 retry_delay=5):
        """初始化向量知识对话API"""
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
    
    def search_relevant_docs(self, query, start_date=None, end_date=None):
        """搜索相关文档"""
        if start_date and end_date:
            date_filtered_docs = self.vector_db.get_by_date_range(start_date, end_date, top_k=self.top_k_docs * 5)
            if not date_filtered_docs:
                return self.vector_db.search(query, top_k=self.top_k_docs)
            return self.vector_db.search(query, top_k=self.top_k_docs, start_date=start_date, end_date=end_date)
        else:
            return self.vector_db.search(query, top_k=self.top_k_docs)
    
    def is_statistics_query(self, query):
        """检测是否为统计类查询"""
        stats_keywords = [
            "多少个文档", "文档总数", "总共有多少", "有多少篇", 
            "文档数量", "数据库大小", "统计信息"
        ]
        
        for keyword in stats_keywords:
            if keyword in query:
                return True
        
        return False
    
    def generate_statistics_response(self):
        """生成统计信息回答"""
        stats = self.vector_db.get_statistics()
        total_docs = stats.get('total_documents', 0)
        
        response = f"向量数据库中目前共有 {total_docs} 篇文档。\n\n"
        
        channels = stats.get('channels', {})
        if channels and len(channels) > 1:
            response += "按频道分布情况：\n"
            for channel, count in channels.items():
                response += f"- {channel}: {count} 篇文档\n"
        
        return response
    
    def build_prompt(self, query, relevant_docs):
        """构建提示词"""
        context = "基于以下提供的知识，回答用户的问题。如果你无法从提供的知识中找到答案，请如实告知。\n\n"
        context += "相关知识：\n"
        
        for i, doc in enumerate(relevant_docs):
            title = doc.get('title', f'文档{i+1}')
            content = doc.get('content', '')
            publish_time = doc.get('publish_time', '未知')
            
            max_content_len = 500
            if len(content) > max_content_len:
                content = content[:max_content_len] + "..."
            
            url = doc.get('url', '')
            context += f"【文档{i+1}】标题：{title}\n发布时间：{publish_time}\nURL：{url}\n内容：{content}\n\n"
        
        if self.conversation_history:
            recent_history = self.conversation_history[-5:]
            context += "历史对话：\n"
            for i, (q, a) in enumerate(recent_history):
                context += f"用户：{q}\n助手：{a}\n"
            context += "\n"
        
        context += f"用户问题：{query}\n"
        context += "请基于上述知识，用中文回答用户问题。"
        
        return context
    
    def generate_response(self, query, start_date=None, end_date=None):
        """生成回答"""
        if self.is_statistics_query(query):
            answer = self.generate_statistics_response()
            self.conversation_history.append((query, answer))
            return answer
        
        relevant_docs = self.search_relevant_docs(query, start_date, end_date)
        
        if not relevant_docs:
            prompt = f"用户问题：{query}\n请用中文回答。"
        else:
            prompt = self.build_prompt(query, relevant_docs)
        
        import requests
        try:
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
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                self.conversation_history.append((query, answer))
                
                return answer
            else:
                return f"抱歉，我暂时无法回答这个问题。错误: {response.status_code}"
        except Exception as e:
            return f"抱歉，我暂时无法回答这个问题。错误: {str(e)}"

    def get_statistics(self):
        """获取统计信息"""
        return self.vector_db.get_statistics()

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        return "对话历史已清空"

# API端点
@app.route('/api/chat', methods=['POST'])
def chat():
    """对话API端点"""
    data = request.json
    session_id = data.get('session_id', 'default')
    query = data.get('query', '')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # 如果会话不存在，创建新的
    if session_id not in chat_instances:
        chat_instances[session_id] = VectorKnowledgeChatAPI()
    
    # 处理特殊命令
    if query.lower() == 'stats':
        stats = chat_instances[session_id].get_statistics()
        return jsonify({
            'status': 'success',
            'answer': stats
        })
    elif query.lower() == 'clear':
        result = chat_instances[session_id].clear_history()
        return jsonify({
            'status': 'success',
            'answer': result
        })
    
    # 生成回答
    answer = chat_instances[session_id].generate_response(query, start_date, end_date)
    
    return jsonify({
        'status': 'success',
        'answer': answer
    })

@app.route('/api/init', methods=['POST'])
def init():
    """初始化API端点"""
    data = request.json
    session_id = data.get('session_id', 'default')
    
    # 初始化参数
    ollama_url = data.get('ollama_url', 'http://localhost:11434/api/generate')
    model = data.get('model', 'deepseek-r1:7b')
    index_path = data.get('index_path', '/Users/zhangpeng/Desktop/zpskt/easy-crawler/vector_index.faiss')
    metadata_path = data.get('metadata_path', '/Users/zhangpeng/Desktop/zpskt/easy-crawler/vector_metadata.json')
    embedding_model = data.get('embedding_model', 'all-MiniLM-L6-v2')
    top_k_docs = data.get('top_k_docs', 10)
    timeout = data.get('timeout', 300)
    
    # 创建新的对话实例
    chat_instances[session_id] = VectorKnowledgeChatAPI(
        ollama_url=ollama_url,
        model=model,
        index_path=index_path,
        metadata_path=metadata_path,
        embedding_model=embedding_model,
        top_k_docs=top_k_docs,
        timeout=timeout
    )
    
    # 获取统计信息
    stats = chat_instances[session_id].get_statistics()
    
    return jsonify({
        'status': 'success',
        'message': '初始化成功',
        'statistics': stats
    })

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息API端点"""
    # 如果没有默认会话，创建一个临时的来获取统计信息
    if 'default' not in chat_instances:
        temp_chat = VectorKnowledgeChatAPI(
            index_path='/Users/zhangpeng/Desktop/zpskt/easy-crawler/vector_index.faiss',
            metadata_path='/Users/zhangpeng/Desktop/zpskt/easy-crawler/vector_metadata.json'
        )
        stats = temp_chat.get_statistics()
    else:
        stats = chat_instances['default'].get_statistics()
    
    return jsonify({
        'status': 'success',
        'statistics': stats
    })

@app.after_request
def after_request(response):
    """添加CORS支持"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='向量数据库知识对话API服务')
    parser.add_argument('--port', '-p', type=int, default=5001, help='服务器端口，默认5000')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机，默认0.0.0.0')
    parser.add_argument('--debug', action='store_true', default=True, help='启用调试模式')
    args = parser.parse_args()
    
    # 启动API服务
    app.run(host=args.host, port=args.port, debug=args.debug)