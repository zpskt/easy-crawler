#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/25 21:59
# @Author  : zhangpeng /zpskt
# @File    : config.py
# @Software: PyCharm
# config.py - 网站特定配置
from urllib.parse import urlparse

SITE_CONFIGS = {
    'weibo.com': {
        'use_selenium': True,
        'wait_time': 5,
        'content_selectors': ['.weibo-text']  # 备用选择器
    },
    'cheaa.com': {
        'use_selenium': False,
        'content_selectors': ['.content', '.article-content']
    }
}

def get_site_config(url):
    """根据URL获取网站特定配置"""
    domain = urlparse(url).netloc
    for site_domain, config in SITE_CONFIGS.items():
        if site_domain in domain:
            return config
    return {}