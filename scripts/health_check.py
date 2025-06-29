#!/usr/bin/env python3
"""
健康检查脚本
"""

import sys
import asyncio
import aiohttp
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import Config


async def check_health():
    """检查服务健康状态"""
    try:
        # 检查配置
        config = Config()
        config.validate()

        # 检查文件权限
        log_file = Path("data/logs/bot.log")
        if not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)

        # 检查Redis连接（如果启用）
        if os.getenv("REDIS_URL"):
            import aioredis
            try:
                redis = await aioredis.from_url(os.getenv("REDIS_URL"))
                await redis.ping()
                await redis.close()
            except Exception as e:
                print(f"❌ Redis连接失败: {e}")
                return False

        # 检查OpenAI API连接
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {config.API_KEY}"}
                async with session.get(
                        f"{config.API_BASE_URL}/models",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        print(f"❌ OpenAI API连接失败: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API连接检查失败: {e}")
            return False

        print("✅ 健康检查通过")
        return True

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(check_health())
    sys.exit(0 if result else 1)