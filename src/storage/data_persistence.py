#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/27 14:00
# @Author  : zhangpeng /zpskt
# @File    : data_persistence.py
# @Software: PyCharm
# 数据持久化模块 - 支持多种数据持久化方式

import json
import pandas as pd
from abc import ABC, abstractmethod

# 导入FAISS持久化（先尝试导入，如果失败则继续）
try:
    from src.storage.vector_db import FAISSPersistence
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

class DataPersistence(ABC):
    """数据持久化抽象基类"""
    
    @abstractmethod
    def save(self, data, output_path=None):
        """保存数据"""
        pass


class JSONPersistence(DataPersistence):
    """JSON文件持久化实现"""
    
    def save(self, data, output_path=None):
        """将数据保存为JSON文件"""
        if output_path is None:
            raise ValueError("必须提供输出文件路径")
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"数据已保存到JSON文件: {output_path}")
        return output_path


class HTMLReportPersistence(DataPersistence):
    """HTML报告持久化实现"""
    
    def save(self, data, output_path=None):
        """生成并保存HTML统计报告"""
        if output_path is None:
            output_path = 'extraction_report.html'
            
        # 计算统计数据
        total = len(data)
        successful = sum(1 for r in data if 'error' not in r)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # 计算平均内容长度和图片数量
        if successful > 0:
            avg_content_length = sum(r.get('content_length', 0) for r in data if 'error' not in r) / successful
            avg_image_count = sum(r.get('image_count', 0) for r in data if 'error' not in r) / successful
        else:
            avg_content_length = 0
            avg_image_count = 0
        
        # 提取方法统计
        source_stats = {}
        for r in data:
            if 'error' not in r and 'source' in r:
                source = r['source']
                source_stats[source] = source_stats.get(source, 0) + 1
        
        # 创建HTML报告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>网页内容提取报告</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .summary {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background-color: #fff;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #3498db;
                    margin-bottom: 10px;
                }}
                .stat-label {{
                    color: #7f8c8d;
                    font-size: 1.1em;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .success {{ color: #27ae60; }}
                .error {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>网页内容提取报告</h1>
            
            <div class="summary">
                <h2>总体统计</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{total}</div>
                        <div class="stat-label">总URL数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value success">{successful}</div>
                        <div class="stat-label">成功提取</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value error">{failed}</div>
                        <div class="stat-label">提取失败</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{success_rate:.1f}%</div>
                        <div class="stat-label">成功率</div>
                    </div>
                </div>
            </div>
            
            <div class="summary">
                <h2>内容统计</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{avg_content_length:.0f}</div>
                        <div class="stat-label">平均内容长度</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_image_count:.1f}</div>
                        <div class="stat-label">平均图片数量</div>
                    </div>
                </div>
            </div>
            
            <h2>提取方法统计</h2>
            <table>
                <tr>
                    <th>提取方法</th>
                    <th>使用次数</th>
                    <th>占比</th>
                </tr>
        """
        
        # 添加提取方法统计行
        for source, count in source_stats.items():
            percentage = (count / successful * 100) if successful > 0 else 0
            html_content += f"""
                <tr>
                    <td>{source}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        # 添加详细结果表格
        html_content += f"""
            </table>
            
            <h2>详细结果</h2>
            <table>
                <tr>
                    <th>URL</th>
                    <th>状态</th>
                    <th>标题</th>
                    <th>内容长度</th>
                    <th>图片数量</th>
                    <th>提取方法</th>
                </tr>
        """
        
        # 添加详细结果行
        for result in data:
            url = result.get('url', '')
            status = '成功' if 'error' not in result else '失败'
            status_class = 'success' if 'error' not in result else 'error'
            title = result.get('title', '')[:50] + '...' if len(result.get('title', '')) > 50 else result.get('title', '')
            content_length = result.get('content_length', 0)
            image_count = result.get('image_count', 0)
            source = result.get('source', '')
            
            html_content += f"""
                <tr>
                    <td>{url}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{title}</td>
                    <td>{content_length}</td>
                    <td>{image_count}</td>
                    <td>{source}</td>
                </tr>
            """
        
        # 结束HTML内容
        html_content += f"""
            </table>
        
            <footer>
                <p style="text-align: center; color: #7f8c8d; margin-top: 50px;">报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </footer>
        </body>
        </html>
        """
        
        # 保存HTML报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"统计报告已保存到: {output_path}")
        return output_path


class APIPersistence(DataPersistence):
    """API接口持久化实现（示例框架）"""
    
    def __init__(self, api_url, api_key=None):
        """初始化API持久化器"""
        self.api_url = api_url
        self.api_key = api_key
        # 这里可以初始化requests会话等
        
    def save(self, data, output_path=None):
        """通过API接口保存数据"""
        # 注意：这是一个示例框架，实际使用时需要根据API规范实现
        print(f"准备通过API保存数据到: {self.api_url}")
        print(f"数据量: {len(data)}条")
        
        # 这里应该实现实际的API调用逻辑
        # 例如：
        # import requests
        # headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        # response = requests.post(self.api_url, json=data, headers=headers)
        # response.raise_for_status()
        
        print("API保存操作已完成（示例）")
        return "api_saved"


class DatabasePersistence(DataPersistence):
    """MySQL数据库持久化实现"""
    
    def __init__(self, db_config=None):
        """初始化数据库持久化类
        
        Args:
            db_config: 数据库配置信息
        """
        self.db_config = db_config or {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'cheaa'
        }
        self.connection = None
        self._connect()
        
    def _connect(self):
        """建立数据库连接"""
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.db_config.get('host', 'localhost'),
                user=self.db_config.get('user'),
                password=self.db_config.get('password'),
                database=self.db_config.get('database'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"成功连接到MySQL数据库: {self.db_config.get('database')}")
            
            # 确保表存在
            self._ensure_tables_exist()
        except Exception as e:
            print(f"连接MySQL数据库失败: {e}")
            self.connection = None
    
    def _ensure_tables_exist(self):
        """确保必要的表存在"""
        if not self.connection:
            return
        
        try:
            with self.connection.cursor() as cursor:
                # 创建文章表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(512) NOT NULL UNIQUE,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    publish_time DATETIME,
                    channel VARCHAR(100),
                    channel_name VARCHAR(100),
                    module VARCHAR(100),
                    module_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_channel (channel),
                    INDEX idx_module (module),
                    INDEX idx_publish_time (publish_time)
                )
                ''')
                
                # 创建分析结果表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_analyses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    article_id INT NOT NULL,
                    summary TEXT,
                    keywords JSON,
                    key_points JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                    UNIQUE INDEX idx_article_id (article_id)
                )
                ''')
                
                # 创建每日汇总表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    total_articles INT NOT NULL,
                    new_articles INT NOT NULL,
                    summary_file VARCHAR(255),
                    analysis_file VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                ''')
            self.connection.commit()
            print("确保表存在完成")
        except Exception as e:
            print(f"创建表失败: {e}")
            if self.connection:
                self.connection.rollback()
    
    def save(self, data, output_path=None):
        """保存数据到数据库
        
        Args:
            data: 要保存的数据
            output_path: 输出路径（在数据库持久化中可能不需要）
        
        Returns:
            str: 保存结果信息
        """
        if not self.connection:
            self._connect()
            if not self.connection:
                return "数据库连接失败，无法保存数据"
        
        if not data:
            return "没有数据需要保存"
        
        # 确保数据是列表格式
        if not isinstance(data, list):
            data = [data]
        
        saved_count = 0
        try:
            with self.connection.cursor() as cursor:
                for item in data:
                    # 跳过有错误的数据
                    if 'error' in item:
                        continue
                    
                    # 保存文章基本信息
                    cursor.execute(
                        """
                        INSERT INTO articles (url, title, content, publish_time, channel, channel_name, module, module_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            title = VALUES(title),
                            content = VALUES(content),
                            publish_time = VALUES(publish_time),
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            item.get('url', ''),
                            item.get('title', ''),
                            item.get('content', ''),
                            item.get('publish_time'),
                            item.get('channel', ''),
                            item.get('channel_name', ''),
                            item.get('module', ''),
                            item.get('module_name', '')
                        )
                    )
                    saved_count += 1
            
            self.connection.commit()
            return f"成功保存 {saved_count} 条数据到数据库"
        except Exception as e:
            print(f"保存数据到数据库失败: {e}")
            if self.connection:
                self.connection.rollback()
            return f"保存失败: {str(e)}"
        finally:
            pass
            # 可选：关闭连接
            # if self.connection:
            #     self.connection.close()


class PersistenceManager:
    """持久化管理器 - 用于管理和协调多种持久化方式"""
    
    def __init__(self):
        """初始化持久化管理器"""
        self.persistence_methods = {}
        
    def register_persistence(self, name, persistence_instance):
        """注册持久化方法"""
        if not isinstance(persistence_instance, DataPersistence):
            raise TypeError("持久化实例必须是DataPersistence的子类")
        self.persistence_methods[name] = persistence_instance
        
    def save_with_method(self, name, data, output_path=None):
        """使用指定的持久化方法保存数据"""
        if name not in self.persistence_methods:
            raise ValueError(f"未找到名为'{name}'的持久化方法")
        return self.persistence_methods[name].save(data, output_path)
    
    def save_all(self, data, config=None):
        """使用所有已配置的持久化方法保存数据"""
        results = {}
        if config is None:
            config = {}
            
        for name, instance in self.persistence_methods.items():
            output_path = config.get(name)
            results[name] = instance.save(data, output_path)
            
        return results


# 默认管理器实例
_default_manager = None


def get_default_manager():
    """获取默认的持久化管理器实例"""
    global _default_manager
    
    if _default_manager is None:
        _default_manager = PersistenceManager()
        
        # 注册默认的持久化方法
        _default_manager.register_persistence('json', JSONPersistence())
        _default_manager.register_persistence('html_report', HTMLReportPersistence())
        
        # 如果FAISS可用，注册FAISS持久化
        if HAS_FAISS:
            try:
                _default_manager.register_persistence('faiss', FAISSPersistence())
            except Exception as e:
                print(f"注册FAISS持久化失败: {e}")
    
    return _default_manager


# 示例用法
if __name__ == "__main__":
    # 示例数据
    sample_data = [
        {'url': 'https://example.com', 'title': '示例页面', 'content': '示例内容', 'content_length': 100, 'image_count': 2, 'source': 'trafilatura'},
        {'url': 'https://example.org', 'error': '无法访问'}
    ]
    
    # 使用默认管理器
    manager = get_default_manager()
    manager.save_with_method('json', sample_data, 'sample_output.json')
    manager.save_with_method('html_report', sample_data)
    
    # 注册并使用自定义持久化方法
    # manager.register_persistence('api', APIPersistence('https://api.example.com/save'))
    # manager.save_with_method('api', sample_data)