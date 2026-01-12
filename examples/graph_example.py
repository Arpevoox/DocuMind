"""
DocuMind Graph 使用示例
"""
import os
from documind.core.knowledge_base import DocuMindKnowledgeBase
from documind.core.graph import run_agent


def example_simple_task():
    """简单任务示例"""
    print("=== 简单任务示例 ===")
    
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # 创建知识库实例
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="graph_example"
    )
    
    # 添加一些示例文档到知识库
    sample_docs = [
        {
            "content": """# Python数据分析
使用pandas进行数据分析的基本方法：
```python
import pandas as pd
df = pd.read_csv('data.csv')
print(df.head())
```
""",
            "metadata": {"topic": "data_analysis", "type": "pandas"}
        },
        {
            "content": """# Python文件操作
基本的文件读写操作：
```python
with open('file.txt', 'r') as f:
    content = f.read()
```
""",
            "metadata": {"topic": "file_operations", "type": "basic"}
        }
    ]
    
    for doc in sample_docs:
        kb.add_document(doc["content"], doc["metadata"])
    
    # 运行智能体执行简单任务
    task = "创建一个Python脚本来读取CSV文件并显示前5行"
    print(f"任务: {task}")
    
    result = run_agent(task, kb, timeout=30)
    
    print(f"执行成功: {result['success']}")
    print(f"迭代次数: {result['iteration']}")
    if result['error']:
        print(f"最终错误: {result['error']}")
    print(f"生成的代码:\n{result['code']}")
    

def example_complex_task():
    """复杂任务示例"""
    print("\n=== 复杂任务示例 ===")
    
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # 创建知识库实例
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="complex_example"
    )
    
    # 添加更复杂的示例文档
    kb.add_document("""# Web Scraping with Python
使用requests和BeautifulSoup进行网页抓取：
```python
import requests
from bs4 import BeautifulSoup

response = requests.get('https://example.com')
soup = BeautifulSoup(response.content, 'html.parser')
title = soup.find('title').text
```
注意事项：
- 总是要检查response的状态码
- 遵守robots.txt规则
- 添加适当的延迟避免过于频繁的请求
""", {"topic": "web_scraping", "level": "intermediate"})
    
    task = "编写一个程序来抓取网页标题并保存到文件"
    print(f"任务: {task}")
    
    result = run_agent(task, kb, timeout=30)
    
    print(f"执行成功: {result['success']}")
    if result['success']:
        print(f"生成的代码:\n{result['code']}")
    else:
        print(f"执行失败，最终错误: {result['error']}")
        print(f"尝试次数: {result['iteration']}")


def example_error_recovery():
    """错误恢复示例"""
    print("\n=== 错误恢复示例 ===")
    
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # 创建知识库实例
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="error_recovery_example"
    )
    
    # 添加关于常见错误和解决方案的文档
    kb.add_document("""# Python错误处理
常见的Python错误及解决方案：
- NameError: 尝试使用未定义的变量
- TypeError: 对象类型不支持特定操作
- ValueError: 传递给函数的参数类型正确但值不合适
- IndexError: 序列中没有此索引

错误处理最佳实践：
```python
try:
    # 可能出错的代码
    result = risky_operation()
except SpecificError as e:
    # 处理特定错误
    print(f"发生错误: {e}")
else:
    # 没有错误时执行
    print("操作成功")
finally:
    # 无论是否有错误都会执行
    cleanup()
```
""", {"topic": "error_handling", "type": "best_practices"})
    
    # 故意给出一个容易出错的任务
    task = "编写一个程序，从列表中随机选择元素，但要妥善处理可能出现的IndexError"
    print(f"任务: {task}")
    
    result = run_agent(task, kb, timeout=30)
    
    print(f"执行成功: {result['success']}")
    if result['success']:
        print(f"生成的代码:\n{result['code']}")
    else:
        print(f"最终未能解决问题，错误: {result['error']}")


if __name__ == "__main__":
    example_simple_task()
    example_complex_task()
    example_error_recovery()
    print("\nGraph示例执行完成！")