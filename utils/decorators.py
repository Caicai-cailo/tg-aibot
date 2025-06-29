"""
装饰器工具
"""

import time
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# 速率限制存储
rate_limit_storage = defaultdict(list)

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """速率限制装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, update, context):
            user_id = update.effective_user.id
            current_time = time.time()

            # 清理过期的请求记录
            rate_limit_storage[user_id] = [
                req_time for req_time in rate_limit_storage[user_id]
                if current_time - req_time < window_seconds
            ]

            # 检查是否超过限制
            if len(rate_limit_storage[user_id]) >= max_requests:
                await update.message.reply_text(
                    f"⏰ 请求过于频繁，请等待 {window_seconds} 秒后重试"
                )
                return

            # 记录当前请求
            rate_limit_storage[user_id].append(current_time)

            return await func(self, update, context)
        return wrapper
    return decorator

def log_user_action(func):
    """用户行为记录装饰器"""
    @wraps(func)
    async def wrapper(self, update, context):
        user = update.effective_user
        chat_type = update.effective_chat.type
        action_name = func.__name__

        # 记录用户行为
        logger.info(f"👤 用户 {user.id} ({user.first_name}) 执行: {action_name}")

        return await func(self, update, context)
    return wrapper

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(self, update, context):
        start_time = time.time()
        error_occurred = False
        error_message = ""

        try:
            result = await func(self, update, context)
            return result
        except Exception as e:
            error_occurred = True
            error_message = str(e)
            logger.error(f"函数 {func.__name__} 执行出错: {e}")
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time

            # 记录到系统监控器
            if hasattr(self, 'bot') and hasattr(self.bot, 'system_monitor'):
                self.bot.system_monitor.record_request(
                    response_time,
                    error_occurred,
                    error_message
                )

            # 记录到实时统计
            if hasattr(self, 'bot') and hasattr(self.bot, 'stats_manager'):
                try:
                    await self.bot.stats_manager.update_user_activity(
                        update.effective_user.id,
                        func.__name__,
                        update.effective_chat.type
                    )
                except Exception as e:
                    logger.error(f"更新统计失败: {e}")

    return wrapper

def admin_required(func):
    """管理员权限装饰器"""
    @wraps(func)
    async def wrapper(self, update, context):
        user_id = update.effective_user.id

        if not hasattr(self, 'bot') or not self.bot.is_admin(user_id):
            await update.message.reply_text("❌ 权限不足，仅管理员可使用此功能")
            return

        return await func(self, update, context)
    return wrapper

def typing_action(func):
    """自动显示正在输入状态的装饰器"""
    @wraps(func)
    async def wrapper(self, update, context):
        # 显示正在输入状态
        chat_id = update.effective_chat.id

        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        except:
            pass  # 忽略发送状态失败

        return await func(self, update, context)
    return wrapper

def error_handler(func):
    """错误处理装饰器"""
    @wraps(func)
    async def wrapper(self, update, context):
        try:
            return await func(self, update, context)
        except Exception as e:
            logger.error(f"处理函数 {func.__name__} 时出错: {e}")

            error_messages = [
                "😅 出了点小问题，让我重新整理一下思路...",
                "🤔 系统有点忙，请稍后再试",
                "⚠️ 遇到了技术问题，正在修复中"
            ]

            import random
            try:
                await update.message.reply_text(random.choice(error_messages))
            except:
                pass  # 防止发送错误消息也失败

    return wrapper