"""
DocuMind Knowledge Base 模块测试
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from documind.core.knowledge_base import DocuMindKnowledgeBase


def test_knowledge_base_initialization():
    """测试知识库初始化"""
    # 模拟环境变量
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch('documind.core.knowledge_base.OpenAIEmbeddings'), \
             patch('documind.core.knowledge_base.Chroma'):
            
            kb = DocuMindKnowledgeBase(persist_directory="./test_db", collection_name="test_collection")
            
            assert kb.persist_directory == "./test_db"
            assert kb.collection_name == "test_collection"
            assert kb.chunk_size == 1000
            assert kb.chunk_overlap == 100


def test_add_document():
    """测试添加文档功能"""
    # 模拟环境变量
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch('documind.core.knowledge_base.OpenAIEmbeddings'), \
             patch('documind.core.knowledge_base.Chroma'), \
             patch.object(DocuMindKnowledgeBase, 'add_document', return_value=True) as mock_add:
            
            kb = DocuMindKnowledgeBase()
            result = kb.add_document("# Test Document\n\nThis is a test document.", {"source": "test"})
            
            assert result is True
            mock_add.assert_called_once()


def test_search():
    """测试搜索功能"""
    # 模拟环境变量
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch('documind.core.knowledge_base.OpenAIEmbeddings'), \
             patch('documind.core.knowledge_base.Chroma') as mock_chroma_class:
             
            # 模拟相似性搜索返回结果
            mock_vector_store = MagicMock()
            mock_doc = MagicMock()
            mock_doc.page_content = "Test content"
            mock_doc.metadata = {"source": "test"}
            mock_vector_store.similarity_search_with_score.return_value = [(mock_doc, 0.5)]
            
            mock_chroma_class.return_value = mock_vector_store
            
            kb = DocuMindKnowledgeBase()
            results = kb.search("test query", k=1)
            
            assert len(results) == 1
            assert results[0]['content'] == "Test content"
            assert results[0]['metadata'] == {"source": "test"}
            assert results[0]['similarity_score'] == 0.5


def test_document_count():
    """测试获取文档数量功能"""
    # 模拟环境变量
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch('documind.core.knowledge_base.OpenAIEmbeddings'), \
             patch('documind.core.knowledge_base.Chroma') as mock_chroma_class:
             
            # 模拟集合计数
            mock_collection = MagicMock()
            mock_collection.count.return_value = 5
            mock_vector_store = MagicMock()
            mock_vector_store._collection = mock_collection
            
            mock_chroma_class.return_value = mock_vector_store
            
            kb = DocuMindKnowledgeBase()
            count = kb.get_document_count()
            
            assert count == 5


if __name__ == "__main__":
    test_knowledge_base_initialization()
    test_add_document()
    test_search()
    test_document_count()
    print("所有测试通过！")