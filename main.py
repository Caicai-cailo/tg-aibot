#!/usr/bin/env python3
"""
Telegram AI Bot - 主程序入口
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.bot import TelegramAIBot
from config.config import Config


# 配置日志
def setup_logging():
    """设置日志配置"""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, Config.LOG_LEVEL),
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        logger = logging.getLogger(__name__)

        # 验证配置
        Config.validate()
        logger.info("配置验证通过")

        # 创建并启动机器人
        bot = TelegramAIBot()
        logger.info("🚀 启动 Telegram AI 机器人...")
        await bot.start()

    except KeyboardInterrupt:
        logger.info("👋 机器人已停止")
    except Exception as e:
        logger.error(f"❌ 启动机器人时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())