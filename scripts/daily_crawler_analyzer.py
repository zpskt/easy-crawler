#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/2 10:00
# @Author  : zhangpeng /zpskt
# @File    : daily_crawler_analyzer.py
# @Software: PyCharm
# 每日爬取和分析系统 - 自动爬取中国家电网数据并通过API传输

import argparse
import json
import time
import os
import logging
from datetime import datetime, timedelta
from tqdm import tqdm
import sys
import requests

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需模块
from src.business.cheaa_crawler import CheaaChannelCrawler
from src.core.crawler import UniversalWebExtractor
from src.storage.data_persistence import get_default_manager
from src.llm_analysis.llm_analyzer import LLMAnalyzer

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

class DailyCrawlerAnalyzer:
    """每日爬取和API传输系统"""
    
    def __init__(self, api_config):
        """初始化系统
        
        Args:
            api_config: API接口配置字典，包含url、api_key、timeout、retry_count、retry_delay等
                      (API是可选项，如果不配置url，则不会进行数据传输)
        """
        # 初始化爬虫
        self.channel_crawler = CheaaChannelCrawler()
        self.web_extractor = UniversalWebExtractor(use_selenium=False)
        
        # 初始化持久化管理器
        self.persistence_manager = get_default_manager()
        
        # 尝试导入并注册FAISS持久化（可选）
        self._setup_faiss()
        
        # 初始化LLM分析器
        self.llm_analyzer = LLMAnalyzer(
            use_real_llm=True,
            model="deepseek-r1:7b"
        )
        
        # 初始化API配置
        self.api_config = api_config or {}
        # 设置默认值
        self.api_config.setdefault('timeout', 30)
        self.api_config.setdefault('retry_count', 3)
        self.api_config.setdefault('retry_delay', 5)
        
        logger.info(f"系统初始化完成，API配置: URL={self.api_config.get('url')[:30]}...")
    
    def _setup_faiss(self):
        """设置FAISS向量数据库（可选功能）"""
        try:
            from src.storage.vector_db import FAISSPersistence
            if 'faiss' not in self.persistence_manager.persistence_methods:
                self.persistence_manager.register_persistence('faiss', FAISSPersistence())
                logger.info("成功注册FAISS持久化")
        except Exception as e:
            logger.error(f"注册FAISS持久化失败: {e}")
    
    def _is_article_new(self, url):
        """检查文章是否已经爬取过（使用本地文件跟踪）
        
        Args:
            url: 文章URL
        
        Returns:
            bool: 是否为新文章
        """
        # 在实际应用中，可以使用本地文件或其他方式来跟踪已爬取的文章
        # 这里简单返回True，表示所有文章都视为新文章
        return True
    
    def _save_to_api(self, data):
        """通过API传输数据，支持重试逻辑
        
        Args:
            data: 要传输的数据
        
        Returns:
            bool: 是否传输成功
        """
        if not self.api_config or not self.api_config.get('url'):
            logger.error("未配置API URL，跳过API传输")
            return False
        
        retry_count = self.api_config.get('retry_count', 3)
        retry_delay = self.api_config.get('retry_delay', 5)
        timeout = self.api_config.get('timeout', 30)
        
        for attempt in range(retry_count):
            try:
                logger.info(f"尝试通过API传输数据到: {self.api_config.get('url')} (尝试 {attempt+1}/{retry_count})")
                headers = {'Content-Type': 'application/json'}
                if 'api_key' in self.api_config:
                    headers['Authorization'] = f"Bearer {self.api_config.get('api_key')}"
                
                response = requests.post(
                    self.api_config.get('url'),
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
    

    
    def crawl_daily_articles(self, channel_keys=None, module_keys=None, batch_size=None, delay=2):
        """爬取每日新文章
        
        Args:
            channel_keys: 要爬取的频道列表
            module_keys: 要爬取的模块列表
            batch_size: 批处理大小
            delay: 请求间隔
        
        Returns:
            list: 新文章列表
        """
        logger.info(f"开始爬取每日新文章: 频道={channel_keys}, 模块={module_keys}")
        
        # 获取文章URL列表
        article_urls = self.channel_crawler.get_article_urls_and_titles(
            channel_keys=channel_keys,
            module_keys=module_keys
        )
        
        logger.info(f"获取到 {len(article_urls)} 个文章URL")
        
        # 过滤出新文章
        new_article_urls = []
        for article in article_urls:
            if self._is_article_new(article['url']):
                new_article_urls.append(article)
                # 如果达到批量大小，停止过滤
                if batch_size and len(new_article_urls) >= batch_size:
                    break
        
        logger.info(f"筛选出 {len(new_article_urls)} 篇新文章")
        
        # 爬取文章详细内容
        if not new_article_urls:
            logger.info("没有新文章需要爬取")
            return []
        
        results = []
        for idx, article in enumerate(tqdm(new_article_urls, desc="爬取文章详情")):
            logger.info(f"正在爬取文章 {idx+1}/{len(new_article_urls)}: {article['title']}")
            
            try:
                # 爬取文章详细内容
                result = self.web_extractor.smart_extract(article['url'])
                
                # 合并文章信息
                result.update({
                    'channel': article.get('channel'),
                    'channel_name': article.get('channel_name'),
                    'module': article.get('module'),
                    'module_name': article.get('module_name'),
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
        self.web_extractor.close()
        
        return results
    
    def analyze_articles(self, articles):
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
        
        # 批量分析文章
        results = self.llm_analyzer.batch_analyze(valid_articles)
        
        # 合并文章ID到分析结果中
        for i, result in enumerate(results):
            if i < len(valid_articles) and 'id' in valid_articles[i]:
                result['id'] = valid_articles[i]['id']
                result['title'] = valid_articles[i].get('title', '')
                result['url'] = valid_articles[i].get('url', '')
                result['publish_time'] = valid_articles[i].get('publish_time', '')
        
        logger.info("文章分析完成")
        
        return results
    
    def generate_daily_files(self, articles, analyses, output_dir=None):
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
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'daily_reports')
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
                'publish_time': article.get('publish_time', ''),
                'channel': article.get('channel_name', article.get('channel', '')),
                'module': article.get('module_name', article.get('module', ''))
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
            self.llm_analyzer.generate_analysis_report(analyses, analysis_html_file)
        
        return summary_file, analysis_file
    
    def run_daily_task(self, channel_keys=None, module_keys=None, batch_size=None, delay=2):
        """运行每日爬取和API传输任务
        
        Args:
            channel_keys: 要爬取的频道列表
            module_keys: 要爬取的模块列表
            batch_size: 批处理大小
            delay: 请求间隔
        
        Returns:
            dict: 任务结果
        """
        try:
            # 1. 爬取每日新文章
            articles = self.crawl_daily_articles(
                channel_keys=channel_keys,
                module_keys=module_keys,
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
            self.persistence_manager.save_with_method('json', valid_articles, output_file)
            logger.info(f"成功保存到本地文件: {output_file}")
            
            # 4. 保存到FAISS向量数据库（如果可用）
            if 'faiss' in self.persistence_manager.persistence_methods:
                self.persistence_manager.save_with_method('faiss', valid_articles)
                logger.info("成功保存到FAISS向量数据库")
            else:
                logger.warning("FAISS持久化不可用，跳过向量数据库保存")
            
            # 5. 通过API传输数据
            api_success_count = 0
            if self.api_config and self.api_config.get('url'):
                logger.info(f"开始通过API传输数据，共 {len(valid_articles)} 篇文章")
                
                # 构建传输数据格式
                api_data = {
                    'crawl_time': datetime.now().isoformat(),
                    'total_articles': len(valid_articles),
                    'articles': valid_articles
                }
                
                # 调用API传输数据
                if self._save_to_api(api_data):
                    api_success_count = len(valid_articles)
                    logger.info(f"成功通过API传输 {api_success_count} 篇文章")
                else:
                    logger.error("API传输失败")
            else:
                logger.warning("未配置API，跳过数据传输")
            
            # 6. 分析文章（可选功能）
            analyses = []
            if hasattr(self, 'llm_analyzer'):
                analyses = self.analyze_articles(valid_articles)
            
            # 7. 生成每日输出文件
            summary_file, analysis_file = self.generate_daily_files(valid_articles, analyses)
            
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


def load_config_from_file(config_path=None):
    """从配置文件加载API配置（API是可选项）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        dict: API配置字典
    """
    if not config_path:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'src', 'config', 'api_config.json'
        )
    
    if not os.path.exists(config_path):
        logger.warning(f"配置文件不存在: {config_path}")
        return {'url': '', 'api_key': '', 'timeout': 30, 'retry_count': 3, 'retry_delay': 5}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 提取API配置
        api_config = {
            'url': config.get('api', {}).get('url', ''),
            'api_key': config.get('api', {}).get('api_key', ''),
            'timeout': config.get('api', {}).get('timeout', 30),
            'retry_count': config.get('api', {}).get('retry_count', 3),
            'retry_delay': config.get('api', {}).get('retry_delay', 5)
        }
        
        logger.info(f"成功从配置文件加载API配置: {config_path}")
        return api_config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {'url': '', 'api_key': '', 'timeout': 30, 'retry_count': 3, 'retry_delay': 5}

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='中国家电网每日爬取和API传输系统')
    
    # 爬虫参数
    parser.add_argument('--channels', '-c', nargs='+', default=['icebox'],
                      help='频道标识列表，例如: icebox ac')
    parser.add_argument('--modules', '-m', nargs='+', default=['xinpin'],
                      help='模块标识列表，例如: xinpin hangqing')
    parser.add_argument('--batch-size', '-b', type=int, help='批处理大小，只处理指定数量的文章')
    parser.add_argument('--delay', '-d', type=int, default=2, help='两次请求之间的延迟（秒），默认为2秒')
    
    # 配置文件参数
    parser.add_argument('--config', '-C', help='配置文件路径')
    
    # API配置参数（会覆盖配置文件中的设置，所有API参数都是可选的）
    parser.add_argument('--api-url', help='API接口URL（可选，不配置则不进行数据传输）')
    parser.add_argument('--api-key', help='API密钥（可选）')
    parser.add_argument('--api-timeout', type=int, help='API请求超时时间（秒，可选）')
    parser.add_argument('--api-retry-count', type=int, help='API请求重试次数（可选）')
    parser.add_argument('--api-retry-delay', type=int, help='API请求重试间隔（秒，可选）')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 从配置文件加载API配置
    api_config = load_config_from_file(args.config)
    
    # 使用命令行参数覆盖配置文件设置
    if args.api_url:
        api_config['url'] = args.api_url
    if args.api_key:
        api_config['api_key'] = args.api_key
    if args.api_timeout:
        api_config['timeout'] = args.api_timeout
    if args.api_retry_count:
        api_config['retry_count'] = args.api_retry_count
    if args.api_retry_delay:
        api_config['retry_delay'] = args.api_retry_delay
    
    # API是可选项，不强制要求配置
    if not api_config.get('url'):
        print("信息: 未配置API URL，将不会进行数据传输")
    
    # 创建系统实例
    daily_system = DailyCrawlerAnalyzer(api_config)
    
    # 运行每日任务
    result = daily_system.run_daily_task(
        channel_keys=args.channels,
        module_keys=args.modules,
        batch_size=args.batch_size,
        delay=args.delay
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
    # 示例用法：
    # python scripts/daily_crawler_analyzer.py --channels icebox --modules xinpin --api-url https://api.example.com/data --api-key your_api_key
    # python scripts/daily_crawler_analyzer.py --channels icebox ac --modules xinpin hangqing --api-url https://api.example.com/data --api-key your_api_key --api-timeout 60 --api-retry-count 5