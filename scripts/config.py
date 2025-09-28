#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/25 21:59
# @Author  : zhangpeng /zpskt
# @File    : config.py
# @Software: PyCharm
# config.py - 网站特定配置

# 爬取网站配置
CRAWLER_PAGE_CONFIG = {
    'urls': ['https://icebox.cheaa.com/xinpin.shtml'],
    'use_selenium': False,
    'extract_articles': True,
    'output_file': '/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir/articles.json',
    'use_vector_db': False,
    'batch_size': 100,
    'delay': 2
}
# 单个网页提取设置
SINGLE_PAGE_CONFIG = {
    'output_file': '/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir/',
}
# 调用外部api的接口配置
API_CONFIG = {
    'url': '',
    'api_key': '',
    'timeout': 30,
    'retry_count': 3,
    'retry_delay': 5
}

# 输出目录配置
OUTPUT_PATHS = {
    'daily_reports': '/Users/zhangpeng/Desktop/zpskt/easy-crawler/daily_reports',
    'outdir': '/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir'
}

# LLM配置
LLM_CONFIG = {
    'ollama_url': 'http://localhost:11434/api/generate',
    'model': 'deepseek-r1:7b'
}