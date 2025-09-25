import requests
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import trafilatura
from readability import Document
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UniversalWebExtractor:
    def __init__(self, use_selenium=False):
        """
        初始化通用网页提取器

        Args:
            use_selenium: 是否使用Selenium处理动态加载页面
        """
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.setup_headers()

        if use_selenium:
            self.driver = self.setup_selenium()

    def setup_headers(self):
        """设置请求头，模拟真实浏览器"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def setup_selenium(self):
        """设置Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def get_page_content(self, url):
        """获取网页内容，支持静态和动态页面"""
        try:
            if self.use_selenium:
                return self.get_content_with_selenium(url)
            else:
                return self.get_content_with_requests(url)
        except Exception as e:
            logger.error(f"获取页面内容失败: {e}")
            return None

    def get_content_with_requests(self, url):
        """使用requests获取页面内容"""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text

    def get_content_with_selenium(self, url):
        """使用Selenium获取动态页面内容"""
        self.driver.get(url)
        time.sleep(3)  # 等待页面加载
        return self.driver.page_source

    def extract_with_trafilatura(self, html, url):
        """使用Trafilatura提取内容"""
        try:
            # 提取为JSON格式，包含更多信息
            result_json = trafilatura.extract(
                html,
                include_links=False,
                include_images=True,
                include_tables=False,
                output_format='json',
                url=url
            )

            if result_json:
                data = json.loads(result_json)
                return {
                    'title': data.get('title', ''),
                    'content': data.get('text', ''),
                    'images': self.extract_images_from_html(html, url),
                    'source': 'trafilatura',
                    'excerpt': data.get('excerpt', ''),
                    'author': data.get('author', ''),
                    'date': data.get('date', '')
                }
        except Exception as e:
            logger.warning(f"Trafilatura提取失败: {e}")

        return None

    def extract_with_readability(self, html, url):
        """使用Readability备用方案提取内容"""
        try:
            doc = Document(html)
            title = doc.title()
            content_html = doc.summary()

            # 清理HTML标签，获取纯文本
            soup = BeautifulSoup(content_html, 'html.parser')
            content_text = soup.get_text(separator='\n', strip=True)

            return {
                'title': title,
                'content': content_text,
                'images': self.extract_images_from_html(html, url),
                'source': 'readability',
                'excerpt': '',
                'author': '',
                'date': ''
            }
        except Exception as e:
            logger.warning(f"Readability提取失败: {e}")
            return None

    def extract_images_from_html(self, html, base_url):
        """从HTML中提取所有图片"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = []

            # 查找所有img标签
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 处理相对路径
                    full_url = urljoin(base_url, src)
                    alt = img.get('alt', '')

                    images.append({
                        'url': full_url,
                        'alt': alt,
                        'width': img.get('width'),
                        'height': img.get('height')
                    })

            return images
        except Exception as e:
            logger.error(f"图片提取失败: {e}")
            return []

    def clean_content(self, text):
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空行和空白字符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        return text

    def smart_extract(self, url):
        """智能提取网页内容"""
        logger.info(f"开始提取: {url}")

        # 获取页面HTML
        html = self.get_page_content(url)
        if not html:
            return {'error': '无法获取页面内容'}

        # 首先尝试使用trafilatura
        result = self.extract_with_trafilatura(html, url)

        # 如果trafilatura失败或内容太短，使用readability
        if not result or len(result.get('content', '')) < 100:
            logger.info("Trafilatura效果不佳，尝试Readability")
            result = self.extract_with_readability(html, url)

        if result:
            # 清理内容
            result['content'] = self.clean_content(result['content'])

            # 添加元数据
            result['url'] = url
            result['extraction_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            result['content_length'] = len(result.get('content', ''))
            result['image_count'] = len(result.get('images', []))

            logger.info(
                f"提取成功: 标题长度{len(result['title'])}, 内容长度{result['content_length']}, 图片数{result['image_count']}")
        else:
            result = {'error': '所有提取方法都失败了', 'url': url}
            logger.error(f"提取失败: {url}")

        return result

    def close(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            self.driver.quit()


# 使用示例
def main():
    # 测试URL列表
    test_urls = [
        "https://icebox.cheaa.com/2025/0921/649935.shtml",  # 中国家电网示例-新品速递
        # "https://weibo.com/xxx",  # 微博页面（需要动态加载）
        # 添加更多测试URL
    ]

    # 创建提取器（对于微博等动态网站使用selenium=True）
    extractor = UniversalWebExtractor(use_selenium=False)

    results = []
    for url in test_urls:
        try:
            result = extractor.smart_extract(url)
            results.append(result)

            # 打印结果摘要
            print(f"\n=== 提取结果: {url} ===")
            if 'error' in result:
                print(f"错误: {result['error']}")
            else:
                print(f"标题: {result['title'][:100]}...")
                print(f"内容预览: {result['content'][:200]}...")
                print(f"图片数量: {result['image_count']}")
                print(f"提取方法: {result['source']}")

            # 保存详细结果到文件
            with open(f'extraction_result_{len(results)}.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 避免请求过快
            time.sleep(2)

        except Exception as e:
            logger.error(f"处理URL {url} 时发生错误: {e}")
            results.append({'url': url, 'error': str(e)})

    # 关闭提取器
    extractor.close()

    # 打印统计信息
    successful = sum(1 for r in results if 'error' not in r)
    print(f"\n=== 统计 ===")
    print(f"总URL数: {len(test_urls)}")
    print(f"成功提取: {successful}")
    print(f"失败: {len(test_urls) - successful}")


if __name__ == "__main__":
    main()