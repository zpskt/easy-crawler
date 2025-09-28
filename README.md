# easy-crawler

一个轻量级、多功能的网页内容爬取与分析框架，支持中国家电网特定爬取、向量数据库存储和基于LLM的文档分析与知识对话。

## 功能概览

- **中国家电网特定爬虫**：支持多个频道（冰箱、空调、电视影音、洗衣机等）的文章爬取
- **通用网页爬虫**：支持任意网页的内容提取和链接爬取
- **智能内容提取**：自动提取文章标题、发布时间、URL和详细内容
- **向量数据库存储**：基于FAISS的高效语义搜索和文档管理
- **LLM文档分析**：支持文档摘要、关键词提取和内容分析
- **知识对话系统**：支持基于向量数据库的问答，可展示文档标题和URL链接
- **每日自动爬取系统**：支持定时任务，自动爬取、分析并存储最新文章
- **导出功能**：支持将分析结果导出为Word文档

## 快速开始

### 环境安装

```bash
# 克隆项目
git clone <项目地址>
cd easy-crawler

# 创建虚拟环境
conda create -n crawler_env python=3.9 -y
conda activate crawler_env

# 安装依赖
pip install -r requirements.txt
```

## 中国家电网爬虫

### 支持的频道和模块

| 频道标识 | 频道名称 | 支持的模块 |
|---------|---------|-----------|
| icebox  | 冰箱频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| ac      | 空调频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| tv      | 电视影音 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |
| washing | 洗衣机频道 | xinpin(新品速递), hangqing(行业瞭望), pinpai(品牌观察), pingce(产品评测), xuangou(选购指南) |

### 命令行使用

```bash
# 列出所有频道
python -m src.business.cheaa_crawler list-channels

# 爬取指定频道和模块的内容
python -m src.business.cheaa_crawler crawl --channels icebox ac --modules xinpin --output cheaa_crawl_result.json

# 使用Selenium爬取动态页面
python -m src.business.cheaa_crawler crawl --channels icebox ac --modules xinpin --use-selenium
```

### 完整爬虫脚本

`scripts/daily_crawler_analyzer.py`提供完整爬取流程，支持自动保存到FAISS向量数据库和MySQL数据库：

```bash
# 爬取指定频道和模块并保存到向量数据库
source activate crawler_env
python scripts/daily_crawler_analyzer.py --channels icebox --modules xinpin

# 限制爬取文章数量和请求间隔
python scripts/daily_crawler_analyzer.py --channels icebox --modules xinpin --batch-size 10 --delay 3

# 指定配置文件
python scripts/daily_crawler_analyzer.py --config /path/to/your/config.json
```

## 通用网页爬虫

系统还提供了一个通用网页爬虫，可以爬取任意网页的内容：

```bash
# 爬取指定网页列表
python scripts/crawler_page.py
```

配置文件位于 [scripts/config.py](file:///Users/zhangpeng/Desktop/zpskt/easy-crawler/scripts/config.py) 中的 `CRAWLER_PAGE_CONFIG` 部分，可以配置要爬取的网页URL列表。

## 向量数据库功能

### 主要特性

- 自动将文档转换为向量表示
- 支持语义相似度搜索
- 支持按日期范围查询
- 提供统计信息查询
- 数据持久化存储

### 向量数据库查询工具

```bash
# 语义搜索
python scripts/vector_query.py search "冰箱新品上市" --top-k 5

# 语义搜索并限制日期范围
python scripts/vector_query.py search "空调技术趋势" --top-k 5 --start-date 2025-09-01 --end-date 2025-09-30

# 查询最近10天的文档
python scripts/vector_query.py recent --days 10 --top-k 10

# 查看向量数据库统计信息
python scripts/vector_query.py stats
```

## 知识对话系统

项目提供了基于向量数据库的知识对话功能，支持自然语言问答并展示相关文档的标题和URL链接。

### 启动对话服务

```bash
# 启动API服务器
python scripts/api_server.py

# 启动前端界面
cd web
npm install
npm run dev
```

### 使用方法

1. 在网页界面中输入查询内容
2. 系统会从向量数据库中检索相关文档
3. 生成回答时会包含相关文档的标题和完整URL链接
4. 可以查询"stats"获取向量数据库统计信息
5. 可以询问"现在把你知道的文档标题和访问链接都发给我"获取所有文档链接

## LLM文档分析

### 功能特点

- 自动分析文档内容，提取摘要、关键词和关键点
- 支持批量分析多个文档
- 生成HTML分析报告
- 可扩展支持真实的LLM API调用

### 使用方法

```bash
# 分析文档文件
python scripts/analyze_documents.py extraction_results.json

# 指定输出目录
python scripts/analyze_documents.py extraction_results.json --output-dir my_reports
```

## Word文档导出

支持将分析结果导出为Word文档格式：

```bash
# 导出分析结果到Word文档
python scripts/export_to_word.py daily_analysis_20250928.json --output report.docx
```

## 项目结构

```
easy-crawler/
├── src/                    # 源代码目录
│   ├── business/           # 业务逻辑
│   ├── core/               # 核心爬虫模块
│   ├── storage/            # 存储模块（向量数据库）
│   ├── llm_analysis/       # LLM分析模块
│   └── config/             # 配置文件
├── scripts/                # 实用脚本
├── web/                    # 前端界面
├── daily_reports/          # 每日报告目录
├── outdir/                 # 输出目录
├── api_server.py           # API服务器
└── requirements.txt        # 项目依赖
```

## 定时任务

系统支持通过cron（Linux/macOS）或任务计划程序（Windows）设置定时任务，实现每日自动爬取和分析：

```bash
# Linux/macOS cron示例 - 每天凌晨2点执行
0 2 * * * cd /path/to/easy-crawler && python scripts/daily_crawler_analyzer.py >> daily_crawler.log 2>&1
```

## 注意事项

1. 对于动态页面，使用`--use-selenium`选项
2. 频繁请求可能被限制，请适当控制请求频率
3. 集成真实LLM API时，需修改[LLMAnalyzer](file:///Users/zhangpeng/Desktop/zpskt/easy-crawler/src/llm_analysis/llm_analyzer.py#L25-L590)类中的相关配置
4. 向量数据库默认使用绝对路径存储，请确保路径配置正确
5. 确保已安装Chrome浏览器和对应的ChromeDriver以支持Selenium功能

## 常见问题

### 提取失败
- 检查网站是否有反爬机制
- 尝试使用Selenium模式
- 检查网络连接

### 向量数据库统计显示为0
- 确认向量索引文件和元数据文件路径正确
- 检查文件是否存在且有权限访问

### 知识对话不显示URL
- 确保已更新到最新版本，API服务器中已添加URL展示功能

### 定时任务不执行
- 检查cron表达式是否正确
- 确认脚本路径和Python路径是否正确
- 查看日志文件了解错误详情