"""
辅助工具函数
"""

import re
from datetime import datetime
from typing import List


def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """智能分割长消息"""
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    # 按段落分割
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        if len(current_part) + len(paragraph) + 2 <= max_length:
            current_part += paragraph + '\n\n'
        else:
            if current_part:
                parts.append(current_part.strip())
                current_part = paragraph + '\n\n'
            else:
                # 段落太长，按句子分割
                sentences = re.split(r'[.!?。！？]', paragraph)
                for sentence in sentences:
                    if sentence.strip():
                        sentence_with_punct = sentence.strip() + '。'
                        if len(current_part) + len(sentence_with_punct) <= max_length:
                            current_part += sentence_with_punct
                        else:
                            if current_part:
                                parts.append(current_part.strip())
                            current_part = sentence_with_punct

    if current_part:
        parts.append(current_part.strip())

    return parts


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    now = datetime.now()
    diff = now - dt

    if diff.days == 0:
        if diff.seconds < 60:
            return "刚刚"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}分钟前"
        else:
            return f"{diff.seconds // 3600}小时前"
    elif diff.days == 1:
        return "昨天"
    elif diff.days < 7:
        return f"{diff.days}天前"
    else:
        return dt.strftime("%Y-%m-%d")


def escape_markdown(text: str) -> str:
    """转义Markdown特殊字符"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in escape_chars:
        text = text.replace(char, f'\\{char}')

    return text


def extract_command_args(text: str) -> tuple:
    """提取命令和参数"""
    parts = text.strip().split()
    if not parts:
        return None, []

    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    return command, args


def is_valid_url(url: str) -> bool:
    """验证URL格式"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None


def clean_text(text: str) -> str:
    """清理文本"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    text = text.strip()
    # 移除特殊控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix