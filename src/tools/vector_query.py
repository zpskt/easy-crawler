#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量数据库查询工具
"""
import argparse
import json
from datetime import datetime, timedelta
from src.storage.vector_db import FAISSPersistence


class VectorQueryTool:
    """向量数据库查询工具"""
    
    def __init__(self):
        """初始化查询工具"""
        self.faiss_db = FAISSPersistence()
    
    def search(self, query, top_k=5, start_date=None, end_date=None):
        """搜索相关文档"""
        results = self.faiss_db.search(query, top_k, start_date, end_date)
        
        if not results:
            print("未找到相关文档")
            return
        
        print(f"找到 {len(results)} 个相关文档:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   相似度: {result['distance']:.4f}")
            print(f"   发布时间: {result.get('publish_time', '未知')}")
            print(f"   URL: {result['url']}")
            print(f"   摘要: {result.get('summary', '')[:150]}...\n")
            
    def get_recent_docs(self, days=10, top_k=20):
        """获取最近几天的文档"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        print(f"获取最近 {days} 天的文档 ({start_date} 至 {end_date})...\n")
        results = self.faiss_db.get_by_date_range(start_date, end_date, top_k)
        
        if not results:
            print(f"未找到最近 {days} 天的文档")
            return
        
        print(f"找到 {len(results)} 个文档:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   发布时间: {result.get('publish_time', '未知')}")
            print(f"   URL: {result['url']}")
            print(f"   频道: {result.get('channel_name', result.get('channel', ''))}\n")
    
    def show_statistics(self):
        """显示向量数据库统计信息"""
        stats = self.faiss_db.get_statistics()
        print("向量数据库统计信息:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='向量数据库查询工具')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索相关文档')
    search_parser.add_argument('query', help='搜索查询文本')
    search_parser.add_argument('--top-k', type=int, default=5, help='返回的最大结果数')
    search_parser.add_argument('--start-date', help='开始日期（YYYY-MM-DD格式）')
    search_parser.add_argument('--end-date', help='结束日期（YYYY-MM-DD格式）')
    
    # recent 命令
    recent_parser = subparsers.add_parser('recent', help='获取最近几天的文档')
    recent_parser.add_argument('--days', type=int, default=10, help='天数')
    recent_parser.add_argument('--top-k', type=int, default=20, help='返回的最大结果数')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示向量数据库统计信息')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    tool = VectorQueryTool()
    
    if args.command == 'search':
        tool.search(args.query, args.top_k, args.start_date, args.end_date)
    elif args.command == 'recent':
        tool.get_recent_docs(args.days, args.top_k)
    elif args.command == 'stats':
        tool.show_statistics()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()