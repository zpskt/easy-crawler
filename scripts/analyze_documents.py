#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档分析脚本 - 用于分析爬取的文档并生成报告
"""
import os
import sys
import argparse

from scripts.config import OUTPUT_PATHS
from src.llm_analysis.llm_report_generator import LLMReportGenerator


def main():
    """主函数"""
    config = OUTPUT_PATHS
    # 处理默认的JSON文件
    input_files = ['/Users/zhangpeng/Desktop/zpskt/easy-crawler/outdir/cheaa_daily_crawl_20250928_224350.json']
    
    # 验证输入文件
    valid_files = []
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"警告: 文件不存在: {file_path}")
            continue
        if not file_path.endswith('.json'):
            print(f"警告: 不支持的文件格式，仅支持JSON: {file_path}")
            continue
        valid_files.append(file_path)
    
    if not valid_files:
        print("错误: 没有找到有效的JSON文件")
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs(config.get('outdir', 'reports'), exist_ok=True)
    
    # 创建报告生成器并生成报告
    generator = LLMReportGenerator()
    summary = generator.analyze_and_generate_report(
        valid_files,
        config.get('outdir', 'reports'),
        generate_json=True,
        generate_html=True
    )
    
    # 打印摘要信息
    print(f"\n=== 文档分析摘要 ===")
    print(f"处理文件数: {summary['total_files']}")
    print(f"总文档数: {summary['total_documents']}")
    print(f"成功分析: {summary['success_count']}")
    print(f"分析失败: {summary['error_count']}")
    print(f"\n生成的报告:")
    for report in summary['reports']:
        print(f"- {os.path.abspath(report)}")
    
    print(f"\n分析完成！所有报告已保存到: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()