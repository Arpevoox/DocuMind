"""
DocuMind 爬虫模块
使用 Crawl4AI 实现高质量的 Markdown 提取
"""
from typing import Dict, Any, Optional
import asyncio
import logging
import ssl
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator


logger = logging.getLogger(__name__)


class DocSpider:
    """
    DocSpider 类，用于自动化网页爬取和高质量 Markdown 提取
    """
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        """
        初始化 DocSpider
        
        Args:
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self._crawler: Optional[AsyncWebCrawler] = None
        
        # 配置爬虫运行参数
        self.config = CrawlerRunConfig(
            word_count_threshold=10,
            extraction_strategy=None,
            verbose=False
        )
        self.config.markdown_generator = DefaultMarkdownGenerator()
    
    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        self._crawler = AsyncWebCrawler()
        await self._crawler.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口，确保资源正确释放
        """
        if self._crawler:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch(self, url: str) -> Dict[str, Any]:
        """
        获取网页内容并提取 Markdown
        
        Args:
            url: 要爬取的网页URL
            
        Returns:
            包含 title, markdown 内容和页面链接的字典
        """
        if not self._crawler:
            raise RuntimeError("DocSpider 未正确初始化，请使用 async with 或手动调用 __aenter__")
        
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                logger.info(f"正在爬取 URL: {url} (尝试 {attempt + 1}/{self.max_retries})")
                
                # 执行爬取
                result = await self._crawler.arun(
                    url=url,
                    config=self.config,
                    bypass_cache=True
                )
                
                if result and result.success:
                    # 提取标题和内容
                    title = result.metadata.get('title', '') or urlparse(url).netloc
                    markdown_content = result.markdown
                    
                    # 过滤掉过短的内容
                    if len(markdown_content.strip()) < 50:
                        logger.warning(f"URL {url} 的内容太短，可能不是有效文档")
                    
                    result_dict = {
                        'url': url,
                        'title': title,
                        'markdown': markdown_content,
                        'success': True,
                        'links': result.links or [],
                        'status_code': result.status_code,
                        'word_count': len(markdown_content.split()),
                        'metadata': result.metadata or {}
                    }
                    
                    logger.info(f"成功爬取 URL: {url}")
                    return result_dict
                else:
                    error_msg = result.error if result else "未知错误"
                    logger.warning(f"爬取失败 (尝试 {attempt + 1}): {url}, 错误: {error_msg}")
                    last_error = error_msg
            
            except asyncio.TimeoutError:
                logger.warning(f"请求超时 (尝试 {attempt + 1}): {url}")
                last_error = "Timeout error"
            except ssl.SSLError as e:
                logger.error(f"SSL 证书错误: {url}, 错误: {str(e)}")
                last_error = f"SSL error: {str(e)}"
            except Exception as e:
                logger.error(f"爬取过程中发生错误 (尝试 {attempt + 1}): {url}, 错误: {str(e)}")
                last_error = str(e)
            
            attempt += 1
            if attempt < self.max_retries:
                # 指数退避策略
                wait_time = min(2 ** attempt, 10)  # 最多等待10秒
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        logger.error(f"爬取失败，已达到最大重试次数: {url}")
        return {
            'url': url,
            'title': '',
            'markdown': '',
            'success': False,
            'links': [],
            'status_code': None,
            'word_count': 0,
            'metadata': {},
            'error': last_error
        }


async def fetch_single_url(url: str, max_retries: int = 3, timeout: int = 30) -> Dict[str, Any]:
    """
    便捷函数：直接获取单个URL的内容
    
    Args:
        url: 要爬取的URL
        max_retries: 最大重试次数
        timeout: 超时时间
        
    Returns:
        包含爬取结果的字典
    """
    async with DocSpider(max_retries=max_retries, timeout=timeout) as spider:
        return await spider.fetch(url)


async def fetch_multiple_urls(urls: list[str], max_retries: int = 3, timeout: int = 30) -> list[Dict[str, Any]]:
    """
    便捷函数：批量获取多个URL的内容
    
    Args:
        urls: 要爬取的URL列表
        max_retries: 最大重试次数
        timeout: 超时时间
        
    Returns:
        包含多个爬取结果的列表
    """
    async with DocSpider(max_retries=max_retries, timeout=timeout) as spider:
        tasks = [spider.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理可能的异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'title': '',
                    'markdown': '',
                    'success': False,
                    'links': [],
                    'status_code': None,
                    'word_count': 0,
                    'metadata': {},
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results