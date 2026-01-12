from typing import Optional
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.syntax import Syntax
import logging
import os
from dotenv import load_dotenv
import asyncio
from pathlib import Path
import json
from documind.core.spider import DocSpider, fetch_multiple_urls
from documind.core.knowledge_base import DocuMindKnowledgeBase
from documind.core.graph import run_agent

# 加载环境变量
load_dotenv()

# 检查API密钥设置
if not (os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")):
    print("警告: 未检测到 DASHSCOPE_API_KEY (阿里云百炼) 或 OPENAI_API_KEY 环境变量")
    print("请在 .env 文件中设置您的API密钥")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)

app = typer.Typer(help="DocuMind - An Agentic RAG System for Document Intelligence")

console = Console()


def display_header():
    """显示项目标题和版本信息"""
    header = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ██████  ████     █████  ██             ║
    ║                   ██░░░░██ ░░██    ██░░░██░░              ║
    ║                  ██    ░░   ██   ░██  ░██ ██ ██████████   ║
    ║                 ░░█████   ░███  ░███████░██░░██░░██░░██  ║
    ║                  ░░░░░██  ░░██  ░██░░░░ ░██ ░██ ░██ ░██  ║
    ║                   ██████   ░██  ░██     ░██ ░██ ░██ ░██  ║
    ║                  ░░░░░░    ░░   ░░      ░░  ░░  ░░  ░░   ║
    ║                                                          ║
    ║                    Advanced RAG System                   ║
    ║                    v0.1.0                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(header, style="bold blue")
    console.print("\n[bold green]DocuMind[/bold green] - An Agentic RAG System for Document Intelligence")
    console.print("[italic]Making AI-powered document analysis accessible and efficient.[/italic]\n")


