"""
DocuMind 知识库模块
使用向量数据库进行文档存储和检索
"""
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.dashscope import DashScopeEmbeddings  # 阿里云百炼 embeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document


logger = logging.getLogger(__name__)


class DocuMindKnowledgeBase:
    """
    DocuMind 知识库类
    负责文档的结构化切分、向量化存储和检索
    """
    
    def __init__(self, 
                 persist_directory: str = "./.chroma_db", 
                 collection_name: str = "documents",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 100):
        """
        初始化知识库
        
        Args:
            persist_directory: Chroma数据库持久化目录
            collection_name: 集合名称
            chunk_size: 文档块大小
            chunk_overlap: 文档块重叠大小
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 确保持久化目录存在
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化嵌入模型
        try:
            # 优先检查阿里云百炼API密钥
            if os.getenv("DASHSCOPE_API_KEY"):
                # 使用阿里云百炼嵌入模型
                self.embeddings = DashScopeEmbeddings(
                    model="text-embedding-v1"
                )
            elif os.getenv("OPENAI_API_KEY"):
                # 备用：使用OpenAI嵌入模型
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-ada-002"
                )
            else:
                raise ValueError("需要设置 DASHSCOPE_API_KEY (阿里云百炼) 或 OPENAI_API_KEY 环境变量")
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {str(e)}")
            raise
        
        # 初始化向量数据库
        try:
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
            logger.info(f"知识库已连接到: {persist_directory}, 集合: {collection_name}")
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {str(e)}")
            raise
    
    def add_document(self, markdown_text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加文档到知识库
        
        Args:
            markdown_text: Markdown格式的文档文本
            metadata: 文档元数据
            
        Returns:
            添加是否成功
        """
        try:
            # 默认元数据
            if metadata is None:
                metadata = {}
            
            # 使用Markdown标题分割器按标题切分
            header_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "header_1"),
                    ("##", "header_2"),
                    ("###", "header_3"),
                ],
                strip_headers=False,
            )
            
            # 首次切分：按标题分割
            header_chunks = header_splitter.split_text(markdown_text)
            
            # 二次切分：对每个标题块使用递归字符切分器
            final_chunks = []
            for chunk in header_chunks:
                # 创建递归字符切分器
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    length_function=len,
                    is_separator_regex=False,
                )
                
                # 对当前块进行二次切分
                sub_chunks = text_splitter.split_text(chunk.page_content if hasattr(chunk, 'page_content') else str(chunk))
                
                # 创建Document对象
                for sub_chunk in sub_chunks:
                    document = Document(
                        page_content=sub_chunk,
                        metadata=metadata.copy()
                    )
                    # 添加源文档的标题信息到元数据
                    if hasattr(chunk, 'metadata'):
                        document.metadata.update(chunk.metadata)
                    
                    final_chunks.append(document)
            
            # 将文档添加到向量数据库
            if final_chunks:
                # 为每个文档生成唯一ID（这里使用内容哈希作为ID的基础）
                import hashlib
                ids = []
                for i, chunk in enumerate(final_chunks):
                    content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()
                    ids.append(f"{content_hash}_{i}")
                
                # 添加到向量数据库
                self.vector_store.add_documents(documents=final_chunks, ids=ids)
                
                logger.info(f"成功添加 {len(final_chunks)} 个文档块到知识库")
                return True
            else:
                logger.warning("没有找到有效的文档块进行添加")
                return False
                
        except Exception as e:
            logger.error(f"添加文档到知识库失败: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关文档片段
        
        Args:
            query: 查询字符串
            k: 返回的文档片段数量
            
        Returns:
            相关文档片段列表
        """
        try:
            # 执行相似性搜索
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k
            )
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': score  # 余弦相似度分数，越低越相似
                })
            
            logger.info(f"搜索完成，找到 {len(formatted_results)} 个相关文档片段")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []
    
    def delete_collection(self) -> bool:
        """
        删除整个集合
        
        Returns:
            删除是否成功
        """
        try:
            # Chroma中删除集合需要重新创建客户端
            import shutil
            collection_path = Path(self.persist_directory) / self.collection_name
            if collection_path.exists():
                shutil.rmtree(collection_path)
                logger.info(f"已删除集合: {self.collection_name}")
                return True
            else:
                logger.warning(f"集合路径不存在: {collection_path}")
                return True  # 如果不存在也算删除成功
        except Exception as e:
            logger.error(f"删除集合失败: {str(e)}")
            return False
    
    def get_document_count(self) -> int:
        """
        获取知识库中文档的数量
        
        Returns:
            文档数量
        """
        try:
            return self.vector_store._collection.count()
        except Exception as e:
            logger.error(f"获取文档数量失败: {str(e)}")
            return 0
    
    def update_document(self, old_content: str, new_content: str) -> bool:
        """
        更新文档（通过删除旧文档并添加新文档）
        
        Args:
            old_content: 旧文档内容
            new_content: 新文档内容
            
        Returns:
            更新是否成功
        """
        try:
            # 删除旧文档（基于内容）
            import hashlib
            old_content_hash = hashlib.md5(old_content.encode()).hexdigest()
            
            # 查找并删除具有相同内容哈希的文档
            # 注意：由于我们在添加时使用了带索引的ID，我们需要查找所有以该哈希开头的ID
            existing_docs = self.vector_store.get(where={"content_hash": old_content_hash})
            
            if existing_docs['ids']:
                self.vector_store._collection.delete(ids=existing_docs['ids'])
            
            # 添加新文档
            return self.add_document(new_content)
        except Exception as e:
            logger.error(f"更新文档失败: {str(e)}")
            return False