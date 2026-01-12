"""
DocuMind Spider 模块测试
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from documind.core.spider import DocSpider, fetch_single_url, fetch_multiple_urls


def test_docspider_initialization():
    """测试 DocSpider 初始化"""
    spider = DocSpider(max_retries=3, timeout=30)
    
    assert spider.max_retries == 3
    assert spider.timeout == 30
    assert spider._crawler is None


def test_async_operations():
    """测试异步操作"""
    async def run_tests():
        # 测试 fetch 方法（使用模拟）
        spider = DocSpider()
        
        # 模拟爬取结果
        mock_result = AsyncMock()
        mock_result.success = True
        mock_result.markdown = "# Test Title\n\nThis is test content."
        mock_result.title = "Test Page"
        mock_result.links = []
        mock_result.status_code = 200
        mock_result.metadata = {}
        mock_result.error = None
        
        with patch.object(spider, '_crawler') as mock_crawler:
            mock_crawler.arun = AsyncMock(return_value=mock_result)
            
            # 设置 _crawler 为非 None
            spider._crawler = mock_crawler
            
            result = await spider.fetch("https://example.com")
            
            assert result['success'] is True
            assert result['title'] == "Test Page"
            assert result['markdown'] == "# Test Title\n\nThis is test content."
            assert result['url'] == "https://example.com"
        
        # 测试 fetch 方法在失败时的行为
        spider_fail = DocSpider(max_retries=1)
        
        # 模拟失败的爬取结果
        mock_result_fail = AsyncMock()
        mock_result_fail.success = False
        mock_result_fail.error = "Connection error"
        
        with patch.object(spider_fail, '_crawler') as mock_crawler_fail:
            mock_crawler_fail.arun = AsyncMock(return_value=mock_result_fail)
            
            # 设置 _crawler 为非 None
            spider_fail._crawler = mock_crawler_fail
            
            result = await spider_fail.fetch("https://example.com")
            
            assert result['success'] is False
            assert result['error'] == "Connection error"
        
        # 测试 fetch_single_url 便捷函数
        with patch('documind.core.spider.DocSpider') as mock_spider_class:
            mock_spider_instance = AsyncMock()
            mock_spider_instance.__aenter__ = AsyncMock(return_value=mock_spider_instance)
            mock_spider_instance.__aexit__ = AsyncMock(return_value=None)
            mock_spider_instance.fetch = AsyncMock(return_value={
                'url': 'https://example.com',
                'title': 'Test',
                'markdown': '# Test',
                'success': True
            })
            
            mock_spider_class.return_value = mock_spider_instance
            
            result = await fetch_single_url('https://example.com')
            
            assert result['success'] is True
            assert result['url'] == 'https://example.com'
        
        # 测试 fetch_multiple_urls 便捷函数
        urls = ['https://example1.com', 'https://example2.com']
        
        with patch('documind.core.spider.DocSpider') as mock_spider_class:
            mock_spider_instance = AsyncMock()
            mock_spider_instance.__aenter__ = AsyncMock(return_value=mock_spider_instance)
            mock_spider_instance.__aexit__ = AsyncMock(return_value=None)
            mock_spider_instance.fetch = AsyncMock(side_effect=[
                {
                    'url': 'https://example1.com',
                    'title': 'Test 1',
                    'markdown': '# Test 1',
                    'success': True
                },
                {
                    'url': 'https://example2.com',
                    'title': 'Test 2',
                    'markdown': '# Test 2',
                    'success': True
                }
            ])
            
            mock_spider_class.return_value = mock_spider_instance
            
            results = await fetch_multiple_urls(urls)
            
            assert len(results) == 2
            assert all(r['success'] is True for r in results)
    
    # 运行异步测试
    asyncio.run(run_tests())


if __name__ == "__main__":
    test_docspider_initialization()
    test_async_operations()