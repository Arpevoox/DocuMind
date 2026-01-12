"""
DocuMind 工具函数模块
提供通用的辅助功能
"""
import logging
from typing import Any, Dict, List, Optional
import os
from pathlib import Path
import json


logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """
    设置日志配置
    
    Args:
        level: 日志级别
    """
    from rich.logging import RichHandler
    import sys
    
    # 清除现有的处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 配置日志
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_path=True
            )
        ]
    )


def ensure_directory_exists(path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        是否成功确保目录存在
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"无法创建目录 {path}: {str(e)}")
        return False


def save_json(data: Any, filepath: str) -> bool:
    """
    将数据保存为JSON文件
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
        
    Returns:
        是否保存成功
    """
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到 {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败 {filepath}: {str(e)}")
        return False


def load_json(filepath: str) -> Optional[Any]:
    """
    从JSON文件加载数据
    
    Args:
        filepath: 文件路径
        
    Returns:
        加载的数据或None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"数据已从 {filepath} 加载")
        return data
    except Exception as e:
        logger.error(f"加载JSON文件失败 {filepath}: {str(e)}")
        return None


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    sanitized = filename
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 限制长度
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def format_bytes(bytes_value: int) -> str:
    """
    将字节数转换为可读格式
    
    Args:
        bytes_value: 字节数
        
    Returns:
        可读格式的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    合并两个字典，dict2中的值会覆盖dict1中的值
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    result.update(dict2)
    return result