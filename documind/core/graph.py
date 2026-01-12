"""
DocuMind Graph 模块
使用 LangGraph 构建智能体工作流
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi  # 阿里云通义千问
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import subprocess
import tempfile
import os
import signal
import logging
import sys
import time
from pathlib import Path
import os  # 添加缺失的os import用于检测环境变量

from ..core.knowledge_base import DocuMindKnowledgeBase


logger = logging.getLogger(__name__)


class AgentOutput(BaseModel):
    """智能体节点输出基类"""
    pass


class ResearcherOutput(AgentOutput):
    """研究员节点输出"""
    context: List[Dict[str, Any]] = Field(description="检索到的相关上下文")
    sources: List[str] = Field(description="信息来源")


class CoderOutput(AgentOutput):
    """编码器节点输出"""
    code: str = Field(description="生成的Python代码")
    explanation: str = Field(description="代码说明")


class ExecutorOutput(AgentOutput):
    """执行器节点输出"""
    success: bool = Field(description="执行是否成功")
    output: str = Field(description="执行输出")
    error: Optional[str] = Field(description="错误信息")
    execution_time: float = Field(description="执行时间")


class AgentState(TypedDict):
    """
    智能体状态定义
    """
    task: str  # 当前任务描述
    context: List[Dict[str, Any]]  # 检索到的上下文
    code: str  # 生成的代码
    error: Optional[str]  # 错误信息
    iteration: int  # 当前迭代次数
    success: bool  # 是否成功完成
    sources: List[str]  # 上下文来源


def researcher_node(state: AgentState, knowledge_base: DocuMindKnowledgeBase) -> Dict[str, Any]:
    """
    研究员节点：从知识库检索上下文
    """
    logger.info(f"研究员节点：检索与任务相关的上下文 - {state['task'][:50]}...")
    
    # 从知识库搜索相关信息
    search_results = knowledge_base.search(state["task"], k=5)
    
    context_list = []
    sources = []
    
    for result in search_results:
        context_list.append({
            "content": result["content"],
            "metadata": result["metadata"],
            "similarity_score": result["similarity_score"]
        })
        # 记录来源
        source = result["metadata"].get("source_file", "unknown")
        if source not in sources:
            sources.append(source)
    
    output = ResearcherOutput(
        context=context_list,
        sources=sources
    )
    
    logger.info(f"研究员节点：检索到 {len(context_list)} 个相关上下文片段")
    
    return {
        "context": output.context,
        "sources": output.sources
    }


def coder_node(state: AgentState) -> Dict[str, Any]:
    """
    编码器节点：根据上下文生成Python代码
    """
    logger.info(f"编码器节点：为任务生成代码 - {state['task'][:50]}...")
    
    # 准备上下文信息
    context_str = "\n".join([item["content"] for item in state["context"][:3]])  # 只取前3个上下文
    
    # 准备系统提示词
    system_prompt = """你是一个专业的Python程序员，负责根据给定的任务和上下文生成高质量的Python代码。
你的代码应该：
1. 功能完整且正确
2. 包含适当的错误处理
3. 包含简明的注释
4. 符合Python最佳实践
5. 如果遇到错误，考虑之前的错误信息并修复

请只输出Python代码，不要有任何其他解释性文字。"""
    
    # 准备用户提示词
    user_prompt = f"""任务: {state['task']}
    
相关上下文:
{context_str}

"""
    
    # 如果有之前的错误，也要包含进去
    if state.get("error"):
        user_prompt += f"""
之前执行的代码遇到了以下错误:
{state['error']}

