#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/1 10:00
# @Author  : zhangpeng /zpskt
# @File    : universal_page_crawler.py
# @Software: PyCharm
# 通用页面爬虫 - 直接提供请求链接列表的方式进行爬取

import time
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入配置
from scripts.config import CRAWLER_PAGE_CONFIG

from src.core.crawler import UniversalWebExtractor
from src.storage.data_persistence import get_default_manager
from tqdm import tqdm
from bs4 import BeautifulSoup

# 尝试导入向量数据库相关模块
try:
    from src.storage.vector_db import FAISSPersistence
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

# 默认配置


class UniversalPageCrawler:
    """通用页面爬虫，支持直接提供URL列表进行爬取"""
    
    def __init__(self):
        """初始化爬虫"""
        self.persistence_manager = get_default_manager()
        
        # 初始化FAISS向量数据库（如果可用）
        self.faiss_db = None
        if HAS_FAISS:
            try:
                self.faiss_db = FAISSPersistence()
                print("FAISS向量数据库已初始化")
            except Exception as e:
                print(f"初始化FAISS向量数据库失败: {e}")

    def extract_article_links(self, html, base_url):
        """从页面提取文章列表链接"""
        article_links = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试多种可能的文章链接选择器
            selectors = [
                'a[href*="/2025/"]',  # 包含年份的文章链接
                '.newslist a',  # 可能的新闻列表链接
                '.artlist a',   # 可能的文章列表链接
                'a.title',      # 可能的标题链接
                '.list_con a',  # 可能的列表内容链接
                '.item a'       # 可能的项目链接
            ]
            
            found_links = set()  # 用于去重
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    title = link.text.strip()
                    
                    if href and title and href not in found_links:
                        # 处理相对路径
                        from urllib.parse import urljoin
                        full_url = urljoin(base_url, href)
                        
                        # 确保是文章详情页链接
                        if ('/20' in href or '/202' in href) and (href.endswith('.shtml') or href.endswith('.html')):
                            article_links.append({
                                'url': full_url,
                                'title': title
                            })
                            found_links.add(href)
            
        except Exception as e:
            print(f"提取文章链接时出错: {e}")
        
        return article_links
        
    def extract_publish_time(self, html):
        """从文章HTML中提取发布时间"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试多种可能的发布时间选择器
            time_selectors = [
                '.time',  # 可能的时间类
                '.pubtime',  # 可能的发布时间类
                '.release-time',  # 可能的发布时间类
                'span.time',  # 可能的时间标签
                'div[class*="time"]',  # 包含time的类名
                'meta[name="pubdate"]',  # meta标签中的发布时间
                'meta[property="article:published_time"]',  # Open Graph协议的发布时间
            ]
            
            for selector in time_selectors:
                elements = soup.select(selector)
                if elements:
                    # 对于meta标签，获取content属性
                    if selector.startswith('meta'):
                        content = elements[0].get('content', '')
                        if content:
                            return content
                    else:
                        # 对于普通标签，获取文本内容
                        text = elements[0].get_text(strip=True)
                        # 匹配常见的日期格式
                        import re
                        date_patterns = [
                            r'\d{4}-\d{2}-\d{2}',  # 2025-09-21
                            r'\d{4}\/\d{2}\/\d{2}',  # 2025/09/21
                            r'\d{2}\/\d{2}\/\d{4}',  # 09/21/2025
                            r'\d{4}年\d{1,2}月\d{1,2}日',  # 2025年9月21日
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, text)
                            if match:
                                return match.group()
            
        except Exception as e:
            print(f"提取发布时间时出错: {e}")
        
        return None

    def crawl_page(self, url, use_selenium=False, extract_articles=True):
        """爬取单个页面"""
        try:
            extractor = UniversalWebExtractor(use_selenium=use_selenium)
            
            # 获取页面HTML（直接调用底层方法获取原始HTML）
            if use_selenium:
                html = extractor.get_content_with_selenium(url)
            else:
                html = extractor.get_content_with_requests(url)
            
            # 如果需要提取文章列表链接
            article_links = []
            if extract_articles:
                article_links = self.extract_article_links(html, url)
                
                # 尝试从文章详情页提取发布时间
                for article in article_links:
                    try:
                        # 获取文章详情页内容
                        if use_selenium:
                            article_html = extractor.get_content_with_selenium(article['url'])
                        else:
                            article_html = extractor.get_content_with_requests(article['url'])
                        
                        # 提取发布时间
                        publish_time = self.extract_publish_time(article_html)
                        if publish_time:
                            article['publish_time'] = publish_time
                    except Exception as e:
                        print(f"提取文章 {article['url']} 发布时间时出错: {e}")
                        article['publish_time'] = None
            
            # 使用smart_extract获取页面内容
            result = extractor.smart_extract(url)
            extractor.close()
            
            # 添加元数据
            result['crawl_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 添加文章列表链接
            if extract_articles:
                result['article_links'] = article_links
                result['article_count'] = len(article_links)
            
            return result
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'article_links': [],
                'article_count': 0
            }
    
    def batch_crawl(self, urls, use_selenium=False, extract_articles=True,
                    output_file=None, use_vector_db=False):
        """批量爬取指定的URL列表"""
        if not urls:
            print("没有提供有效的URL，爬取任务取消")
            return []
        
        print(f"开始爬取 {len(urls)} 个页面...")
        
        # 开始爬取
        results = []
        for url in tqdm(urls, desc="爬取进度"):
            print(f"正在爬取: {url}")
            result = self.crawl_page(url, use_selenium, extract_articles)
            results.append(result)
        
        # 保存结果到JSON文件
        if output_file:
            self.persistence_manager.save_with_method('json', results, output_file)
        else:
            # 默认文件名
            default_output = f"universal_crawl_{time.strftime('%Y%m%d_%H%M%S')}.json"
            self.persistence_manager.save_with_method('json', results, default_output)
        
        # 生成HTML报告
        self.persistence_manager.save_with_method('html_report', results)
        
        # 如果启用了向量数据库，并且FAISS可用，保存到向量数据库
        if use_vector_db and self.faiss_db:
            # 过滤出成功爬取的文档
            success_docs = [r for r in results if 'error' not in r]
            if success_docs:
                print(f"将 {len(success_docs)} 个文档保存到向量数据库...")
                self.faiss_db.save(success_docs)
        
        return results


def main():
    """主函数"""
    # 加载配置
    config = CRAWLER_PAGE_CONFIG
    
    crawler = UniversalPageCrawler()
    
    # 执行爬取
    crawler.batch_crawl(
        urls=config['urls'],
        use_selenium=config['use_selenium'],
        extract_articles=config['extract_articles'],
        output_file=config['output_file'],
        use_vector_db=config['use_vector_db']
    )

if __name__ == "__main__":
    # 此示例是爬取网页中所有文章的链接和标题
    main()