@app.command()
def crawl(
    url: str = typer.Argument(..., help="要爬取的网站URL"),
    output_dir: str = typer.Option("./data", "--output", "-o", help="输出目录路径"),
    max_pages: int = typer.Option(10, "--max-pages", "-m", help="最大爬取页面数")
):
    """
    爬取网页内容并保存到本地
    """
    console.print(f"[bold blue]开始爬取网站:[/bold blue] {url}")
    console.print(f"[bold green]输出目录:[/bold green] {output_dir}")
    console.print(f"[bold green]最大页面数:[/bold green] {max_pages}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]正在爬取网站...", total=100)
        
        async def run_crawl():
            async with DocSpider() as spider:
                progress.update(task, description="[cyan]初始化爬虫...")
                result = await spider.fetch(url)
                progress.update(task, completed=100)
                
                if result['success']:
                    console.print(f"\n[bold green]✓[/bold green] 成功爬取: {result['title']}")
                    
                    # 保存爬取结果
                    import json
                    from pathlib import Path
                    
                    # 确保输出目录存在
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    
                    # 生成文件名
                    safe_title = "".join(c for c in result['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    if not safe_title:
                        safe_title = "untitled"
                    
                    output_file = Path(output_dir) / f"{safe_title}.json"
                    
                    # 保存结果
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    console.print(f"[bold green]✓[/bold green] 结果已保存到: {output_file}")
                    
                    # 显示内容预览
                    content_preview = result['markdown'][:200] + "..." if len(result['markdown']) > 200 else result['markdown']
                    console.print(Panel.fit(content_preview, title="[bold]内容预览[/bold]", border_style="green"))
                else:
                    console.print(f"\n[bold red]✗[/bold red] 爬取失败: {result.get('error', 'Unknown error')}")
        
        # 运行异步爬取
        asyncio.run(run_crawl())


@app.command()
def index(
    input_dir: str = typer.Option("./data", "--input", "-i", help="输入数据目录"),
    collection_name: str = typer.Option("documents", "--collection", "-c", help="ChromaDB集合名称")
):
    """
    将文档索引到向量数据库
    """
    console.print(f"[bold blue]开始索引文档:[/bold blue]")
    console.print(f"[bold green]输入目录:[/bold green] {input_dir}")
    console.print(f"[bold green]集合名称:[/bold green] {collection_name}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        # 初始化知识库
        console.print("[cyan]正在初始化知识库...")
        kb = DocuMindKnowledgeBase(
            persist_directory="./.chroma_db",
            collection_name=collection_name
        )
        
        input_path = Path(input_dir)
        if not input_path.exists():
            console.print(f"[bold red]错误:[/bold red] 输入目录不存在: {input_dir}")
            return
        
        # 查找所有JSON文件（包含爬取结果）
        json_files = list(input_path.glob("*.json"))
        
        if not json_files:
            console.print(f"[bold yellow]警告:[/bold yellow] 在 {input_dir} 中未找到JSON文件")
            return
        
        console.print(f"[bold blue]找到 {len(json_files)} 个JSON文件[/bold blue]")
        
        task = progress.add_task("[cyan]正在索引文档...", total=len(json_files))
        
        success_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取markdown内容并添加到知识库
                markdown_content = data.get('markdown', '')
                if markdown_content:
                    metadata = {
                        'source_file': str(json_file),
                        'title': data.get('title', ''),
                        'url': data.get('url', ''),
                        'word_count': data.get('word_count', 0)
                    }
                    
                    if kb.add_document(markdown_content, metadata):
                        success_count += 1
                        console.print(f"[bold green]✓[/bold green] 已索引: {data.get('title', 'Unknown')}")
                    else:
                        console.print(f"[bold red]✗[/bold red] 索引失败: {json_file}")
                else:
                    console.print(f"[bold yellow]⚠[/bold yellow] 文件中没有markdown内容: {json_file}")
            
                progress.advance(task)
            except Exception as e:
                console.print(f"[bold red]✗[/bold red] 处理文件失败 {json_file}: {str(e)}")
                progress.advance(task)
        
        console.print(f"\n[bold blue]索引完成:[/bold blue] 成功 {success_count}/{len(json_files)}")
        console.print(f"[bold blue]文档总数:[/bold blue] {kb.get_document_count()}")


@app.command()
def query(
    question: str = typer.Argument(..., help="要查询的问题"),
    collection_name: str = typer.Option("documents", "--collection", "-c", help="ChromaDB集合名称")
):
    """
    查询已索引的文档
    """
    console.print(f"[bold blue]查询问题:[/bold blue] {question}")
    console.print(f"[bold green]集合名称:[/bold green] {collection_name}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]正在检索相关文档...", total=100)
        
        # 初始化知识库
        kb = DocuMindKnowledgeBase(
            persist_directory="./.chroma_db",
            collection_name=collection_name
        )
        
        # 搜索相关文档
        results = kb.search(question, k=5)
        
        progress.update(task, completed=100)
        
        if not results:
            console.print("\n[bold yellow]未找到相关文档。[/bold yellow]")
            return
        
        console.print(f"\n[bold blue]找到 {len(results)} 个相关文档片段:[/bold blue]")
        
        for i, result in enumerate(results, 1):
            console.print(f"\n[bold green]结果 {i}:[/bold green]")
            console.print(f"相似度分数: {result['similarity_score']:.3f}")
            
            # 显示内容预览
            content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
            console.print(Panel(content_preview, title=f"内容预览", border_style="blue"))
            
            if result['metadata']:
                console.print(f"元数据: {result['metadata']}")


@app.command()
def chat():
    """
    启动交互式聊天界面
    """
    console.print("[bold blue]启动DocuMind聊天界面...[/bold blue]")
    logger.info("聊天功能待实现")


@app.command()
def agent(
    task: str = typer.Argument(..., help="要执行的任务"),
    collection_name: str = typer.Option("documents", "--collection", "-c", help="ChromaDB集合名称"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="代码执行超时时间（秒）")
):
    """
    运行智能体来完成指定任务
    """
    console.print(f"[bold blue]任务:[/bold blue] {task}")
    console.print(f"[bold green]集合名称:[/bold green] {collection_name}")
    console.print(f"[bold green]超时时间:[/bold green] {timeout}秒")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            init_task = progress.add_task("[cyan]正在初始化知识库...", total=100)
            
            # 初始化知识库
            kb = DocuMindKnowledgeBase(
                persist_directory="./.chroma_db",
                collection_name=collection_name
            )
            
            progress.update(init_task, completed=100)
            
            agent_task = progress.add_task("[cyan]智能体正在处理任务...", total=100)
            
            console.print("[bold blue]正在运行智能体...[/bold blue]")
            
            # 运行智能体
            result = run_agent(task, kb, timeout=timeout)
            
            progress.update(agent_task, completed=100)
            
            console.print(f"\n[bold blue]执行完成![/bold blue]")
            console.print(f"[bold green]成功:[/bold green] {result['success']}")
            console.print(f"[bold green]迭代次数:[/bold green] {result['iteration']}")
            
            if result['error']:
                console.print(Panel(result['error'], title="[bold red]最终错误[/bold red]", border_style="red"))
            
            console.print(f"\n[bold blue]生成的代码:[/bold blue]")
            
            # 使用语法高亮显示代码
            syntax = Syntax(result['code'], "python", theme="monokai", line_numbers=True)
            console.print(syntax)
            
    except Exception as e:
        console.print(Panel(str(e), title="[bold red]智能体执行失败[/bold red]", border_style="red"))


@app.callback()
def main():
    """
    DocuMind - 基于Agent的RAG系统
    """
    display_header()


if __name__ == "__main__":
    app()