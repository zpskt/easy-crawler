#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/25 21:59
# @Author  : zhangpeng /zpskt
# @File    : batch_processor.py
# @Software: PyCharm
# batch_processor.py
import pandas as pd
from crawler import UniversalWebExtractor
import json
from tqdm import tqdm


def generate_report(results, output_file):
    """生成提取结果统计报告"""
    # 计算统计数据
    total = len(results)
    successful = sum(1 for r in results if 'error' not in r)
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # 计算平均内容长度和图片数量
    if successful > 0:
        avg_content_length = sum(r.get('content_length', 0) for r in results if 'error' not in r) / successful
        avg_image_count = sum(r.get('image_count', 0) for r in results if 'error' not in r) / successful
    else:
        avg_content_length = 0
        avg_image_count = 0
    
    # 提取方法统计
    source_stats = {}
    for r in results:
        if 'error' not in r and 'source' in r:
            source = r['source']
            source_stats[source] = source_stats.get(source, 0) + 1
    
    # 创建HTML报告
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>网页内容提取报告</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 2.5em;
                font-weight: bold;
                color: #3498db;
                margin-bottom: 10px;
            }}
            .stat-label {{
                color: #7f8c8d;
                font-size: 1.1em;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .success {{ color: #27ae60; }}
            .error {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>网页内容提取报告</h1>
        
        <div class="summary">
            <h2>总体统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">总URL数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value success">{successful}</div>
                    <div class="stat-label">成功提取</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value error">{failed}</div>
                    <div class="stat-label">提取失败</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{success_rate:.1f}%</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <h2>内容统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{avg_content_length:.0f}</div>
                    <div class="stat-label">平均内容长度</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_image_count:.1f}</div>
                    <div class="stat-label">平均图片数量</div>
                </div>
            </div>
        </div>
        
        <h2>提取方法统计</h2>
        <table>
            <tr>
                <th>提取方法</th>
                <th>使用次数</th>
                <th>占比</th>
            </tr>
    """
    
    # 添加提取方法统计行
    for source, count in source_stats.items():
        percentage = (count / successful * 100) if successful > 0 else 0
        html_content += f"""
            <tr>
                <td>{source}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
        """
    
    # 添加详细结果表格
    html_content += f"""
        </table>
        
        <h2>详细结果</h2>
        <table>
            <tr>
                <th>URL</th>
                <th>状态</th>
                <th>标题</th>
                <th>内容长度</th>
                <th>图片数量</th>
                <th>提取方法</th>
            </tr>
    """
    
    # 添加详细结果行
    for result in results:
        url = result.get('url', '')
        status = '成功' if 'error' not in result else '失败'
        status_class = 'success' if 'error' not in result else 'error'
        title = result.get('title', '')[:50] + '...' if len(result.get('title', '')) > 50 else result.get('title', '')
        content_length = result.get('content_length', 0)
        image_count = result.get('image_count', 0)
        source = result.get('source', '')
        error_msg = result.get('error', '')
        
        html_content += f"""
            <tr>
                <td>{url}</td>
                <td class="{status_class}">{status}</td>
                <td>{title}</td>
                <td>{content_length}</td>
                <td>{image_count}</td>
                <td>{source}</td>
            </tr>
        """
    
    # 结束HTML内容
    html_content += f"""
        </table>
    
        <footer>
            <p style="text-align: center; color: #7f8c8d; margin-top: 50px;">报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </body>
    </html>
    """
    
    # 保存HTML报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"统计报告已保存到: {output_file}")


def batch_process_urls(urls_file, output_file, use_selenium=False):
    """批量处理URL列表"""

    # 读取URL列表
    df = pd.read_csv(urls_file) if urls_file.endswith('.csv') else pd.read_excel(urls_file)
    urls = df['url'].tolist()

    extractor = UniversalWebExtractor(use_selenium=use_selenium)
    results = []

    for url in tqdm(urls, desc="处理进度"):
        try:
            result = extractor.smart_extract(url)
            results.append(result)
        except Exception as e:
            results.append({'url': url, 'error': str(e)})

    extractor.close()

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 生成统计报告
    generate_report(results, 'extraction_report.html')


# 使用示例
if __name__ == "__main__":
    batch_process_urls('urls.csv', 'extraction_results.json', use_selenium=False)