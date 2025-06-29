"""
OpenAI API 服务
"""

import logging
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from config.config import Config

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI API 服务类"""

    def __init__(self):
        self.config = Config
        self.session = None
        self.base_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.API_KEY}"
        }

    async def get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(
                headers=self.base_headers,
                timeout=timeout
            )
        return self.session

    async def close_session(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个友好、专业的AI助手。请遵循以下回复风格:

1. 用清晰的结构组织回答
2. 重要信息用**加粗**标记
3. 使用适当的表情符号增强表达
4. 保持回答简洁而有用
5. 如果不确定，诚实地说明
6. 根据上下文调整回复风格

请始终以用户为中心，提供有价值的帮助。"""

    async def make_api_request(self, messages: list) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.config.API_BASE_URL}/chat/completions"

        data = {
            "model": self.config.MODEL,
            "messages": messages,
            "max_tokens": self.config.MAX_TOKENS,
            "temperature": self.config.TEMPERATURE
        }

        session = await self.get_session()

        for attempt in range(self.config.MAX_RETRIES):
            try:
                async with session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientTimeout:
                logger.warning(f"API请求超时 (尝试 {attempt + 1}/{self.config.MAX_RETRIES})")
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise Exception("API请求超时，请稍后重试")

            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # 速率限制
                    logger.warning(f"API速率限制 (尝试 {attempt + 1}/{self.config.MAX_RETRIES})")
                    if attempt < self.config.MAX_RETRIES - 1:
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                raise Exception(f"API错误: {e.status}")

            except Exception as e:
                logger.error(f"请求错误 (尝试 {attempt + 1}/{self.config.MAX_RETRIES}): {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise Exception(f"网络错误: {e}")

        raise Exception("API请求失败，已达到最大重试次数")

    async def get_chat_response(self, user_message: str, context: Optional[str] = None) -> str:
        """获取聊天回复"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]

            # 添加上下文
            if context:
                messages.append({"role": "user", "content": context})
            else:
                messages.append({"role": "user", "content": user_message})

            # 发送请求
            response_data = await self.make_api_request(messages)

            # 解析响应
            if self.config.API_TYPE in ["openai", "one-api", "new-api"]:
                raw_response = response_data["choices"][0]["message"]["content"]
                return self.format_response(raw_response)
            else:
                logger.error(f"不支持的API类型: {self.config.API_TYPE}")
                return "抱歉，配置错误。请联系管理员。"

        except Exception as e:
            logger.error(f"获取AI响应时出错: {e}")
            raise Exception(f"AI服务暂时不可用: {str(e)}")

    def format_response(self, text: str) -> str:
        """格式化响应文本"""
        if not text:
            return ""

        import re

        # 格式化规则
        patterns = [
            # 二级标题转为粗体
            (re.compile(r'^#{2,} (.+)$', re.MULTILINE), r'**\1**'),
            # 列表项
            (re.compile(r'^- (.+)$', re.MULTILINE), r'• \1'),
            # HTML标签转Markdown
            (re.compile(r'<b>(.+?)</b>'), r'**\1**'),
            (re.compile(r'<i>(.+?)</i>'), r'_\1_'),
            # 清理多余空行
            (re.compile(r'\n{3,}'), r'\n\n')
        ]

        for pattern, replacement in patterns:
            text = pattern.sub(replacement, text)

        return text.strip()

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            test_response = await self.get_chat_response("Hello")
            return bool(test_response)
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False

    def __del__(self):
        """析构函数"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.close_session())