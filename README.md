# easy-crawler

一个简单易用的网页内容智能提取工具，可以自动提取网页中的文章标题、正文、图片等信息，支持静态和动态页面。

## 项目特点

- 自动选择最佳的提取方法（trafilatura和readability-lxml），确保提取成功率
- 支持静态页面和动态页面（通过Selenium）
- 可以提取标题、正文、图片、作者、日期等信息
- 提供批量处理功能，支持CSV/Excel格式的URL列表
- 网站特定配置，可针对不同网站进行优化

## 环境安装

```bash
pip install trafilatura readability-lxml requests beautifulsoup4 selenium webdriver-manager pandas tqdm
```

## 基本使用

### 静态页面提取

```python
from crawler import UniversalWebExtractor

extractor = UniversalWebExtractor(use_selenium=False)  # 静态页面
try:
    result = extractor.smart_extract("http://example.com")
    print(f"标题: {result['title']}")
    print(f"内容长度: {result['content_length']}字符")
    print(f"图片数量: {result['image_count']}")
except Exception as e:
    print(f"提取失败: {e}")
finally:
    extractor.close()  # 关闭资源
```

### 动态页面提取

```python
from crawler import UniversalWebExtractor

extractor = UniversalWebExtractor(use_selenium=True)  # 动态页面如微博
try:
    result = extractor.smart_extract("https://weibo.com/xxx")
    print(f"标题: {result['title']}")
    print(f"内容长度: {result['content_length']}字符")
    print(f"图片数量: {result['image_count']}")
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
- `url`: 提取的网页URL
- `extraction_time`: 提取时间
- `content_length`: 内容长度（字符数）
- `image_count`: 图片数量
- `error`: 错误信息（如果提取失败）

## 批量处理

使用`batch_processor.py`可以批量处理URL列表：

```python
from batch_processor import batch_process_urls

# 批量处理URL列表
# 支持CSV或Excel文件，文件中需包含名为'url'的列
batch_process_urls('urls.csv', 'extraction_results.json', use_selenium=False)
```

也可以直接运行脚本：

```bash
python batch_processor.py
```

## 网站特定配置

在`config.py`文件中，可以配置针对特定网站的提取参数：

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