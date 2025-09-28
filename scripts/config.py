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
    'use_vector_db': False
}
# 单个网页提取设置
SINGLE_PAGE_CONFIG = {
    'output_file': '/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir/',
}
