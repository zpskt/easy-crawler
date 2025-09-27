#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/25 21:59
# @Author  : zhangpeng /zpskt
# @File    : config.py
# @Software: PyCharm
# config.py - 网站特定配置
from urllib.parse import urlparse

# 网站特定配置
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

# 中国家电网频道和模块配置
CHEAA_CHANNELS = {
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

def get_site_config(url):
    """根据URL获取网站特定配置"""
    domain = urlparse(url).netloc
    for site_domain, config in SITE_CONFIGS.items():
        if site_domain in domain:
            return config
    return {}