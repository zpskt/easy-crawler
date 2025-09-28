#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/2 10:00
# @Author  : zhangpeng /zpskt
# @File    : daily_crawler_analyzer.py
# @Software: PyCharm
# 每日爬取和分析系统 - 自动爬取中国家电网数据并通过API传输

import json
import logging
import os
import sys
import time
from datetime import datetime

import requests
from tqdm import tqdm

from scripts.config import CRAWLER_PAGE_CONFIG, API_CONFIG, OUTPUT_PATHS, LLM_CONFIG

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需模块
from src.core.crawler import UniversalWebExtractor
from src.storage.data_persistence import get_default_manager
from src.llm_analysis.llm_analyzer import LLMAnalyzer
from src.business.universal_page_crawler import UniversalPageCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_faiss():
    """设置FAISS向量数据库（可选功能）"""
    try:
        from src.storage.vector_db import FAISSPersistence
        persistence_manager = get_default_manager()
        if 'faiss' not in persistence_manager.persistence_methods:
            persistence_manager.register_persistence('faiss', FAISSPersistence())
            logger.info("成功注册FAISS持久化")
        return persistence_manager
    except Exception as e:
        logger.error(f"注册FAISS持久化失败: {e}")
        return get_default_manager()

def is_article_new(url):
    """检查文章是否已经爬取过（使用本地文件跟踪）
    
    Args:
        url: 文章URL
    
    Returns:
        bool: 是否为新文章
    """
    # 在实际应用中，可以使用本地文件或其他方式来跟踪已爬取的文章
    # 这里简单返回True，表示所有文章都视为新文章
    return True

