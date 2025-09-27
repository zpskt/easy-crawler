# 每日爬取和分析系统使用说明

## 概述

本系统实现了对中国家电网数据的每日自动爬取、持久化存储和智能分析功能。系统将爬取的数据保存到MySQL数据库和FAISS向量数据库中，并生成每日分析报告。

## 功能特点

- **自动爬取**：每天自动爬取中国家电网的新文章
- **多渠道持久化**：支持MySQL数据库、FAISS向量数据库、JSON文件和API接口存储
- **智能分析**：使用LLM模型（如DeepSeek）对文章进行摘要提取、关键词识别和关键点分析
- **报告生成**：生成每日新文章列表和详细的分析报告
- **配置灵活**：支持通过配置文件或命令行参数进行设置

## 系统架构

![系统架构图](https://i.imgur.com/example.png)

- **爬取模块**：负责从中国家电网获取新文章数据
- **持久化模块**：将数据保存到MySQL、FAISS和JSON文件
- **分析模块**：使用LLM对文章内容进行智能分析
- **报告模块**：生成每日新文章列表和分析报告

## 环境准备

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 特别安装以下依赖
pip install pymysql requests beautifulsoup4 selenium tqdm faiss-cpu
```

### 数据库准备

1. 安装MySQL数据库
2. 创建数据库（默认为`cheaa`）
3. 配置数据库用户和密码

### LLM服务准备

确保本地Ollama服务已启动，并加载了`deepseek-r1:7b`模型：

```bash
# 拉取模型
oollama pull deepseek-r1:7b

# 启动Ollama服务
systemctl start ollama
```

## 配置说明

### 1. 配置文件方式

编辑 `src/config/db_config.json` 文件，填写数据库和API配置：

```json
{
  "mysql": {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "cheaa"
  },
  "api": {
    "url": "https://api.example.com/save",
    "api_key": "your_api_key"
  }
}
```

**注意：** 此文件包含敏感信息，已添加到`.gitignore`中，不会被提交到版本控制系统。

### 2. 命令行参数方式

系统支持通过命令行参数覆盖配置文件中的设置：

```bash
python scripts/daily_crawler_analyzer.py --mysql-user root --mysql-password password --mysql-database cheaa
```

## 使用方法

### 基本用法

使用默认配置文件和参数运行：

```bash
python scripts/daily_crawler_analyzer.py
```

### 指定配置文件

```bash
python scripts/daily_crawler_analyzer.py --config /path/to/your/config.json
```

### 指定爬取频道和模块

```bash
python scripts/daily_crawler_analyzer.py --channels icebox ac --modules xinpin hangqing
```

### 完整示例

```bash
python scripts/daily_crawler_analyzer.py \
  --channels icebox ac tv washing \
  --modules xinpin hangqing pinpai \
  --delay 3 \
  --batch-size 100 \
  --mysql-host localhost \
  --mysql-user root \
  --mysql-password your_password \
  --mysql-database cheaa \
  --api-url https://api.example.com/save \
  --api-key your_api_key
```

## 命令行参数说明

| 参数 | 短选项 | 说明 | 默认值 |
|------|-------|------|--------|
| `--channels` | `-c` | 频道标识列表，例如：`icebox ac` | `['icebox', 'ac', 'tv', 'washing']` |
| `--modules` | `-m` | 模块标识列表，例如：`xinpin hangqing` | `['xinpin', 'hangqing', 'pinpai', 'pingce', 'xuangou']` |
| `--batch-size` | `-b` | 批处理大小，只处理指定数量的文章 | 全部 |
| `--delay` | `-d` | 两次请求之间的延迟（秒） | `2` |
| `--config` | `-C` | 配置文件路径 | `src/config/db_config.json` |
| `--mysql-host` | | MySQL主机地址 | 配置文件中的值或`localhost` |
| `--mysql-user` | | MySQL用户名 | 配置文件中的值（必需） |
| `--mysql-password` | | MySQL密码 | 配置文件中的值（必需） |
| `--mysql-database` | | MySQL数据库名 | 配置文件中的值（必需） |
| `--api-url` | | API接口URL | 配置文件中的值 |
| `--api-key` | | API密钥 | 配置文件中的值 |

## 输出文件

系统会在`daily_reports`目录下生成以下文件：

1. `daily_new_articles_YYYYMMDD.json` - 每日新文章列表，包含文章标题和URL
2. `daily_analysis_YYYYMMDD.json` - LLM分析结果的JSON格式
3. `daily_analysis_YYYYMMDD.html` - LLM分析结果的HTML格式报告

## 数据库结构

系统会自动创建以下表结构：

### 1. articles 表

存储文章的基本信息

```sql
CREATE TABLE IF NOT EXISTS articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(512) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    publish_time DATETIME,
    channel VARCHAR(100),
    channel_name VARCHAR(100),
    module VARCHAR(100),
    module_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

### 2. article_analyses 表

存储文章的分析结果

```sql
CREATE TABLE IF NOT EXISTS article_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    summary TEXT,
    keywords JSON,
    key_points JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
)
```

### 3. daily_summaries 表

存储每日爬取和分析的汇总信息

```sql
CREATE TABLE IF NOT EXISTS daily_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_articles INT NOT NULL,
    new_articles INT NOT NULL,
    summary_file VARCHAR(255),
    analysis_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

## 定时任务设置

### Linux/macOS系统

使用cron设置每日定时任务：

```bash
# 编辑crontab
crontab -e

# 添加每日凌晨2点执行的任务
0 2 * * * cd /path/to/easy-crawler && /path/to/python3 scripts/daily_crawler_analyzer.py >> /path/to/cron.log 2>&1
```

### Windows系统

使用任务计划程序设置每日定时任务：

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器为"每天"
4. 操作选择"启动程序"
5. 程序/脚本设置为python.exe路径
6. 添加参数设置为scripts/daily_crawler_analyzer.py
7. 起始于设置为项目根目录

## 常见问题与解决方案

### 1. 数据库连接失败

- 检查`db_config.json`中的数据库配置是否正确
- 确认MySQL服务是否正在运行
- 确认数据库用户是否有足够的权限

### 2. LLM分析失败

- 确认Ollama服务是否正在运行
- 确认`deepseek-r1:7b`模型是否已下载
- 检查网络连接是否正常

### 3. 爬取速度过慢

- 增加`--delay`参数的值，减少请求频率
- 使用`--batch-size`参数限制爬取文章数量

### 4. FAISS持久化失败

- 确认已安装`faiss-cpu`或`faiss-gpu`包
- 检查系统内存是否足够

## 日志管理

系统会生成`daily_crawler.log`文件，记录爬取和分析过程中的关键信息和错误日志。定期检查日志文件可以及时发现并解决问题。

## 注意事项

1. 请遵守网站的robots.txt规则，合理设置爬取频率
2. 数据库配置文件包含敏感信息，请妥善保管
3. 定期备份数据库，防止数据丢失
4. LLM分析可能需要较长时间，请耐心等待
5. 首次运行时，系统会创建必要的数据库表结构

## 版本更新记录

### v1.0.0 (2025-10-02)
- 初始版本发布
- 实现基本的每日爬取和分析功能
- 支持MySQL、FAISS、JSON文件和API存储
- 提供灵活的配置选项

## 联系我们

如有任何问题或建议，请联系：

邮箱：zpskt@example.com
GitHub：https://github.com/zpskt/easy-crawler