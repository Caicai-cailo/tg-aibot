"""
配置管理模块
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""

    # =============================================================================
    # Telegram 配置
    # =============================================================================
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # =============================================================================
    # OpenAI API 配置
    # =============================================================================
    API_TYPE = os.getenv("API_TYPE", "openai")
    API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    API_KEY = os.getenv("API_KEY")
    MODEL = os.getenv("MODEL", "gpt-4")

    # =============================================================================
    # 功能开关
    # =============================================================================
    ENABLE_VOICE = os.getenv("ENABLE_VOICE", "true").lower() == "true"
    ENABLE_IMAGE = os.getenv("ENABLE_IMAGE", "true").lower() == "true"
    ENABLE_TRANSLATION = os.getenv("ENABLE_TRANSLATION", "true").lower() == "true"
    ENABLE_REACTIONS = os.getenv("ENABLE_REACTIONS", "true").lower() == "true"
    ENABLE_USER_PROFILES = os.getenv("ENABLE_USER_PROFILES", "true").lower() == "true"

    # =============================================================================
    # 性能配置
    # =============================================================================
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    SHOW_TYPING_DELAY = float(os.getenv("SHOW_TYPING_DELAY", "1.0"))
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))

    # =============================================================================
    # 速率限制
    # =============================================================================
    RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "20"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # =============================================================================
    # 管理员配置
    # =============================================================================
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
        if x.strip().isdigit()
    ]

    # =============================================================================
    # 日志配置
    # =============================================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "data/logs/bot.log")

    @classmethod
    def validate(cls):
        """验证必要的配置项"""
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("❌ TELEGRAM_TOKEN 未设置，请检查 .env 文件")

        if not cls.API_KEY:
            raise ValueError("❌ API_KEY 未设置，请检查 .env 文件")

        if cls.API_TYPE not in ["openai", "one-api", "new-api"]:
            raise ValueError(f"❌ 不支持的 API_TYPE: {cls.API_TYPE}")

        if not cls.API_BASE_URL.startswith(('http://', 'https://')):
            raise ValueError("❌ API_BASE_URL 格式无效")

    @classmethod
    def get_summary(cls) -> str:
        """获取配置摘要"""
        return f"""
📋 **配置摘要:**
• API类型: {cls.API_TYPE}
• 模型: {cls.MODEL}
• 语音功能: {'✅' if cls.ENABLE_VOICE else '❌'}
• 图片功能: {'✅' if cls.ENABLE_IMAGE else '❌'}
• 翻译功能: {'✅' if cls.ENABLE_TRANSLATION else '❌'}
• 管理员数量: {len(cls.ADMIN_IDS)}
        """.strip()