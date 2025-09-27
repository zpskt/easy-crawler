#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM报告生成器 - 用于生成LLM分析报告
"""
import json
import os
import logging
import datetime
from typing import List, Dict
from src.llm_analysis.llm_analyzer import LLMAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMReportGenerator:
    """LLM报告生成器类"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.analyzer = LLMAnalyzer()
        
    def analyze_and_generate_report(self, input_files: List[str], output_dir: str = '.', 
                                   generate_json: bool = True, generate_html: bool = True) -> Dict:
        """分析多个文件并生成报告
        
        Args:
            input_files: 输入文件列表
            output_dir: 输出目录
            generate_json: 是否生成JSON结果文件
            generate_html: 是否生成HTML报告
        
        Returns:
            包含所有分析结果的字典
        """
        all_documents = []
        all_results = []
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载并分析所有文件
        for file_path in input_files:
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                continue
            
            # 加载文档
            documents = self.analyzer.load_documents_from_json(file_path)
            if not documents:
                logger.warning(f"未能从文件加载有效文档: {file_path}")
                continue
            
            all_documents.extend(documents)
            
            # 分析文档
            results = self.analyzer.batch_analyze(documents)
            all_results.extend(results)
            
            # 为每个文件生成单独的报告
            file_name = os.path.basename(file_path).split('.')[0]
            
            if generate_json:
                json_output = os.path.join(output_dir, f'{file_name}_analysis.json')
                self.analyzer.save_analysis_results(results, json_output)
            
            if generate_html:
                html_output = os.path.join(output_dir, f'{file_name}_analysis.html')
                self.analyzer.generate_analysis_report(results, html_output)
        
        # 生成合并后的报告
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        summary = {
            'total_files': len(input_files),
            'total_documents': len(all_documents),
            'total_results': len(all_results),
            'success_count': sum(1 for r in all_results if 'error' not in r),
            'error_count': sum(1 for r in all_results if 'error' in r),
            'reports': []
        }
        
        # 保存合并后的结果
        if all_results:
            if generate_json:
                merged_json = os.path.join(output_dir, f'all_analysis_{timestamp}.json')
                self.analyzer.save_analysis_results(all_results, merged_json)
                summary['reports'].append(merged_json)
            
            if generate_html:
                merged_html = os.path.join(output_dir, f'all_analysis_{timestamp}.html')
                self.analyzer.generate_analysis_report(all_results, merged_html)
                summary['reports'].append(merged_html)
        
        return summary

# 使用示例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_files = sys.argv[1:]
        output_dir = '../..'
        
        # 检查最后一个参数是否为目录
        if os.path.isdir(input_files[-1]):
            output_dir = input_files.pop()
        
        generator = LLMReportGenerator()
        summary = generator.analyze_and_generate_report(input_files, output_dir)
        
        print(f"\n=== 分析摘要 ===")
        print(f"处理文件数: {summary['total_files']}")
        print(f"总文档数: {summary['total_documents']}")
        print(f"成功分析: {summary['success_count']}")
        print(f"分析失败: {summary['error_count']}")
        print(f"\n生成的报告:")
        for report in summary['reports']:
            print(f"- {report}")
    else:
        print("用法: python llm_report_generator.py <输入JSON文件1> [输入JSON文件2] ... [输出目录]")