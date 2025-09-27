#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量数据库持久化模块 - 使用FAISS实现向量存储和检索
"""
import json
import os
import numpy as np
import faiss
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple
from src.storage.data_persistence import DataPersistence
from sentence_transformers import SentenceTransformer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAISSPersistence(DataPersistence):
    """FAISS向量数据库持久化实现"""
    
    def __init__(self, index_path: str = 'vector_index.faiss', 
                 metadata_path: str = 'vector_metadata.json',
                 embedding_model: str = 'all-MiniLM-L6-v2'):
        """初始化FAISS向量数据库
        
        Args:
            index_path: FAISS索引文件路径
            metadata_path: 元数据文件路径
            embedding_model: 用于生成向量的预训练模型
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model = embedding_model
        
        # 加载嵌入模型
        try:
            self.model = SentenceTransformer(embedding_model)
            logger.info(f"成功加载嵌入模型: {embedding_model}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}")
            raise
        
        # 加载或创建FAISS索引
        self.index = None
        self.metadata = []  # 存储与向量对应的元数据
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """加载已有的索引或创建新索引"""
        try:
            # 尝试加载现有的索引和元数据
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"成功加载现有索引，包含 {len(self.metadata)} 个文档")
            else:
                # 创建新的索引
                embedding_dim = 384  # all-MiniLM-L6-v2模型的输出维度
                self.index = faiss.IndexFlatL2(embedding_dim)  # 使用L2距离的扁平索引
                self.metadata = []
                logger.info("创建了新的FAISS索引")
        except Exception as e:
            logger.error(f"加载或创建索引时出错: {e}")
            # 回退到创建新索引
            embedding_dim = 384
            self.index = faiss.IndexFlatL2(embedding_dim)
            self.metadata = []
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本的向量嵌入
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            向量嵌入数组
        """
        try:
            # 限制文本长度以避免处理过大的文本
            max_length = 512  # 模型的最大序列长度
            if len(text) > max_length:
                text = text[:max_length]
            
            # 生成嵌入
            embedding = self.model.encode([text])[0]
            return np.array([embedding], dtype=np.float32)
        except Exception as e:
            logger.error(f"生成嵌入时出错: {e}")
            # 返回零向量作为后备
            return np.zeros((1, 384), dtype=np.float32)
    
    def save(self, data: Union[Dict, List[Dict]], output_path: Optional[str] = None):
        """将数据保存到FAISS向量数据库
        
        Args:
            data: 要保存的数据，可以是单个文档或文档列表
            output_path: 输出路径（这里忽略，使用初始化时设置的路径）
            
        Returns:
            保存结果信息
        """
        try:
            # 确保数据是列表格式
            if isinstance(data, dict):
                data = [data]
            
            # 为每个文档生成嵌入并添加到索引
            new_embeddings = []
            new_metadata = []
            
            for doc in data:
                # 检查文档是否包含必要字段
                if 'content' not in doc:
                    logger.warning("文档缺少content字段，跳过")
                    continue
                
                # 生成嵌入
                embedding = self._generate_embedding(doc['content'])
                new_embeddings.append(embedding)
                
                # 准备元数据
                metadata_item = {
                    'title': doc.get('title', ''),
                    'content': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                    'url': doc.get('url', ''),
                    'publish_time': doc.get('publish_time', doc.get('date', '')),
                    'extraction_time': doc.get('extraction_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'channel': doc.get('channel', ''),
                    'channel_name': doc.get('channel_name', ''),
                    'module': doc.get('module', ''),
                    'module_name': doc.get('module_name', ''),
                    'summary': doc.get('summary', ''),
                    'keywords': doc.get('keywords', []),
                    'key_points': doc.get('key_points', [])
                }
                new_metadata.append(metadata_item)
            
            # 如果有新的嵌入，添加到索引
            if new_embeddings:
                # 合并所有新嵌入
                embeddings_array = np.vstack(new_embeddings)
                
                # 添加到FAISS索引
                self.index.add(embeddings_array)
                
                # 更新元数据
                self.metadata.extend(new_metadata)
                
                # 保存索引和元数据
                self._save_index()
                
                logger.info(f"成功添加 {len(new_embeddings)} 个文档到向量数据库")
            else:
                logger.warning("没有有效的文档添加到向量数据库")
            
            return f"成功添加 {len(new_embeddings)} 个文档到向量数据库，当前总文档数: {len(self.metadata)}"
        except Exception as e:
            logger.error(f"保存数据到向量数据库时出错: {e}")
            return f"保存失败: {str(e)}"
    
    def _save_index(self):
        """保存索引和元数据到文件"""
        try:
            # 保存FAISS索引
            faiss.write_index(self.index, self.index_path)
            
            # 保存元数据
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                
            logger.info(f"索引和元数据已保存到 {self.index_path} 和 {self.metadata_path}")
        except Exception as e:
            logger.error(f"保存索引和元数据时出错: {e}")
    
    def search(self, query: str, top_k: int = 5, 
               start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Dict]:
        """在向量数据库中搜索相关文档
        
        Args:
            query: 搜索查询文本
            top_k: 返回的最大结果数
            start_date: 开始日期（YYYY-MM-DD或YYYY-MM-DD HH:MM:SS格式）
            end_date: 结束日期（YYYY-MM-DD或YYYY-MM-DD HH:MM:SS格式）
            
        Returns:
            搜索结果列表
        """
        try:
            if self.index is None or len(self.metadata) == 0:
                logger.warning("向量数据库为空")
                return []
            
            # 生成查询向量
            query_embedding = self._generate_embedding(query)
            
            # 在FAISS中搜索
            distances, indices = self.index.search(query_embedding, min(top_k * 2, len(self.metadata)))
            
            # 准备搜索结果
            results = []
            for i, idx in enumerate(indices[0]):
                # 获取元数据
                metadata = self.metadata[idx]
                
                # 检查日期范围
                if start_date or end_date:
                    doc_date = metadata.get('publish_time') or metadata.get('extraction_time')
                    if doc_date:
                        try:
                            # 尝试解析日期
                            doc_datetime = None
                            # 尝试多种日期格式
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                                try:
                                    doc_datetime = datetime.strptime(doc_date.split(' ')[0], fmt)
                                    break
                                except ValueError:
                                    continue
                            
                            # 检查日期是否在范围内
                            if doc_datetime:
                                # 解析开始和结束日期
                                start_datetime = datetime.strptime(start_date.split(' ')[0], '%Y-%m-%d') if start_date else None
                                end_datetime = datetime.strptime(end_date.split(' ')[0], '%Y-%m-%d') if end_date else None
                                
                                # 如果有结束日期，将其设置为当天结束
                                if end_datetime:
                                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                                
                                # 检查日期范围
                                if start_datetime and doc_datetime < start_datetime:
                                    continue
                                if end_datetime and doc_datetime > end_datetime:
                                    continue
                        except Exception as e:
                            logger.warning(f"解析日期时出错: {e}")
                            # 如果日期解析失败，仍然包含该文档
                
                # 添加结果
                result = metadata.copy()
                result['distance'] = float(distances[0][i])  # 添加相似度分数
                results.append(result)
            
            # 按相似度排序并限制返回数量
            results.sort(key=lambda x: x['distance'])
            return results[:top_k]
        except Exception as e:
            logger.error(f"搜索向量数据库时出错: {e}")
            return []
    
    def get_by_date_range(self, start_date: str, end_date: str, top_k: int = 20) -> List[Dict]:
        """按日期范围获取文档
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            top_k: 返回的最大结果数
            
        Returns:
            符合条件的文档列表
        """
        try:
            if not self.metadata:
                logger.warning("向量数据库为空")
                return []
            
            # 解析日期范围
            try:
                start_datetime = datetime.strptime(start_date.split(' ')[0], '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date.split(' ')[0], '%Y-%m-%d')
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except Exception as e:
                logger.error(f"解析日期范围时出错: {e}")
                return []
            
            # 筛选符合日期范围的文档
            results = []
            for metadata in self.metadata:
                doc_date = metadata.get('publish_time') or metadata.get('extraction_time')
                if doc_date:
                    try:
                        # 尝试解析文档日期
                        doc_datetime = None
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                            try:
                                doc_datetime = datetime.strptime(doc_date.split(' ')[0], fmt)
                                break
                            except ValueError:
                                continue
                        
                        # 检查是否在日期范围内
                        if doc_datetime and start_datetime <= doc_datetime <= end_datetime:
                            results.append(metadata)
                    except Exception as e:
                        logger.warning(f"解析文档日期时出错: {e}")
            
            # 按日期排序并限制结果数量
            results.sort(key=lambda x: (x.get('publish_time') or x.get('extraction_time')), reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"按日期范围查询时出错: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """获取向量数据库的统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {
                'total_documents': len(self.metadata),
                'index_size': os.path.getsize(self.index_path) if os.path.exists(self.index_path) else 0,
                'metadata_size': os.path.getsize(self.metadata_path) if os.path.exists(self.metadata_path) else 0,
                'embedding_model': self.embedding_model,
                'index_type': str(type(self.index))
            }
            
            # 按频道统计
            channel_stats = {}
            for metadata in self.metadata:
                channel = metadata.get('channel', 'unknown')
                channel_stats[channel] = channel_stats.get(channel, 0) + 1
            stats['channels'] = channel_stats
            
            # 按日期统计
            date_stats = {}
            for metadata in self.metadata:
                doc_date = metadata.get('publish_time') or metadata.get('extraction_time')
                if doc_date:
                    try:
                        # 提取日期部分
                        date_part = doc_date.split(' ')[0]
                        # 尝试标准化日期格式
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                            try:
                                parsed_date = datetime.strptime(date_part, fmt)
                                date_key = parsed_date.strftime('%Y-%m-%d')
                                date_stats[date_key] = date_stats.get(date_key, 0) + 1
                                break
                            except ValueError:
                                continue
                    except Exception:
                        # 如果无法解析日期，使用原始日期字符串
                        date_stats[date_part] = date_stats.get(date_part, 0) + 1
            stats['dates'] = date_stats
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            return {'error': str(e)}

