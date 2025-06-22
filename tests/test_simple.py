# -*- coding: utf-8 -*-
"""
简单测试 - 验证测试基础设施
"""
import pytest


def test_basic_functionality():
    """测试基本功能"""
    assert 1 + 1 == 2


def test_string_operations():
    """测试字符串操作"""
    text = "Hello World"
    assert text.lower() == "hello world"
    assert len(text) == 11


@pytest.mark.utils
def test_list_operations():
    """测试列表操作"""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    assert max(test_list) == 5


def test_dict_operations():
    """测试字典操作"""
    test_dict = {'name': '测试', 'value': 100}
    assert test_dict['name'] == '测试'
    assert test_dict.get('value') == 100
    assert 'name' in test_dict