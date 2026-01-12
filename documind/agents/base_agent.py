"""
DocuMind 基础Agent模块
定义Agent的基本接口和功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph
from ..utils.helpers import setup_logging


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    基础Agent抽象类
    定义了所有Agent都应该实现的基本方法
    """
    
    def __init__(self, 
                 name: str, 
                 llm: Optional[BaseLanguageModel] = None,
                 system_prompt: Optional[str] = None):
        """
        初始化基础Agent
        
        Args:
            name: Agent的名称
            llm: 语言模型实例
            system_prompt: 系统提示词
        """
        self.name = name
        self.system_prompt = system_prompt or f"You are {name}, a helpful AI assistant."
        
        # 如果没有提供LLM，尝试创建一个默认的
        if llm is None:
            import os
            if os.getenv("OPENAI_API_KEY"):
                self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
            else:
                raise ValueError("需要设置OPENAI_API_KEY环境变量或提供自定义LLM")
        else:
            self.llm = llm
        
        logger.info(f"Agent '{name}' 已初始化")
    
    @abstractmethod
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入并返回结果的抽象方法
        
        Args:
            inputs: 输入数据字典
            
        Returns:
            输出数据字典
        """
        pass
    
    def get_response(self, 
                     prompt: str, 
                     system_message: Optional[str] = None) -> str:
        """
        获取LLM的响应
        
        Args:
            prompt: 用户输入的提示
            system_message: 系统消息（可选）
            
        Returns:
            LLM的响应
        """
        messages = []
        
        # 添加系统消息
        sys_msg = system_message or self.system_prompt
        if sys_msg:
            messages.append(SystemMessage(content=sys_msg))
        
        # 添加用户消息
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"获取LLM响应时出错: {str(e)}")
            return f"错误: 无法获取响应 - {str(e)}"
    
    async def aget_response(self, 
                           prompt: str, 
                           system_message: Optional[str] = None) -> str:
        """
        异步获取LLM的响应
        
        Args:
            prompt: 用户输入的提示
            system_message: 系统消息（可选）
            
        Returns:
            LLM的响应
        """
        messages = []
        
        # 添加系统消息
        sys_msg = system_message or self.system_prompt
        if sys_msg:
            messages.append(SystemMessage(content=sys_msg))
        
        # 添加用户消息
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = await self.llm.ainvoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"异步获取LLM响应时出错: {str(e)}")
            return f"错误: 无法获取响应 - {str(e)}"
    
    def update_system_prompt(self, new_prompt: str) -> None:
        """
        更新系统提示词
        
        Args:
            new_prompt: 新的系统提示词
        """
        self.system_prompt = new_prompt
        logger.debug(f"Agent '{self.name}' 的系统提示词已更新")