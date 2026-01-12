"""
DocuMind Knowledge Base 使用示例
"""
import os
from documind.core.knowledge_base import DocuMindKnowledgeBase


def example_basic_usage():
    """基本使用示例"""
    print("=== 知识库基本使用示例 ===")
    
    # 设置环境变量（实际使用时请在环境或 .env 文件中设置）
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # 创建知识库实例
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="example_docs"
    )
    
    # 示例Markdown文档
    sample_markdown = """
# Python编程入门

## 简介
Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。

## 基本语法
Python的基本语法非常简洁，易于学习。

### 变量
在Python中，变量不需要声明类型：
```python
x = 5
name = "Alice"
```

### 循环
Python支持for和while循环：
```python
for i in range(5):
    print(i)
```

## 高级特性
Python拥有许多高级特性，如列表推导式、装饰器等。

### 列表推导式
列表推导式是Python的一个强大特性：
```python
squares = [x**2 for x in range(10)]
```

### 装饰器
装饰器是Python的一个高级特性，用于修改函数行为。
"""
    
    # 添加文档到知识库
    success = kb.add_document(sample_markdown, {"source": "python_guide", "author": "example"})
    if success:
        print("✓ 文档已成功添加到知识库")
    else:
        print("✗ 添加文档失败")
    
    # 搜索相关文档
    print("\n--- 搜索结果 ---")
    results = kb.search("Python的变量定义", k=2)
    
    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"  内容预览: {result['content'][:100]}...")
        print(f"  相似度分数: {result['similarity_score']:.3f}")
        print(f"  元数据: {result['metadata']}")
        print()


def example_multiple_documents():
    """多文档处理示例"""
    print("=== 多文档处理示例 ===")
    
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="multi_docs"
    )
    
    # 多个文档
    documents = [
        {
            "content": """# 机器学习简介
机器学习是人工智能的一个分支，通过算法让计算机能够从数据中学习并做出决策或预测。
## 监督学习
监督学习使用标记的训练数据来学习映射函数。
## 无监督学习
无监督学习从无标记的数据中发现隐藏的结构。
""",
            "metadata": {"topic": "machine_learning", "level": "beginner"}
        },
        {
            "content": """# 深度学习基础
深度学习是机器学习的一个子集，使用多层神经网络进行学习。
## 神经网络
神经网络是模拟人脑神经元连接的计算模型。
## 反向传播
反向传播是训练神经网络的核心算法。
""",
            "metadata": {"topic": "deep_learning", "level": "intermediate"}
        }
    ]
    
    # 添加多个文档
    for i, doc in enumerate(documents):
        success = kb.add_document(doc["content"], doc["metadata"])
        print(f"文档 {i+1} 添加{'成功' if success else '失败'}")
    
    # 搜索
    print("\n--- 搜索'神经网络' ---")
    results = kb.search("什么是神经网络", k=3)
    
    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"  内容预览: {result['content'][:150]}...")
        print(f"  话题: {result['metadata'].get('topic', 'N/A')}")
        print()


def example_document_statistics():
    """文档统计示例"""
    print("=== 文档统计示例 ===")
    
    kb = DocuMindKnowledgeBase(
        persist_directory="./.chroma_db_example",
        collection_name="stats_docs"
    )
    
    # 添加一些文档
    kb.add_document("# 数据结构\n数据结构是计算机存储、组织数据的方式。", {"type": "data_structure"})
    kb.add_document("# 算法\n算法是解决特定问题的一系列步骤。", {"type": "algorithm"})
    
    # 获取统计信息
    count = kb.get_document_count()
    print(f"知识库中总共有 {count} 个文档块")


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_documents()
    example_document_statistics()
    print("\n知识库示例执行完成！")