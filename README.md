# easy-crawler

一个简单易用的网页内容智能提取工具，可以自动提取网页中的文章标题、正文、图片等信息，支持静态和动态页面。

## 项目特点

- 自动选择最佳的提取方法（trafilatura和readability-lxml），确保提取成功率
- 支持静态页面和动态页面（通过Selenium）
- 可以提取标题、正文、图片、作者、日期等信息
- 提供批量处理功能，支持CSV/Excel格式的URL列表
- 网站特定配置，可针对不同网站进行优化
- 灵活的数据持久化模块，支持多种存储方式
- 中国家电网专用频道爬虫，支持多种频道和模块
- LLM文档分析功能，可自动分析爬取的文档并生成简要报告

## 环境安装

```bash
pip install trafilatura readability-lxml requests beautifulsoup4 selenium webdriver-manager pandas tqdm
```

## 基本使用

### 静态页面提取

```python
from src.core.crawler import UniversalWebExtractor

extractor = UniversalWebExtractor(use_selenium=False)  # 静态页面
try:
  result = extractor.smart_extract("http://example.com")
  print(f"标题: {result['title']}")
  print(f"内容长度: {result['content_length']}字符")
  print(f"图片数量: {result['image_count']}")
  print(f"发布时间: {result.get('publish_time', '未找到')}")
except Exception as e:
  print(f"提取失败: {e}")
finally:
  extractor.close()  # 关闭资源
```

### 动态页面提取

```python
from src.core.crawler import UniversalWebExtractor

extractor = UniversalWebExtractor(use_selenium=True)  # 动态页面如微博
try:
  result = extractor.smart_extract("https://weibo.com/xxx")
  print(f"标题: {result['title']}")
  print(f"内容长度: {result['content_length']}字符")
  print(f"图片数量: {result['image_count']}")
  print(f"发布时间: {result.get('publish_time', '未找到')}")
except Exception as e:
  print(f"提取失败: {e}")
finally:
  extractor.close()  # 关闭资源
```

## 提取结果字段说明

提取结果是一个字典，包含以下字段：

- `title`: 文章标题
- `content`: 清理后的正文内容
- `images`: 图片列表（包含URL、alt文本、宽高等信息）
- `source`: 使用的提取方法（trafilatura或readability）
- `author`: 作者（如果可提取）
- `date`: 发布日期（如果可提取）
- `publish_time`: 精确的发布时间（格式：YYYY-MM-DD HH:MM，特别针对中国家电网优化）
- `url`: 提取的网页URL
- `extraction_time`: 提取时间
- `content_length`: 内容长度（字符数）
- `image_count`: 图片数量
- `error`: 错误信息（如果提取失败）

## 批量处理

使用`scripts/batch_processor.py`可以批量处理URL列表：

```python
from scripts.batch_processor import batch_process_urls

# 批量处理URL列表
# 支持CSV或Excel文件，文件中需包含名为'url'的列
batch_process_urls('src/config/urls.csv', 'extraction_results.json', use_selenium=False)
```

也可以直接运行脚本：

```bash
python scripts/batch_processor.py
```

## 网站特定配置

在`src/config/config.py`文件中，可以配置针对特定网站的提取参数：

```python
# 示例配置
SITE_CONFIGS = {
    'weibo.com': {
        'use_selenium': True,  # 使用Selenium处理动态加载
        'wait_time': 5,        # 等待时间（秒）
        'content_selectors': ['.weibo-text']  # 内容选择器
    },
    'cheaa.com': {
        'use_selenium': False,  # 静态页面，不需要Selenium
        'content_selectors': ['.content', '.article-content']
    }
}
```

## 数据持久化模块

`src/storage/data_persistence.py`提供了灵活的数据持久化功能，支持多种存储方式：

### 功能特点

- 基于策略模式设计，易于扩展新的持久化方式
- 支持JSON文件存储、HTML报告生成、API调用和数据库存储
- 提供统一的接口进行数据保存
- 单例模式的管理器，方便全局使用

### 使用示例

```python
from src.storage.data_persistence import get_default_manager

# 获取持久化管理器实例（单例模式）
manager = get_default_manager()

# 保存数据为JSON文件
manager.save_with_method('json', data, 'output.json')

# 生成HTML报告
manager.save_with_method('html_report', data)

# 使用API保存数据（需要在配置中设置API地址）
# manager.save_with_method('api', data)

# 保存到数据库（需要在配置中设置数据库连接信息）
# manager.save_with_method('database', data)
```

### 支持的持久化策略

- **JSON文件**: 将数据保存为JSON格式文件
- **HTML报告**: 生成可视化的HTML报告
- **API调用**: 将数据通过HTTP请求发送到指定API
- **数据库**: 将数据直接保存到数据库（预留接口，需自行实现具体数据库连接）

## 中国家电网频道爬虫

`src/business/cheaa_crawler.py`提供了专门针对中国家电网的频道和模块爬虫功能：

### 功能特点

- 支持多个频道的选择（冰箱、空调、电视影音、洗衣机等）
- 支持每个频道下的多个模块爬取（新品速递、行业瞭望、品牌观察等）
- 自动提取文章链接和标题
- 支持提取文章的发布时间
- 提供命令行接口，方便批量操作

### 支持的频道和模块

| 频道标识 | 频道名称 | 支持的模块 |
|---------|---------|-----------|
| icebox  | 冰箱频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| ac      | 空调频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| tv      | 电视影音 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| washing | 洗衣机频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |

