#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM文档分析器 - 用于分析爬取的文档并生成简要报告
"""
import json
import os
import logging
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM文档分析器类"""
    
    def __init__(self):
        """初始化分析器"""
        # 这里可以初始化LLM API客户端
        # 例如OpenAI、Anthropic、百度文心一言等
        # 目前使用模拟分析，实际使用时需要替换为真实的LLM API调用
        self.use_real_llm = False
        
    def analyze_document(self, document: Dict) -> Dict:
        """分析单个文档并生成摘要
        
        Args:
            document: 包含文档内容的字典
        
        Returns:
            包含分析结果的字典
        """
        logger.info(f"分析文档: {document.get('title', '未命名文档')}")
        
        # 提取文档内容
        title = document.get('title', '')
        content = document.get('content', '')
        url = document.get('url', '')
        publish_time = document.get('publish_time', document.get('date', ''))
        
        # 生成分析结果
        analysis_result = {
            'title': title,
            'url': url,
            'publish_time': publish_time,
            'summary': '',
            'keywords': [],
            'sentiment': 'neutral',  # 中性
            'key_points': []
        }
        
        if not content:
            analysis_result['summary'] = '文档内容为空'
            return analysis_result
        
        # 模拟LLM分析结果（实际使用时替换为真实的API调用）
        if self.use_real_llm:
            # 这里应该调用实际的LLM API
            # 例如：
            # analysis_result = self._call_llm_api(content)
            pass
        else:
            # 模拟分析结果
            # 从内容提取前100个字符作为摘要
            if len(content) > 100:
                analysis_result['summary'] = content[:100] + '...'
            else:
                analysis_result['summary'] = content
            
            # 简单提取关键词（实际使用时应该使用更复杂的算法或LLM）
            # 这里仅作为示例
            common_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这']
            words = content[:500].split()  # 只取前500个字符进行分析
            keywords_count = {}
            
            for word in words:
                # 过滤掉短词和常见词
                if len(word) > 2 and word not in common_words:
                    keywords_count[word] = keywords_count.get(word, 0) + 1
            
            # 获取出现频率最高的5个词作为关键词
            sorted_keywords = sorted(keywords_count.items(), key=lambda x: x[1], reverse=True)
            analysis_result['keywords'] = [kw for kw, _ in sorted_keywords[:5]]
            
            # 简单提取关键点
            lines = content.split('\n')
            key_points = []
            for line in lines[:5]:  # 只取前5行
                if line.strip() and len(line.strip()) > 20:
                    key_points.append(line.strip())
            analysis_result['key_points'] = key_points
        
        return analysis_result
    
    def batch_analyze(self, documents: List[Dict]) -> List[Dict]:
        """批量分析文档
        
        Args:
            documents: 文档列表
        
        Returns:
            分析结果列表
        """
        logger.info(f"开始批量分析 {len(documents)} 个文档")
        results = []
        
        for doc in documents:
            try:
                result = self.analyze_document(doc)
                results.append(result)
            except Exception as e:
                logger.error(f"分析文档失败: {e}")
                # 记录错误但继续处理其他文档
                results.append({
                    'title': doc.get('title', '未命名文档'),
                    'url': doc.get('url', ''),
                    'error': str(e)
                })
        
        return results
    
    def load_documents_from_json(self, file_path: str) -> List[Dict]:
        """从JSON文件加载文档数据
        
        Args:
            file_path: JSON文件路径
        
        Returns:
            文档列表
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回的是列表
                if isinstance(data, dict):
                    # 如果是单个文档，包装成列表
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    logger.error(f"文件格式不正确，期望列表或字典: {file_path}")
                    return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return []
    
    def save_analysis_results(self, results: List[Dict], output_file: str) -> bool:
        """保存分析结果到JSON文件
        
        Args:
            results: 分析结果列表
            output_file: 输出文件路径
        
        Returns:
            是否保存成功
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"分析结果已保存到: {output_file}")
            return True
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False
    
    def generate_analysis_report(self, results: List[Dict], output_file: str = 'analysis_report.html') -> bool:
        """生成HTML格式的分析报告
        
        Args:
            results: 分析结果列表
            output_file: 输出文件路径
        
        Returns:
            是否生成成功
        """
        try:
            # 计算统计信息
            total_docs = len(results)
            success_docs = sum(1 for r in results if 'error' not in r)
            failed_docs = total_docs - success_docs
            
            # 创建HTML报告
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>文档分析报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                    .stat-card {{ background-color: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .stat-value {{ font-size: 2.5em; font-weight: bold; color: #3498db; margin-bottom: 10px; }}
                    .stat-label {{ color: #7f8c8d; font-size: 1.1em; }}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .success {{ color: #27ae60; }}
                    .error {{ color: #e74c3c; }}
                    .document-item {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                    .keywords {{ color: #3498db; font-weight: bold; }}
                    .key-points {{ margin-top: 10px; padding-left: 20px; }}
                </style>
            </head>
            <body>
                <h1>文档分析报告</h1>
                
                <div class="summary">
                    <h2>总体统计</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{total_docs}</div>
                            <div class="stat-label">总文档数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value success">{success_docs}</div>
                            <div class="stat-label">成功分析</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value error">{failed_docs}</div>
                            <div class="stat-label">分析失败</div>
                        </div>
                    </div>
                </div>
                
                <h2>文档分析详情</h2>
            """
            
            # 添加每个文档的分析结果
            for result in results:
                if 'error' in result:
                    # 错误文档
                    html_content += f"""
                    <div class="document-item">
                        <h3>{result.get('title', '未命名文档')}</h3>
                        <p class="error">错误: {result['error']}</p>
                        <p>URL: <a href="{result.get('url', '')}" target="_blank">{result.get('url', '')}</a></p>
                    </div>
                    """
                else:
                    # 成功分析的文档
                    keywords_html = ', '.join(f'<span class="keywords">{kw}</span>' for kw in result.get('keywords', []))
                    key_points_html = ''.join(f'<li>{point}</li>' for point in result.get('key_points', []))
                    
                    html_content += f"""
                    <div class="document-item">
                        <h3>{result.get('title', '未命名文档')}</h3>
                        <p>发布时间: {result.get('publish_time', '未知')}</p>
                        <p>URL: <a href="{result.get('url', '')}" target="_blank">{result.get('url', '')}</a></p>
                        <p>摘要: {result.get('summary', '')}</p>
                        <p>关键词: {keywords_html}</p>
                        {f'<div class="key-points"><p>关键点:</p><ul>{key_points_html}</ul></div>' if key_points_html else ''}
                    </div>
                    """
            
            # 结束HTML内容
            html_content += f"""
            </body>
            </html>
            """
            
            # 保存HTML报告
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"分析报告已保存到: {output_file}")
            return True
        except Exception as e:
            logger.error(f"生成分析报告失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'analysis_results.json'
        report_file = sys.argv[3] if len(sys.argv) > 3 else 'analysis_report.html'
        
        analyzer = LLMAnalyzer()
        
        # 加载文档
        documents = analyzer.load_documents_from_json(input_file)
        if not documents:
            print(f"没有找到有效文档，或文件格式错误: {input_file}")
            sys.exit(1)
        
        # 批量分析
        results = analyzer.batch_analyze(documents)
        
        # 保存结果
        analyzer.save_analysis_results(results, output_file)
        
        # 生成HTML报告
        analyzer.generate_analysis_report(results, report_file)
        
        print(f"分析完成！结果已保存到 {output_file}，报告已保存到 {report_file}")
    else:
        print("用法: python llm_analyzer.py <输入JSON文件> [输出结果文件] [HTML报告文件]")