#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/1 10:00
# @Author  : zhangpeng /zpskt
# @File    : cheaa_full_crawler.py
# @Software: PyCharm
# 中国家电网完整爬虫 - 先获取文章链接，再爬取详细内容
import json
import os
import random
import sys
import time

from scripts.config import CRAWLER_PAGE_CONFIG, SINGLE_PAGE_CONFIG
from src.business.universal_page_crawler import UniversalPageCrawler
from src.core.crawler import UniversalWebExtractor

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 然后再导入其他模块

# # 尝试导入并注册FAISS持久化
# try:
#     from src.storage.vector_db import FAISSPersistence
#     # 获取默认管理器
#     default_manager = get_default_manager()
#     # 注册FAISS持久化（如果尚未注册）
#     if 'faiss' not in default_manager.persistence_methods:
#         default_manager.register_persistence('faiss', FAISSPersistence())
#         print("成功注册FAISS持久化")
# except Exception as e:
#     print(f"注册FAISS持久化失败: {e}")

def main():
    """主函数"""
    config = CRAWLER_PAGE_CONFIG

    crawler = UniversalPageCrawler()

    # 执行爬取
    articles = crawler.batch_crawl(urls=config['urls'], use_selenium=config['use_selenium'],
                                extract_articles=config['extract_articles'], output_file=config['output_file'],
                                use_vector_db=config['use_vector_db'])
    print(f"爬取完成，共获取到{len(articles)}篇文章")
    article_links = articles[0].get('article_links', [])

    # 初始化单网页内容提取器
    extractor = UniversalWebExtractor(use_selenium=False)
    results = []
    print(f"开始提取{len(article_links)}篇文章的详细内容")
    for article in article_links:
        print(f"正在处理第{article_links.index(article) + 1}篇文章: {article['url']}")
        result = extractor.smart_extract(article['url'])
        results.append(result)
        # 避免请求过快
        time.sleep(2)
    # 关闭提取器
    extractor.close()

    # 保存详细结果到文件
    filename_pattern = SINGLE_PAGE_CONFIG.get('output_file') + 'single_result_{}.json'
    timestamp = int(time.time())
    random_num = random.randint(1000, 9999)
    filename = filename_pattern.format(timestamp + random_num)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"已保存{len(results)}篇文章的详细内容到文件")


if __name__ == "__main__":
    main()
