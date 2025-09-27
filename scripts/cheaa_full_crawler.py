#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/1 10:00
# @Author  : zhangpeng /zpskt
# @File    : cheaa_full_crawler.py
# @Software: PyCharm
# 中国家电网完整爬虫 - 先获取文章链接，再爬取详细内容

import argparse
import json
import time
from tqdm import tqdm
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 然后再导入其他模块
from src.business.cheaa_crawler import CheaaChannelCrawler
from src.core.crawler import UniversalWebExtractor
from src.storage.data_persistence import get_default_manager

class CheaaFullCrawler:
    """中国家电网完整爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        self.channel_crawler = CheaaChannelCrawler()
        self.persistence_manager = get_default_manager()
        self.article_urls = []
        
    def get_article_urls(self, channel_keys=None, module_keys=None, use_selenium=False):
        """获取文章URL列表"""
        self.article_urls = self.channel_crawler.get_article_urls_and_titles(
            channel_keys=channel_keys,
            module_keys=module_keys,
            use_selenium=use_selenium
        )
        return self.article_urls
        
    def crawl_article_details(self, use_selenium=False, batch_size=None, delay=2):
        """爬取文章详细内容
        
        Args:
            use_selenium: 是否使用Selenium
            batch_size: 批处理大小，None表示处理所有文章
            delay: 两次请求之间的延迟（秒）
            
        Returns:
            list: 包含所有文章详细内容的列表
        """
        if not self.article_urls:
            print("没有可爬取的文章URL，请先调用get_article_urls方法")
            return []
            
        # 如果指定了batch_size，则只处理指定数量的文章
        articles_to_process = self.article_urls[:batch_size] if batch_size else self.article_urls
        total_articles = len(articles_to_process)
        
        print(f"开始爬取 {total_articles} 篇文章的详细内容...")
        
        results = []
        extractor = UniversalWebExtractor(use_selenium=use_selenium)
        
        try:
            for idx, article in enumerate(tqdm(articles_to_process, desc="爬取文章详情")):
                print(f"正在爬取文章 {idx+1}/{total_articles}: {article['title']}")
                
                try:
                    # 使用UniversalWebExtractor爬取文章详细内容
                    result = extractor.smart_extract(article['url'])
                    
                    # 合并文章的基本信息
                    result.update({
                        'channel': article.get('channel'),
                        'channel_name': article.get('channel_name'),
                        'module': article.get('module'),
                        'module_name': article.get('module_name'),
                        'publish_time': article.get('publish_time') or result.get('publish_time')
                    })
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"爬取文章 {article['url']} 时出错: {e}")
                    results.append({
                        'url': article['url'],
                        'title': article['title'],
                        'error': str(e)
                    })
                
                # 避免请求过快
                if idx < total_articles - 1:
                    time.sleep(delay)
            
        finally:
            # 确保关闭提取器
            extractor.close()
        
        # 统计结果
        successful = sum(1 for r in results if 'error' not in r)
        failed = total_articles - successful
        
        print(f"\n爬取完成！")
        print(f"总文章数: {total_articles}")
        print(f"成功爬取: {successful}")
        print(f"爬取失败: {failed}")
        
        return results
        
    def run_full_crawl(self, channel_keys=None, module_keys=None, use_selenium=False, 
                      batch_size=None, delay=2, output_file=None):
        """运行完整的爬取流程
        
        Args:
            channel_keys: 要爬取的频道列表
            module_keys: 要爬取的模块列表
            use_selenium: 是否使用Selenium
            batch_size: 批处理大小，None表示处理所有文章
            delay: 两次请求之间的延迟（秒）
            output_file: 输出文件路径
            
        Returns:
            list: 包含所有文章详细内容的列表
        """
        # 1. 获取文章URL列表
        self.get_article_urls(channel_keys=channel_keys, module_keys=module_keys, use_selenium=use_selenium)
        
        # 2. 爬取文章详细内容
        results = self.crawl_article_details(use_selenium=use_selenium, batch_size=batch_size, delay=delay)
        
        # 3. 保存结果
        if output_file:
            # 保存JSON格式结果
            self.persistence_manager.save_with_method('json', results, output_file)
            
            # 生成HTML报告
            html_report_file = output_file.replace('.json', '_report.html')
            self.persistence_manager.save_with_method('html_report', results, html_report_file)
        else:
            # 使用默认文件名
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_output = f"cheaa_full_crawl_{timestamp}.json"
            self.persistence_manager.save_with_method('json', results, default_output)
            
            # 生成HTML报告
            html_report_file = default_output.replace('.json', '_report.html')
            self.persistence_manager.save_with_method('html_report', results, html_report_file)
        
        return results


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='中国家电网完整爬虫 - 先获取文章链接，再爬取详细内容')
    
    parser.add_argument('--channels', '-c', nargs='+', help='频道标识列表，例如: icebox ac')
    parser.add_argument('--modules', '-m', nargs='+', help='模块标识列表，例如: xinpin hangqing')
    parser.add_argument('--use-selenium', '-s', action='store_true', help='使用Selenium进行爬取')
    parser.add_argument('--batch-size', '-b', type=int, help='批处理大小，只处理指定数量的文章')
    parser.add_argument('--delay', '-d', type=int, default=2, help='两次请求之间的延迟（秒），默认为2秒')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 创建爬虫实例
    full_crawler = CheaaFullCrawler()
    
    # 运行完整爬取流程
    full_crawler.run_full_crawl(
        channel_keys=args.channels,
        module_keys=args.modules,
        use_selenium=args.use_selenium,
        batch_size=args.batch_size,
        delay=args.delay,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
    # python scripts/cheaa_full_crawler.py --channels icebox --modules xinpin --output icebox_xinpin_result.json