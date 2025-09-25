#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/25 21:59
# @Author  : zhangpeng /zpskt
# @File    : batch_processor.py
# @Software: PyCharm
# batch_processor.py
import pandas as pd
from crawler import UniversalWebExtractor
from tqdm import tqdm
from data_persistence import get_default_manager, JSONPersistence, HTMLReportPersistence, PersistenceManager, APIPersistence, DatabasePersistence


class BatchProcessor:
    """批量URL处理类"""
    
    def __init__(self):
        """初始化批处理器"""
        self.persistence_manager = get_default_manager()
        
    def add_persistence_method(self, name, persistence_instance):
        """添加自定义持久化方法"""
        self.persistence_manager.register_persistence(name, persistence_instance)
        
    def process_urls(self, urls_file, output_file, use_selenium=False, persistence_config=None):
        """批量处理URL列表"""
        # 读取URL列表
        df = pd.read_csv(urls_file) if urls_file.endswith('.csv') else pd.read_excel(urls_file)
        urls = df['url'].tolist()

        extractor = UniversalWebExtractor(use_selenium=use_selenium)
        results = []

        for url in tqdm(urls, desc="处理进度"):
            try:
                result = extractor.smart_extract(url)
                results.append(result)
            except Exception as e:
                results.append({'url': url, 'error': str(e)})

        extractor.close()

        # 使用持久化管理器保存结果
        if persistence_config:
            # 使用配置的持久化方法
            self.persistence_manager.save_all(results, persistence_config)
        else:
            # 默认保存为JSON和HTML报告
            self.persistence_manager.save_with_method('json', results, output_file)
            self.persistence_manager.save_with_method('html_report', results)
        
        return results


# 兼容旧版API的函数

def batch_process_urls(urls_file, output_file, use_selenium=False):
    """批量处理URL列表（兼容旧版API）"""
    processor = BatchProcessor()
    return processor.process_urls(urls_file, output_file, use_selenium)


# 使用示例
if __name__ == "__main__":
    # 基本用法
    batch_process_urls('urls.csv', 'extraction_results.json', use_selenium=False)
    
    # 高级用法 - 使用BatchProcessor类
    """
    processor = BatchProcessor()
    
    # 添加自定义持久化方法（示例）
    # processor.add_persistence_method('api', APIPersistence('https://api.example.com/save'))
    # processor.add_persistence_method('database', DatabasePersistence('connection_string'))
    
    # 配置要使用的持久化方法
    persistence_config = {
        'json': 'extraction_results.json',
        'html_report': 'custom_report.html'
        # 'api': None,  # API持久化不需要output_path
        # 'database': None  # 数据库持久化不需要output_path
    }
    
    # 处理URL并保存结果
    processor.process_urls('urls.csv', 'extraction_results.json', use_selenium=False, persistence_config=persistence_config)
    """