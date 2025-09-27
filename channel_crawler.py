#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/1 10:00
# @Author  : zhangpeng /zpskt
# @File    : channel_crawler.py
# @Software: PyCharm
# 中国家电网频道和模块爬虫 - 灵活选择目标爬取模块网址

import argparse
import json
from crawler import UniversalWebExtractor
from data_persistence import get_default_manager
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class CheaaChannelCrawler:
    """中国家电网频道爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        # 定义中国家电网的频道和模块
        self.channel_modules = {
            'icebox': {
                'name': '冰箱频道',
                'base_url': 'https://icebox.cheaa.com/',
                'modules': {
                    'xinpin': {'name': '新品速递', 'url': 'xinpin.shtml'},
                    'hangqing': {'name': '行业瞭望', 'url': 'hangqing.shtml'},
                    'pinpai': {'name': '品牌观察', 'url': 'pinpai.shtml'},
                    'pingce': {'name': '产品评测', 'url': 'pingce.shtml'},
                    'xuangou': {'name': '选购指南', 'url': 'xuangou.shtml'}
                }
            },
            'ac': {
                'name': '空调频道',
                'base_url': 'https://ac.cheaa.com/',
                'modules': {
                    'xinpin': {'name': '新品速递', 'url': 'xinpin.shtml'},
                    'hangqing': {'name': '行业瞭望', 'url': 'hangqing.shtml'},
                    'pinpai': {'name': '品牌观察', 'url': 'pinpai.shtml'},
                    'pingce': {'name': '产品评测', 'url': 'pingce.shtml'},
                    'xuangou': {'name': '选购指南', 'url': 'xuangou.shtml'}
                }
            },
            'tv': {
                'name': '电视影音',
                'base_url': 'https://digitalhome.cheaa.com/',
                'modules': {
                    'xinpin': {'name': '新品速递', 'url': 'xinpin.shtml'},
                    'hangqing': {'name': '行业瞭望', 'url': 'hangqing.shtml'},
                    'pinpai': {'name': '品牌观察', 'url': 'pinpai.shtml'},
                    'pingce': {'name': '产品评测', 'url': 'pingce.shtml'},
                    'xuangou': {'name': '选购指南', 'url': 'xuangou.shtml'}
                }
            },
            'washing': {
                'name': '洗衣机频道',
                'base_url': 'https://washer.cheaa.com/',
                'modules': {
                    'xinpin': {'name': '新品速递', 'url': 'xinpin.shtml'},
                    'hangqing': {'name': '行业瞭望', 'url': 'hangqing.shtml'},
                    'pinpai': {'name': '品牌观察', 'url': 'pinpai.shtml'},
                    'pingce': {'name': '产品评测', 'url': 'pingce.shtml'},
                    'xuangou': {'name': '选购指南', 'url': 'xuangou.shtml'}
                }
            }
        }
        
        self.persistence_manager = get_default_manager()
        
    def list_channels(self):
        """列出所有可用的频道"""
        print("可用频道列表:")
        for channel_key, channel_info in self.channel_modules.items():
            print(f"- {channel_key}: {channel_info['name']}")
        
    def list_modules(self, channel_key):
        """列出指定频道的所有模块"""
        if channel_key not in self.channel_modules:
            print(f"未找到频道: {channel_key}")
            return False
        
        print(f"{self.channel_modules[channel_key]['name']} 的模块列表:")
        for module_key, module_info in self.channel_modules[channel_key]['modules'].items():
            print(f"- {module_key}: {module_info['name']}")
        return True
        
    def generate_module_urls(self, channel_keys=None, module_keys=None):
        """生成指定频道和模块的URL列表"""
        urls = []
        
        # 如果没有指定频道，使用所有频道
        if not channel_keys:
            channel_keys = list(self.channel_modules.keys())
        
        # 确保channel_keys是列表
        if isinstance(channel_keys, str):
            channel_keys = [channel_keys]
        
        for channel_key in channel_keys:
            if channel_key not in self.channel_modules:
                print(f"警告: 未找到频道 '{channel_key}'，已跳过")
                continue
            
            channel_info = self.channel_modules[channel_key]
            
            # 如果没有指定模块，使用当前频道的所有模块
            if not module_keys:
                current_module_keys = list(channel_info['modules'].keys())
            else:
                # 确保module_keys是列表
                if isinstance(module_keys, str):
                    current_module_keys = [module_keys]
                else:
                    current_module_keys = module_keys
            
            for module_key in current_module_keys:
                if module_key not in channel_info['modules']:
                    print(f"警告: 在频道 '{channel_key}' 中未找到模块 '{module_key}'，已跳过")
                    continue
                
                module_info = channel_info['modules'][module_key]
                full_url = f"{channel_info['base_url']}{module_info['url']}"
                urls.append({
                    'url': full_url,
                    'channel': channel_key,
                    'channel_name': channel_info['name'],
                    'module': module_key,
                    'module_name': module_info['name']
                })
        
        return urls
        
    def extract_article_links(self, html, base_url):
        """从中国家电网频道页面提取文章列表链接"""
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
                        full_url = urljoin(base_url, href)
                        
                        # 确保是文章详情页链接
                        if '/20' in href and (href.endswith('.shtml') or href.endswith('.html')):
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
        
    def crawl_module(self, url_info, use_selenium=False):
        """爬取单个模块页面"""
        try:
            extractor = UniversalWebExtractor(use_selenium=use_selenium)
            
            # 获取页面HTML（直接调用底层方法获取原始HTML）
            if use_selenium:
                html = extractor.get_content_with_selenium(url_info['url'])
            else:
                html = extractor.get_content_with_requests(url_info['url'])
            
            # 提取文章列表链接
            article_links = self.extract_article_links(html, url_info['url'])
            
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
            result = extractor.smart_extract(url_info['url'])
            extractor.close()
            
            # 添加频道和模块信息
            result['channel'] = url_info['channel']
            result['channel_name'] = url_info['channel_name']
            result['module'] = url_info['module']
            result['module_name'] = url_info['module_name']
            
            # 添加文章列表链接
            result['article_links'] = article_links
            result['article_count'] = len(article_links)
            
            return result
        except Exception as e:
            return {
                'url': url_info['url'],
                'channel': url_info['channel'],
                'channel_name': url_info['channel_name'],
                'module': url_info['module'],
                'module_name': url_info['module_name'],
                'error': str(e),
                'article_links': [],
                'article_count': 0
            }
            
    def batch_crawl(self, channel_keys=None, module_keys=None, use_selenium=False, output_file=None):
        """批量爬取指定的频道和模块"""
        # 生成URL列表
        url_infos = self.generate_module_urls(channel_keys, module_keys)
        
        if not url_infos:
            print("没有找到有效的URL，爬取任务取消")
            return []
        
        print(f"开始爬取 {len(url_infos)} 个模块页面...")
        
        # 开始爬取
        results = []
        for url_info in tqdm(url_infos, desc="爬取进度"):
            print(f"正在爬取: {url_info['channel_name']} - {url_info['module_name']} ({url_info['url']})")
            result = self.crawl_module(url_info, use_selenium)
            results.append(result)
        
        # 保存结果
        if output_file:
            self.persistence_manager.save_with_method('json', results, output_file)
        else:
            # 默认文件名
            channel_str = '_'.join(channel_keys) if channel_keys else 'all_channels'
            module_str = '_'.join(module_keys) if module_keys else 'all_modules'
            default_output = f"cheaa_crawl_{channel_str}_{module_str}.json"
            self.persistence_manager.save_with_method('json', results, default_output)
        
        # 生成HTML报告
        self.persistence_manager.save_with_method('html_report', results)
        
        return results


# 命令行接口

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='中国家电网频道和模块爬虫')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list-channels 命令
    list_channels_parser = subparsers.add_parser('list-channels', help='列出所有可用频道')
    
    # list-modules 命令
    list_modules_parser = subparsers.add_parser('list-modules', help='列出指定频道的模块')
    list_modules_parser.add_argument('channel', help='频道标识')
    
    # generate-urls 命令
    generate_urls_parser = subparsers.add_parser('generate-urls', help='生成指定频道和模块的URL')
    generate_urls_parser.add_argument('--channels', '-c', nargs='+', help='频道标识列表')
    generate_urls_parser.add_argument('--modules', '-m', nargs='+', help='模块标识列表')
    generate_urls_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取指定频道和模块的内容')
    crawl_parser.add_argument('--channels', '-c', nargs='+', help='频道标识列表')
    crawl_parser.add_argument('--modules', '-m', nargs='+', help='模块标识列表')
    crawl_parser.add_argument('--use-selenium', '-s', action='store_true', help='使用Selenium进行爬取')
    crawl_parser.add_argument('--output', '-o', help='输出文件路径')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    crawler = CheaaChannelCrawler()
    
    if args.command == 'list-channels':
        # 列出所有频道
        crawler.list_channels()
        
    elif args.command == 'list-modules':
        # 列出指定频道的模块
        crawler.list_modules(args.channel)
        
    elif args.command == 'generate-urls':
        # 生成URL列表
        url_infos = crawler.generate_module_urls(args.channels, args.modules)
        urls = [info['url'] for info in url_infos]
        
        print(f"生成了 {len(urls)} 个URL:")
        for url in urls:
            print(url)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(urls, f, ensure_ascii=False, indent=2)
            print(f"URL列表已保存到: {args.output}")
            
    elif args.command == 'crawl':
        # 执行爬取
        crawler.batch_crawl(args.channels, args.modules, args.use_selenium, args.output)
        
    else:
        # 显示帮助信息
        print("请指定命令，使用 --help 查看可用命令")


if __name__ == "__main__":
    main()