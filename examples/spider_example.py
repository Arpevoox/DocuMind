"""
DocuMind Spider 使用示例
"""
import asyncio
import json
from pathlib import Path
from documind.core.spider import DocSpider, fetch_single_url, fetch_multiple_urls


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    async with DocSpider() as spider:
        # 爬取单个URL
        result = await spider.fetch("https://www.python.org")
        
        if result['success']:
            print(f"标题: {result['title']}")
            print(f"字数: {result['word_count']}")
            print(f"链接数: {len(result['links'])}")
            print(f"Markdown 内容预览 (前500字符):")
            print(result['markdown'][:500] + "..." if len(result['markdown']) > 500 else result['markdown'])
        else:
            print(f"爬取失败: {result['error']}")


async def example_batch_crawling():
    """批量爬取示例"""
    print("\n=== 批量爬取示例 ===")
    
    urls = [
        "https://docs.python.org/3/",
        "https://fastapi.tiangolo.com/",
        "https://docs.langchain.com/docs/"
    ]
    
    results = await fetch_multiple_urls(urls, max_retries=2)
    
    for result in results:
        if result['success']:
            print(f"✓ {result['title']} ({result['word_count']} 字)")
        else:
            print(f"✗ {result['url']} - {result['error']}")


async def example_save_results():
    """保存结果示例"""
    print("\n=== 保存结果示例 ===")
    
    async with DocSpider() as spider:
        result = await spider.fetch("https://realpython.com/")
        
        if result['success']:
            # 确保目录存在
            output_dir = Path("./output")
            output_dir.mkdir(exist_ok=True)
            
            # 生成安全的文件名
            safe_title = "".join(c for c in result['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title:
                safe_title = "untitled"
            
            # 保存完整的爬取结果
            output_file = output_dir / f"{safe_title}_full.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 仅保存 Markdown 内容
            md_file = output_dir / f"{safe_title}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(result['markdown'])
            
            print(f"结果已保存到 {output_file} 和 {md_file}")


async def main():
    """主函数"""
    await example_basic_usage()
    await example_batch_crawling()
    await example_save_results()


if __name__ == "__main__":
    asyncio.run(main())