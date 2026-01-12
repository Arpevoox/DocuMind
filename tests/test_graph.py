"""
DocuMind Graph 模块测试
"""
import pytest
from unittest.mock import Mock, patch
from documind.core.graph import (
    AgentState, researcher_node, coder_node, executor_node, 
    should_continue, build_agent_graph, run_agent
)
from documind.core.knowledge_base import DocuMindKnowledgeBase


def test_agent_state():
    """测试智能体状态结构"""
    state: AgentState = {
        "task": "Test task",
        "context": [],
        "code": "print('hello')",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    assert state["task"] == "Test task"
    assert state["code"] == "print('hello')"
    assert state["error"] is None


@patch('documind.core.knowledge_base.DocuMindKnowledgeBase')
def test_researcher_node(mock_kb):
    """测试研究员节点"""
    # 设置模拟知识库的返回值
    mock_kb.search.return_value = [
        {
            "content": "Test context content",
            "metadata": {"source_file": "test_source.txt"},
            "similarity_score": 0.8
        }
    ]
    
    state = {
        "task": "Find information about Python",
        "context": [],
        "code": "",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    result = researcher_node(state, mock_kb)
    
    assert "context" in result
    assert "sources" in result
    assert len(result["context"]) == 1
    assert result["sources"] == ["test_source.txt"]


@patch('documind.core.graph.ChatOpenAI')
def test_coder_node_success(mock_llm_class):
    """测试编码器节点成功情况"""
    # 模拟LLM返回值
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = Mock()
    mock_llm_instance.invoke.return_value.content = "print('Hello World')"
    mock_llm_class.return_value = mock_llm_instance
    
    state = {
        "task": "Create a hello world program",
        "context": [{"content": "Python basics", "metadata": {}, "similarity_score": 0.5}],
        "code": "",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    result = coder_node(state)
    
    assert "code" in result
    assert result["code"] == "print('Hello World')"
    assert "error" in result
    assert result["error"] is None


def test_executor_node_success():
    """测试执行器节点成功情况"""
    state = {
        "task": "Test task",
        "context": [],
        "code": "print('Success')",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    result = executor_node(state, timeout=10)
    
    assert "success" in result
    assert result["success"] is True
    assert "error" in result
    assert result["error"] is None


def test_executor_node_failure():
    """测试执行器节点失败情况"""
    state = {
        "task": "Test task",
        "context": [],
        "code": "raise ValueError('Test error')",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    result = executor_node(state, timeout=10)
    
    assert "success" in result
    assert result["success"] is False
    assert "error" in result
    assert result["error"] is not None
    assert "Test error" in result["error"]


def test_should_continue():
    """测试条件判断函数"""
    # 测试成功情况
    state_success = {
        "success": True,
        "iteration": 1
    }
    assert should_continue(state_success) == "end"
    
    # 测试达到最大迭代次数
    state_max_iter = {
        "success": False,
        "iteration": 3
    }
    assert should_continue(state_max_iter) == "end"
    
    # 测试需要继续的情况
    state_continue = {
        "success": False,
        "iteration": 1
    }
    assert should_continue(state_continue) == "continue"


if __name__ == "__main__":
    test_agent_state()
    test_researcher_node(Mock())
    test_coder_node_success(Mock())
    test_executor_node_success()
    test_executor_node_failure()
    test_should_continue()
    print("所有测试通过！")