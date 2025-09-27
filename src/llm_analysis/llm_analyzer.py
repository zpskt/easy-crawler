#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM文档分析器 - 用于分析爬取的文档并生成简要报告
"""
import json
import os
import logging
import requests
import time
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM文档分析器类"""
    
    def __init__(self, use_real_llm: bool = True, ollama_url: str = "http://localhost:11434/api/generate", model: str = "deepseek-r1:7b"):
        """初始化分析器
        
        Args:
            use_real_llm: 是否使用真实的LLM模型
            ollama_url: ollama API的URL地址
            model: 使用的模型名称
        """
        # 这里初始化LLM API客户端
        self.use_real_llm = use_real_llm
        self.ollama_url = ollama_url
        self.model = model
        self.max_retries = 3
        self.retry_delay = 5  # 增加重试间隔时间到5秒
        self.timeout = 60  # 增加超时时间到60秒
        
        # 如果启用真实LLM，测试连接
        if self.use_real_llm:
            self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """测试与ollama服务的连接"""
        try:
            logger.info(f"测试连接到ollama服务: {self.ollama_url}，使用模型: {self.model}")
            # 发送一个简单的请求测试连接
            response = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": "hello", "stream": False},
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info(f"成功连接到ollama服务，使用模型: {self.model}")
                logger.info(f"响应示例: {response.json().get('response', '')[:30]}...")
            else:
                logger.warning(f"连接到ollama服务失败，状态码: {response.status_code}")
                logger.warning(f"响应内容: {response.text}")
        except requests.Timeout:
            logger.warning(f"连接到ollama服务超时，请检查服务是否正常运行或增加超时时间")
        except requests.ConnectionError:
            logger.warning(f"无法连接到ollama服务，请确保服务正在运行，URL: {self.ollama_url}")
        except Exception as e:
            logger.warning(f"测试ollama连接时出错: {type(e).__name__}: {e}")
            logger.info("请确保ollama服务正在运行，并且已经下载了指定的模型")
    
    def _call_llm_api(self, content: str) -> Dict:
        """调用LLM API进行文档分析
        
        Args:
            content: 文档内容
            
        Returns:
            分析结果字典
        """
        # 构建提示词
        prompt = f"""请分析以下文档内容，并按照要求生成分析结果：
                1. 生成2-4句话的摘要
                2. 提取3个关键词
                3. 列出3-5个关键点
                返回的数据格式为JSON，请返回JSON格式数据。
                摘要放在summary字段，关键词放在keywords字段，关键点放在key_points字段。
                文档内容：
                {content[:2000]}..."""
        
        logger.info(f"准备调用LLM API，内容长度: {len(content)}字符")
        # 调用ollama API
        for attempt in range(self.max_retries):
            try:
                logger.info(f"第{attempt+1}/{self.max_retries}次尝试调用LLM API...")
                start_time = time.time()
                response = requests.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 500
                        }
                    },
                    timeout=self.timeout
                )
                end_time = time.time()
                logger.info(f"API调用完成，耗时: {end_time - start_time:.2f}秒")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"API调用成功，响应长度: {len(result.get('response', ''))}字符")
                    return self._parse_llm_response(result.get("response", ""))
                else:
                    logger.error(f"LLM API调用失败，状态码: {response.status_code}")
                    logger.error(f"响应内容: {response.text}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"{self.retry_delay}秒后重试...")
                        time.sleep(self.retry_delay)
            except requests.Timeout:
                logger.error(f"LLM API调用超时 (当前设置: {self.timeout}秒)")
                if attempt < self.max_retries - 1:
                    logger.info(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
            except requests.ConnectionError:
                logger.error(f"无法连接到ollama服务，请检查服务是否正在运行")
                if attempt < self.max_retries - 1:
                    logger.info(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"LLM API调用异常: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
        
        # 如果所有重试都失败，返回空结果
        logger.error(f"所有{self.max_retries}次LLM API调用尝试都失败了")
        return {
            "summary": "",
            "keywords": [],
            "key_points": []
        }
    
    def _remove_thinking_process(self, response):
        """
        移除LLM响应中的思考过程内容
        """
        # 移除思考过程标记（<think>...</think>格式）
        if '<think>' in response and '</think>' in response:
            # 找到第一个和最后一个思考过程标记
            start = response.find('<think>') + len('<think>')
            end = response.find('</think>')
            # 保留标记外的内容
            response = response[:response.find('<think>')] + response[end + len('</think>'):]
        
        # 同时保留对旧格式的支持（以防万一）
        if '</think>' in response and '</think>' in response[response.find('</think>')+3:]:
            start = response.find('</think>') + 3
            end = response.rfind('</think>')
            response = response[:response.find('</think>')] + response[end+3:]
        
        # 处理其他可能的思考过程格式
        if '思考过程' in response or 'thought' in response.lower():
            # 可以添加更多过滤逻辑
            pass
            
        return response.strip()

    def _parse_llm_response(self, response):
        """解析LLM的响应，提取摘要、关键词和关键点"""
        try:
            # 第一步：移除思考过程
            clean_response = self._remove_thinking_process(response)
            logger.debug(f"过滤思考过程后的响应: {clean_response}")
            
            # 第二步：移除Markdown代码块标记
            if clean_response.startswith('```json') and '```' in clean_response:
                # 找到开始和结束的代码块标记
                start_marker = '```json'
                end_marker = '```'
                start_index = clean_response.find(start_marker) + len(start_marker)
                end_index = clean_response.rfind(end_marker)
                # 提取中间的JSON内容
                json_content = clean_response[start_index:end_index].strip()
                logger.debug(f"移除代码块标记后的JSON内容: {json_content}")
            else:
                json_content = clean_response
            
            # 第三步：尝试直接解析JSON
            try:
                result = json.loads(json_content)
                logger.debug(f"成功解析JSON响应: {result}")
                
                # 验证必要的字段是否存在
                if all(key in result for key in ['summary', 'keywords', 'key_points']):
                    return {
                        'summary': result['summary'],
                        'keywords': result['keywords'],
                        'key_points': result['key_points']
                    }
                else:
                    logger.warning("JSON格式不完整，缺少必要字段")
                    # 如果JSON格式不完整，回退到文本解析
                    return self._parse_text_response(json_content)
                
            except json.JSONDecodeError:
                logger.warning(f"JSON解析失败，回退到文本解析: {json_content}")
                # JSON解析失败，回退到文本解析
                return self._parse_text_response(json_content)
                
        except Exception as e:
            logger.error(f"解析响应时发生错误: {str(e)}")
            return {
                'summary': "",
                'keywords': [],
                'key_points': []
            }

    def _parse_text_response(self, text):
        """当JSON解析失败时，使用文本解析作为备选方案"""
        # 这里保留原有的文本解析逻辑
        result = {
            "summary": "",
            "keywords": [],
            "key_points": []
        }
        
        # 这里放入原来的文本解析代码
        # 简单解析响应，根据常见的格式进行提取
        lines = response.strip().split('\n')
        
        # 重置所有解析状态
        parsing_summary = False
        parsing_keywords = False
        parsing_key_points = False
        
        # 遍历所有行，根据行内容判断当前应该解析的部分
        for line in lines:
            stripped_line = line.strip()
            
            # 如果是空行，跳过
            if not stripped_line:
                continue
            
            # 检查是否是部分标题行，使用更宽松的匹配
            if ('摘要' in stripped_line or 'Summary' in stripped_line.lower()):
                parsing_summary = True
                parsing_keywords = False
                parsing_key_points = False
                # 如果标题后面直接跟内容，提取内容
                if ':' in stripped_line:
                    summary_content = stripped_line.split(':', 1)[1].strip()
                    if summary_content:
                        result["summary"] = summary_content
                continue
            elif ('关键词' in stripped_line or 'Keywords' in stripped_line.lower()):
                parsing_summary = False
                parsing_keywords = True
                parsing_key_points = False
                continue
            elif ('关键点' in stripped_line or 'Key Points' in stripped_line.lower()):
                parsing_summary = False
                parsing_keywords = False
                parsing_key_points = True
                continue
            
            # 根据当前解析状态处理内容
            if parsing_summary:
                # 移除可能的引号和HTML实体
                cleaned_line = stripped_line.replace('&quot;', '"').replace('&amp;', '&')
                if result["summary"]:
                    result["summary"] += ' ' + cleaned_line
                else:
                    result["summary"] = cleaned_line
            elif parsing_keywords:
                # 处理关键词行，可能包含序号
                if stripped_line[0].isdigit() and (stripped_line[1] == '.' or stripped_line[1] == '、'):
                    # 移除序号前缀（如1.、2.、3.等）
                    keyword = stripped_line.split('.', 1)[1].strip() if '.' in stripped_line else \
                              stripped_line.split('、', 1)[1].strip()
                    if keyword and len(result["keywords"]) < 5:
                        result["keywords"].append(keyword)
                elif ':' in stripped_line:
                    # 处理类似"关键词：关键词1，关键词2"的格式
                    keywords_part = stripped_line.split(':', 1)[1].strip()
                    # 分割关键词（处理逗号、顿号、分号等分隔符）
                    for sep in [',', '，', ';', '；']:
                        if sep in keywords_part:
                            keywords = [kw.strip() for kw in keywords_part.split(sep)]
                            for kw in keywords[:5 - len(result["keywords"])]:
                                if kw:
                                    result["keywords"].append(kw)
                            break
            elif parsing_key_points:
                # 处理关键点行，可能包含序号
                if stripped_line[0].isdigit() and (stripped_line[1] == '.' or stripped_line[1] == '、'):
                    # 移除序号前缀（如1.、2.、3.等）
                    key_point = stripped_line.split('.', 1)[1].strip() if '.' in stripped_line else \
                               stripped_line.split('、', 1)[1].strip()
                    # 移除可能的引号和HTML实体
                    key_point = key_point.replace('&quot;', '"').replace('&amp;', '&')
                    if key_point and len(result["key_points"]) < 3:
                        result["key_points"].append(key_point)
        
        # 如果解析后仍然没有数据，尝试使用备选解析方案
        if not result["summary"] and not result["keywords"] and not result["key_points"]:
            # 尝试直接从响应中提取有用信息
            for i, line in enumerate(lines):
                stripped_line = line.strip().replace('&quot;', '"').replace('&amp;', '&')
                if not stripped_line:
                    continue
                
                # 如果是第一行且长度适中，可能是摘要
                if i == 0 and 20 <= len(stripped_line) <= 200:
                    result["summary"] = stripped_line
                # 如果包含明显的关键词格式
                elif ':' in stripped_line and ('关键词' in stripped_line or 'Keywords' in stripped_line.lower()):
                    keywords_part = stripped_line.split(':', 1)[1].strip()
                    for sep in [',', '，', ';', '；']:
                        if sep in keywords_part:
                            keywords = [kw.strip() for kw in keywords_part.split(sep)]
                            result["keywords"] = keywords[:5]
                            break
                # 如果包含序号列表，可能是关键点
                elif stripped_line[0].isdigit() and (stripped_line[1] == '.' or stripped_line[1] == '、') and len(stripped_line) > 10:
                    key_point = stripped_line.split('.', 1)[1].strip() if '.' in stripped_line else \
                               stripped_line.split('、', 1)[1].strip()
                    if key_point and len(result["key_points"]) < 3:
                        result["key_points"].append(key_point)
        
        return result

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
        
        # 生成分析结果
        if self.use_real_llm:
            # 调用实际的LLM API
            llm_result = self._call_llm_api(content)
            analysis_result['summary'] = llm_result.get('summary', '')
            analysis_result['keywords'] = llm_result.get('keywords', [])
            analysis_result['key_points'] = llm_result.get('key_points', [])
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
        use_real_llm = True if '--use-real-llm' in sys.argv else True
        model = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else 'deepseek-r1:7b'
        
        analyzer = LLMAnalyzer(use_real_llm=use_real_llm, model=model)
        
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
        print("用法: python llm_analyzer.py <输入JSON文件> [输出结果文件] [HTML报告文件] [--use-real-llm] [--model 模型名称]")