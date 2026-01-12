"""
DocuMind 主模块测试
"""
import pytest
from typer.testing import CliRunner
from documind.main import app


runner = CliRunner()


def test_app_initialization():
    """测试应用初始化"""
    assert app is not None
    assert app.info.name == "main"


def test_crawl_command_help():
    """测试crawl命令的帮助信息"""
    result = runner.invoke(app, ["crawl", "--help"])
    assert result.exit_code == 0
    assert "要爬取的网站URL" in result.output


def test_index_command_help():
    """测试index命令的帮助信息"""
    result = runner.invoke(app, ["index", "--help"])
    assert result.exit_code == 0
    assert "输入数据目录" in result.output


def test_query_command_help():
    """测试query命令的帮助信息"""
    result = runner.invoke(app, ["query", "--help"])
    assert result.exit_code == 0
    assert "要查询的问题" in result.output


def test_chat_command_help():
    """测试chat命令的帮助信息"""
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code == 0
    assert "启动交互式聊天界面" in result.output