from crawl4ai import AsyncWebCrawler
import asyncio

async def test():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url='https://httpbin.org/html')
        print('Available attributes:', [attr for attr in dir(result) if not attr.startswith('_')])
        print('Has title?', hasattr(result, 'title'))
        print('Has metadata?', hasattr(result, 'metadata'))
        print('Has markdown?', hasattr(result, 'markdown'))
        print('Has success?', hasattr(result, 'success'))
        print('Has error?', hasattr(result, 'error'))
        print('Has links?', hasattr(result, 'links'))
        print('Has status_code?', hasattr(result, 'status_code'))
        
        # 尝试访问这些属性
        print('Title:', getattr(result, 'title', 'No title attribute'))
        print('Metadata:', getattr(result, 'metadata', 'No metadata attribute'))
        print('Markdown (first 200 chars):', getattr(result, 'markdown', 'No markdown attribute')[:200])
        print('Success:', getattr(result, 'success', 'No success attribute'))
        print('Error:', getattr(result, 'error', 'No error attribute'))
        print('Links (first 5):', getattr(result, 'links', 'No links attribute')[:5])
        print('Status code:', getattr(result, 'status_code', 'No status_code attribute'))
        
        return result

res = asyncio.run(test())