def save_to_api(data, api_config):
    """通过API传输数据，支持重试逻辑
    
    Args:
        data: 要传输的数据
        api_config: API配置
    
    Returns:
        bool: 是否传输成功
    """
    if not api_config or not api_config.get('url'):
        logger.error("未配置API URL，跳过API传输")
        return False
    
    retry_count = api_config.get('retry_count', 3)
    retry_delay = api_config.get('retry_delay', 5)
    timeout = api_config.get('timeout', 30)
    
    for attempt in range(retry_count):
        try:
            logger.info(f"尝试通过API传输数据到: {api_config.get('url')} (尝试 {attempt+1}/{retry_count})")
            headers = {'Content-Type': 'application/json'}
            if 'api_key' in api_config:
                headers['Authorization'] = f"Bearer {api_config.get('api_key')}"
            
            response = requests.post(
                api_config.get('url'),
                json=data,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                logger.info("成功通过API传输数据")
                return True
            else:
                logger.error(f"API传输失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < retry_count - 1:
                    logger.info(f"{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
        except Exception as e:
            logger.error(f"API传输异常: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < retry_count - 1:
                logger.info(f"{retry_delay}秒后重试...")
                time.sleep(retry_delay)
                continue
            else:
                return False
    
    return False

def crawl_daily_articles(urls=None, batch_size=None, delay=2):
    """爬取每日新文章
    
    Args:
        urls: 要爬取的URL列表
        batch_size: 批处理大小
        delay: 请求间隔
    
    Returns:
        list: 新文章列表
    """
    logger.info(f"开始爬取每日新文章: URLs数量={len(urls) if urls else 0}")
    
    # 初始化爬虫
    crawler = UniversalPageCrawler()
    
    # 如果没有提供URL，则使用默认URL
    if not urls:
        urls = ['https://icebox.cheaa.com/xinpin.shtml']
    
    # 执行爬取获取文章链接
    articles_results = crawler.batch_crawl(
        urls=urls, 
        use_selenium=False,
        extract_articles=True, 
        output_file=None,
        use_vector_db=False
    )
    
    # 合并所有文章链接
    article_urls = []
    for result in articles_results:
        if 'article_links' in result:
            article_urls.extend(result['article_links'])
    
    logger.info(f"获取到 {len(article_urls)} 个文章URL")
    
    # 过滤出新文章
    new_article_urls = []
    for article in article_urls:
        if is_article_new(article['url']):
            new_article_urls.append(article)
            # 如果达到批量大小，停止过滤
            if batch_size and len(new_article_urls) >= batch_size:
                break
    
    logger.info(f"筛选出 {len(new_article_urls)} 篇新文章")
    
    # 爬取文章详细内容
    if not new_article_urls:
        logger.info("没有新文章需要爬取")
        return []
    
    web_extractor = UniversalWebExtractor(use_selenium=False)
    results = []
    for idx, article in enumerate(tqdm(new_article_urls, desc="爬取文章详情")):
        logger.info(f"正在爬取文章 {idx+1}/{len(new_article_urls)}: {article['title']}")
        
        try:
            # 爬取文章详细内容
            result = web_extractor.smart_extract(article['url'])
            
            # 合并文章信息
            result.update({
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'publish_time': article.get('publish_time') or result.get('publish_time')
            })
            
            results.append(result)
        except Exception as e:
            logger.error(f"爬取文章 {article['url']} 时出错: {e}")
            results.append({
                'url': article['url'],
                'title': article['title'],
                'error': str(e)
            })
        
        # 避免请求过快
        if idx < len(new_article_urls) - 1:
            time.sleep(delay)
    
    # 统计结果
    successful = sum(1 for r in results if 'error' not in r)
    failed = len(results) - successful
    
    logger.info(f"爬取完成！成功: {successful}, 失败: {failed}")
    
    # 关闭提取器
    web_extractor.close()
    
    return results

def analyze_articles(articles):
    """分析文章并生成分析报告
    
    Args:
        articles: 文章列表
    
    Returns:
        list: 分析结果列表
    """
    if not articles:
        logger.info("没有文章需要分析")
        return []
    
    # 过滤掉有错误的文章
    valid_articles = [a for a in articles if 'error' not in a]
    if not valid_articles:
        logger.info("没有有效的文章需要分析")
        return []
    
    logger.info(f"开始分析 {len(valid_articles)} 篇文章")
    
    # 初始化LLM分析器
    llm_analyzer = LLMAnalyzer(
        use_real_llm=True,
        ollama_url=LLM_CONFIG.get('ollama_url', 'http://localhost:11434/api/generate'),
        model=LLM_CONFIG.get('model', 'deepseek-r1:7b')
    )
    
    # 批量分析文章
    results = llm_analyzer.batch_analyze(valid_articles)
    
    # 合并文章ID到分析结果中
    for i, result in enumerate(results):
        if i < len(valid_articles) and 'id' in valid_articles[i]:
            result['id'] = valid_articles[i]['id']
            result['title'] = valid_articles[i].get('title', '')
            result['url'] = valid_articles[i].get('url', '')
            result['publish_time'] = valid_articles[i].get('publish_time', '')
    
    logger.info("文章分析完成")
    
    return results

def generate_daily_files(articles, analyses, output_dir=None):
    """生成每日输出文件
    
    Args:
        articles: 文章列表
        analyses: 分析结果列表
        output_dir: 输出目录
    
    Returns:
        tuple: (summary_file_path, analysis_file_path)
    """
    if not articles:
        logger.info("没有文章生成每日文件")
        return None, None
    
    # 设置输出目录
    if not output_dir:
        output_dir = OUTPUT_PATHS.get('daily_reports', '/Users/zhangpeng/Desktop/zpskt/easy-crawler/daily_reports')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    today = datetime.now().strftime('%Y%m%d')
    summary_file = os.path.join(output_dir, f'daily_new_articles_{today}.json')
    analysis_file = os.path.join(output_dir, f'daily_analysis_{today}.json')
    analysis_html_file = os.path.join(output_dir, f'daily_analysis_{today}.html')
    
    # 1. 生成每日新文章及其对应地址文件
    new_articles_summary = []
    for article in articles:
        if 'error' in article:
            continue
        
        new_articles_summary.append({
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'publish_time': article.get('publish_time', '')
        })
    
    # 保存每日新文章摘要
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(new_articles_summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"每日新文章列表已保存到: {summary_file}")
    
    # 2. 保存分析结果JSON
    if analyses:
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析结果已保存到: {analysis_file}")
        
        # 生成HTML分析报告
        llm_analyzer = LLMAnalyzer(
            use_real_llm=True,
            ollama_url=LLM_CONFIG.get('ollama_url', 'http://localhost:11434/api/generate'),
            model=LLM_CONFIG.get('model', 'deepseek-r1:7b')
        )
        llm_analyzer.generate_analysis_report(analyses, analysis_html_file)
    
    return summary_file, analysis_file

def run_daily_task(api_config, urls=None, batch_size=None, delay=2):
    """运行每日爬取和API传输任务
    
    Args:
        api_config: API配置
        urls: 要爬取的URL列表
        batch_size: 批处理大小
        delay: 请求间隔
    
    Returns:
        dict: 任务结果
    """
    try:
        # 1. 爬取每日新文章
        articles = crawl_daily_articles(
            urls=urls,
            batch_size=batch_size,
            delay=delay
        )
        
        if not articles:
            logger.info("没有新文章，任务结束")
            return {'success': True, 'new_articles': 0}
        
        # 2. 过滤出成功爬取的文章
        valid_articles = [a for a in articles if 'error' not in a]
        if not valid_articles:
            logger.warning("所有文章爬取失败，任务结束")
            return {'success': False, 'error': '所有文章爬取失败'}
        
        # 3. 保存到文件（本地备份）
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        output_file = f"cheaa_daily_crawl_{timestamp}.json"
        output_dir = OUTPUT_PATHS.get('outdir', '/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir')
        output_file_path = os.path.join(output_dir, output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        persistence_manager = setup_faiss()
        persistence_manager.save_with_method('json', valid_articles, output_file_path)
        logger.info(f"成功保存到本地文件: {output_file_path}")
        
        # 4. 保存到FAISS向量数据库（如果可用）
        if 'faiss' in persistence_manager.persistence_methods:
            persistence_manager.save_with_method('faiss', valid_articles)
            logger.info("成功保存到FAISS向量数据库")
        else:
            logger.warning("FAISS持久化不可用，跳过向量数据库保存")
        
        # 5. 通过API传输数据
        api_success_count = 0
        if api_config and api_config.get('url'):
            logger.info(f"开始通过API传输数据，共 {len(valid_articles)} 篇文章")
            
            # 构建传输数据格式
            api_data = {
                'crawl_time': datetime.now().isoformat(),
                'total_articles': len(valid_articles),
                'articles': valid_articles
            }
            
            # 调用API传输数据
            if save_to_api(api_data, api_config):
                api_success_count = len(valid_articles)
                logger.info(f"成功通过API传输 {api_success_count} 篇文章")
            else:
                logger.error("API传输失败")
        else:
            logger.warning("未配置API，跳过数据传输")
        
        # 6. 分析文章（可选功能）
        analyses = analyze_articles(valid_articles)
        
        # 7. 生成每日输出文件
        summary_file, analysis_file = generate_daily_files(valid_articles, analyses)
        
        logger.info("每日爬取和API传输任务完成！")
        return {
            'success': True,
            'total_articles': len(valid_articles),
            'new_articles': len(valid_articles),  # 所有爬取的文章都视为新文章
            'api_success_count': api_success_count,
            'summary_file': summary_file,
            'analysis_file': analysis_file
        }
    except Exception as e:
        logger.error(f"每日任务执行失败: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """主函数"""
    config = CRAWLER_PAGE_CONFIG
    api_config = API_CONFIG

    
    # API是可选项，不强制要求配置
    if not api_config.get('url'):
        print("信息: 未配置API URL，将不会进行数据传输")
    
    # 运行每日任务
    result = run_daily_task(
        api_config=api_config,
        urls=config.get('urls', []),
        batch_size=config.get('batch_size', 100),
        delay=config.get('delay', 2)
    )
    
    # 输出结果
    if result['success']:
        print(f"任务成功完成！")
        print(f"总文章数: {result.get('total_articles', 0)}")
        print(f"新文章数: {result.get('new_articles', 0)}")
        print(f"成功传输到API的文章数: {result.get('api_success_count', 0)}")
        if 'summary_file' in result and result['summary_file']:
            print(f"每日新文章列表已保存到: {result['summary_file']}")
        if 'analysis_file' in result and result['analysis_file']:
            print(f"分析结果已保存到: {result['analysis_file']}")
    else:
        print(f"任务执行失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
