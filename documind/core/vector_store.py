"""
DocuMind 向量存储模块
负责文档的向量索引和检索
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging


logger = logging.getLogger(__name__)


class DocuMindVectorStore:
    """
    DocuMind 向量存储类
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", 
                 collection_name: str = "documents"):
        """
        初始化向量存储
        
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # 使用默认的 OpenAI 嵌入函数（如果可用）或其他嵌入函数
        # 如果没有 OpenAI API 密钥，则使用 Sentence Transformer
        try:
            # 尝试使用 OpenAI 嵌入
            import os
            if os.getenv("OPENAI_API_KEY"):
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model_name="text-embedding-ada-002"
                )
            else:
                # 使用 Sentence Transformer 作为备选
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
        except ImportError:
            # 如果没有安装 openai 库，使用 Sentence Transformer
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档应包含 id, content, metadata
        """
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            ids.append(doc.get("id", str(hash(doc.get("content", "")))))
            texts.append(doc.get("content", ""))
            metadatas.append(doc.get("metadata", {}))
        
        if texts:  # 只有在有文本时才添加
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"成功添加 {len(texts)} 个文档到集合 {self.collection_name}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在向量存储中搜索相关文档
        
        Args:
            query: 查询字符串
            top_k: 返回最相似的文档数量
            
        Returns:
            包含匹配文档的列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # 重组结果格式
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else None
            })
        
        return formatted_results
    
    def delete_collection(self) -> None:
        """
        删除当前集合
        """
        self.client.delete_collection(self.collection_name)
        logger.info(f"已删除集合 {self.collection_name}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            包含集合统计信息的字典
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory
        }