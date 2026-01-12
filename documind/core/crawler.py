"""
DocuMind 爬虫模块
负责网页内容的抓取和解析
"""
from typing import List, Dict, Any, Optional
import asyncio
from crawl4ai import AsyncWebCrawler


class DocuMindCrawler:
    """
    DocuMind 网页爬虫类
    """
    
    def __init__(self, max_concurrent_requests: int = 5):
        self.max_concurrent_requests = max_concurrent_requests
    
    async def crawl_single_url(self, url: str) -> Dict[str, Any]:
        """
        爬取单个URL的内容
        
        Args:
            url: 要爬取的URL
            
        Returns:
            包含爬取结果的字典
        """
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                
                if result and result.success:
                    return {
                        "url": url,
                        "success": True,
                        "content": result.markdown,
                        "metadata": {
                            "title": result.title,
                            "description": result.description,
                            "links": result.links,
                        }
                    }
                else:
                    return {
                        "url": url,
                        "success": False,
                        "error": f"Crawling failed for {url}",
                        "content": "",
                        "metadata": {}
                    }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "content": "",
                "metadata": {}
            }
    
    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量爬取多个URL的内容
        
        Args:
            urls: 要爬取的URL列表
            
        Returns:
            包含爬取结果的字典列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl_single_url(url)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理可能的异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "success": False,
                    "error": str(result),
                    "content": "",
                    "metadata": {}
                })
            else:
                processed_results.append(result)
        
        return processed_results