### 使用示例

```python
from src.business.cheaa_crawler import CheaaChannelCrawler

# 创建爬虫实例
crawler = CheaaChannelCrawler()

# 列出所有可用频道
crawler.list_channels()

# 列出指定频道的模块
crawler.list_modules('icebox')

# 批量爬取指定频道和模块
results = crawler.batch_crawl(
  channel_keys=['icebox', 'ac'],  # 冰箱和空调频道
  module_keys=['xinpin'],  # 仅爬取新品速递模块
  output_file='cheaa_crawl_result.json'
)
```

### 命令行接口

```bash
# 列出所有频道
python -m src.business.cheaa_crawler list-channels

# 列出指定频道的模块
python -m src.business.cheaa_crawler list-modules icebox

# 生成指定频道和模块的URL
python -m src.business.cheaa_crawler generate-urls --channels icebox ac --modules xinpin

# 爬取指定频道和模块的内容
python -m src.business.cheaa_crawler crawl --channels icebox ac --modules xinpin --output cheaa_crawl_result.json

# 使用Selenium爬取
python -m src.business.cheaa_crawler crawl --channels icebox ac --modules xinpin --use-selenium
```

## 项目结构

```
easy-crawler/
├── crawler.py           # 核心提取功能实现
├── config.py            # 网站特定配置
├── batch_processor.py   # 批量处理功能
├── README.md            # 项目说明文档
├── .gitignore           # Git忽略文件
└── extraction_result_1.json  # 提取结果示例
```

## 核心类和方法

### UniversalWebExtractor

主要类，用于提取网页内容。

- `__init__(use_selenium=False)`: 初始化提取器
  - `use_selenium`: 是否使用Selenium处理动态页面

- `smart_extract(url)`: 智能提取网页内容
  - `url`: 要提取的网页URL
  - 返回: 包含提取结果的字典

- `close()`: 清理资源，关闭Selenium WebDriver

## 注意事项

1. 对于动态页面（如微博），需要使用`use_selenium=True`选项
2. 使用Selenium时，首次运行会自动下载ChromeDriver
3. 频繁请求同一网站可能会被限制，请适当控制请求频率
4. 不同网站的结构差异较大，提取效果可能有所不同
5. 如果提取结果不理想，可以在`config.py`中添加针对该网站的配置

## 常见问题

### 1. 为什么提取失败？

- 网站可能有反爬机制
- 网页结构可能比较特殊
- 网络问题导致无法访问页面

### 2. 如何提高提取成功率？

- 对于动态页面，使用`use_selenium=True`
- 在`config.py`中添加针对特定网站的配置
- 适当增加Selenium的等待时间

### 3. 如何处理大量URL？

使用批量处理功能，参考批量处理部分的说明

## LLM文档分析功能

easy-crawler现在提供了强大的LLM文档分析功能，可以自动分析爬取的文档内容并生成简要报告。

### 功能特点

- 自动分析文档内容，提取摘要、关键词和关键点
- 支持批量分析多个文档
- 生成直观的HTML分析报告
- 可扩展支持真实的LLM API调用（如OpenAI、百度文心一言等）

### 使用方法

使用提供的命令行脚本可以快速分析爬取的文档：

```bash
# 分析单个文档文件
python analyze_documents.py extraction_results.json

# 分析多个文档文件
python analyze_documents.py file1.json file2.json file3.json

# 指定输出目录
python analyze_documents.py extraction_results.json --output-dir my_reports

# 只生成HTML报告（不生成JSON结果）
python analyze_documents.py extraction_results.json --no-json

# 只生成JSON结果（不生成HTML报告）
python analyze_documents.py extraction_results.json --no-html
```

### 分析结果包含

- 文档标题和URL
- 发布时间（如果有）
- 内容摘要
- 关键词提取
- 关键点总结

### 直接使用API

```python
from llm_analyzer import LLMAnalyzer

# 创建分析器实例
analyzer = LLMAnalyzer()

# 加载文档
# 可以是单个文档字典，也可以是文档列表
# documents = [{'title': '文档标题', 'content': '文档内容', ...}]
documents = analyzer.load_documents_from_json('extraction_results.json')

# 分析文档
results = analyzer.batch_analyze(documents)

# 保存分析结果
analyzer.save_analysis_results(results, 'analysis_results.json')

# 生成HTML报告
analyzer.generate_analysis_report(results, 'analysis_report.html')
```

### 集成真实LLM API

目前的实现使用模拟分析结果。要集成真实的LLM API，请修改`LLMAnalyzer`类中的`use_real_llm`属性为`True`，并实现`_call_llm_api`方法：

```python
# 在llm_analyzer.py中添加
class LLMAnalyzer:
    def __init__(self):
        self.use_real_llm = True  # 设置为True使用真实LLM API
        # 初始化LLM API客户端
        # 例如OpenAI API
        # import openai
        # openai.api_key = 'your-api-key'
    
    def _call_llm_api(self, content):
        """调用实际的LLM API进行分析"""
        # 实现实际的API调用
        # 例如：
        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "你是一个文档分析助手，..."},
        #         {"role": "user", "content": f"分析以下文档内容：{content[:2000]}"}
        #     ]
        # )
        # # 解析API响应并返回分析结果
        # return self._parse_llm_response(response)
        pass
```

## 代码分层结构

为了提高代码的可维护性和可扩展性，我们建议按照以下分层结构组织代码：