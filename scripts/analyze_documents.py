#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档分析脚本 - 用于分析爬取的文档并生成报告
"""
import os
import sys
import argparse
from src.llm_analysis.llm_report_generator import LLMReportGenerator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文档分析工具 - 使用LLM分析爬取的文档并生成报告')
    parser.add_argument('input_files', nargs='*', default=['/Users/zhangpeng/Desktop/zpskt/easy-crawler/icebox_xinpin_result.json'], help='输入的JSON文件路径，默认使用当前目录下的icebox_xinpin_result.json文件')
    parser.add_argument('--output-dir', '-o', default='reports', help='输出报告目录')
    parser.add_argument('--no-json', action='store_true', help='不生成JSON结果文件')
    parser.add_argument('--no-html', action='store_true', help='不生成HTML报告')
    
    args = parser.parse_args()
    
    # 处理默认的JSON文件
    import glob
    input_files = []
    if not args.input_files:
        # 当没有提供参数时，使用默认的icebox_xinpin_result.json文件
        input_files = ['icebox_xinpin_result.json']
        print(f"未指定输入文件，将使用默认文件: {input_files[0]}")
    else:
        # 展开可能包含通配符的文件路径
        for file_pattern in args.input_files:
            input_files.extend(glob.glob(file_pattern))
    
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
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 创建报告生成器并生成报告
    generator = LLMReportGenerator()
    summary = generator.analyze_and_generate_report(
        valid_files,
        args.output_dir,
        generate_json=not args.no_json,
        generate_html=not args.no_html
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