请修复此错误并重新生成代码。
"""
    
    # 初始化语言模型
    # 优先使用阿里云通义千问，否则使用OpenAI
    if os.getenv("DASHSCOPE_API_KEY"):
        llm = ChatTongyi(
            model_name="qwen-max"  # 或其他支持的模型
        )
    else:
        llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    try:
        # 生成代码
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        generated_code = response.content
        
        # 清理代码（移除可能的markdown标记）
        if generated_code.startswith("```python"):
            generated_code = generated_code[11:]  # 移除 ```python
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]  # 移除 ```
        
        output = CoderOutput(
            code=generated_code.strip(),
            explanation="Generated code based on task and context"
        )
        
        logger.info("编码器节点：代码生成完成")
        
        return {
            "code": output.code,
            "error": None  # 重置错误信息
        }
    except Exception as e:
        logger.error(f"编码器节点：代码生成失败 - {str(e)}")
        return {
            "error": f"代码生成失败: {str(e)}"
        }


def executor_node(state: AgentState, timeout: int = 30) -> Dict[str, Any]:
    """
    执行器节点：在子进程中运行代码并捕获错误
    """
    logger.info(f"执行器节点：执行生成的代码 (迭代 {state['iteration']})")
    
    code = state["code"]
    
    # 创建临时文件并在子进程中运行
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    
    try:
        start_time = time.time()
        
        # 使用subprocess运行代码，设置超时
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        # 检查执行结果
        if result.returncode == 0:
            # 执行成功
            output = ExecutorOutput(
                success=True,
                output=result.stdout,
                error=None,
                execution_time=execution_time
            )
            
            logger.info(f"执行器节点：代码执行成功，耗时 {execution_time:.2f}s")
            
            return {
                "success": True,
                "error": None,
                "code": state["code"]  # 保留成功的代码
            }
        else:
            # 执行失败
            error_msg = result.stderr
            output = ExecutorOutput(
                success=False,
                output=result.stdout,
                error=error_msg,
                execution_time=execution_time
            )
            
            logger.warning(f"执行器节点：代码执行失败\n错误: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "code": state["code"]  # 保留失败的代码供修复
            }
    
    except subprocess.TimeoutExpired:
        # 执行超时
        execution_time = time.time() - start_time
        
        logger.warning(f"执行器节点：代码执行超时 ({timeout}s)")
        
        return {
            "success": False,
            "error": f"代码执行超时 ({timeout}秒)",
            "code": state["code"]
        }
    
    except Exception as e:
        # 其他执行错误
        logger.error(f"执行器节点：执行过程中出现异常 - {str(e)}")
        
        return {
            "success": False,
            "error": f"执行异常: {str(e)}",
            "code": state["code"]
        }
    
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass  # 忽略删除临时文件时的错误


def should_continue(state: AgentState) -> str:
    """
    条件边：决定下一步操作
    """
    # 如果成功或者迭代次数超过限制，则结束
    if state["success"] or state["iteration"] >= 3:
        return "end"
    else:
        # 如果有错误，继续修复
        return "continue"


def build_agent_graph(knowledge_base: DocuMindKnowledgeBase, timeout: int = 30) -> StateGraph:
    """
    构建智能体工作流图
    """
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("researcher", lambda state: researcher_node(state, knowledge_base))
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", lambda state: executor_node(state, timeout))
    
    # 设置入口点
    workflow.set_entry_point("researcher")
    
    # 添加边
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", "executor")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {
            "end": "__end__",
            "continue": "coder"
        }
    )
    
    # 编译图
    app = workflow.compile()
    
    return app


def run_agent(task: str, knowledge_base: DocuMindKnowledgeBase, timeout: int = 30) -> AgentState:
    """
    运行智能体来完成指定任务
    """
    logger.info(f"开始运行智能体，任务: {task}")
    
    # 初始化状态
    initial_state = {
        "task": task,
        "context": [],
        "code": "",
        "error": None,
        "iteration": 0,
        "success": False,
        "sources": []
    }
    
    # 构建图
    app = build_agent_graph(knowledge_base, timeout)
    
    # 执行图
    final_state = app.invoke(initial_state)
    
    logger.info(f"智能体执行完成，成功: {final_state['success']}")
    
    return final_state