# 添加到默认的持久化管理器
from src.storage.data_persistence import get_default_manager

def register_faiss_persistence():
    """注册FAISS持久化到默认管理器"""
    try:
        manager = get_default_manager()
        # 注册FAISS持久化实现
        manager.register_persistence('faiss', FAISSPersistence())
        logger.info("FAISS持久化已注册到默认管理器")
    except Exception as e:
        logger.error(f"注册FAISS持久化时出错: {e}")

# 如果直接运行此脚本，提供一些示例用法
if __name__ == "__main__":
    # 创建FAISS持久化实例
    try:
        faiss_persistence = FAISSPersistence()
        
        # 打印统计信息
        stats = faiss_persistence.get_statistics()
        print("向量数据库统计信息:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        
        # 示例搜索
        # results = faiss_persistence.search("冰箱新品", top_k=5)
        # print("\n搜索结果:")
        # for i, result in enumerate(results):
        #     print(f"{i+1}. {result['title']} (相似度: {result['distance']:.4f})")
        #     print(f"   URL: {result['url']}")
        #     print(f"   摘要: {result['summary']}\n")
            
        # 示例按日期范围查询
        # end_date = datetime.now().strftime('%Y-%m-%d')
        # start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        # recent_docs = faiss_persistence.get_by_date_range(start_date, end_date)
        # print(f"\n最近10天的文档 ({start_date} 至 {end_date}):")
        # for i, doc in enumerate(recent_docs[:5]):
        #     print(f"{i+1}. {doc['title']}")
        #     print(f"   发布时间: {doc.get('publish_time', '未知')}")
        #     print(f"   URL: {doc['url']}\n")
            
    except Exception as e:
        print(f"运行示例时出错: {e}")