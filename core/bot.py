"""
Telegram AI 机器人核心类 - 增强版
"""

import logging
import asyncio
from telegram.ext import Application
from config.config import Config
from .handlers.commands import CommandHandlers
from .handlers.messages import MessageHandlers
from .handlers.callbacks import CallbackHandlers
from .handlers.media import MediaHandlers
from services.user_service import UserService
from services.system_monitor import SystemMonitor
from services.realtime_stats import RealTimeStatsManager

logger = logging.getLogger(__name__)

class TelegramAIBot:
    """Telegram AI 机器人主类 - 实时监控增强版"""

    def __init__(self):
        self.config = Config
        self.application = None
        self.bot_info = None

        # 初始化监控和统计服务
        self.system_monitor = SystemMonitor()
        self.stats_manager = RealTimeStatsManager()

        # 初始化其他服务
        self.user_service = UserService()

        # 初始化处理器
        self.command_handlers = CommandHandlers(self)
        self.message_handlers = MessageHandlers(self)
        self.callback_handlers = CallbackHandlers(self)
        self.media_handlers = MediaHandlers(self)

        logger.info("🤖 Telegram AI 机器人实例已创建")

    async def setup_bot_info(self, application):
        """设置机器人信息和初始化监控服务"""
        try:
            self.bot_info = await application.bot.get_me()
            logger.info(f"🤖 机器人信息: @{self.bot_info.username} ({self.bot_info.first_name})")

            # 初始化实时统计管理器
            await self.stats_manager.initialize()

            # 显示配置摘要
            logger.info(self.config.get_summary())

            # 启动后台任务
            asyncio.create_task(self._background_tasks())

            logger.info("✅ 机器人初始化完成，所有服务已启动")

        except Exception as e:
            logger.error(f"❌ 机器人初始化失败: {e}")
            raise

    async def _background_tasks(self):
        """后台任务"""
        while True:
            try:
                # 每小时清理一次过期数据
                await asyncio.sleep(3600)  # 1小时
                await self.stats_manager.cleanup_old_data()
                logger.info("🧹 定期清理任务完成")

            except Exception as e:
                logger.error(f"后台任务出错: {e}")
                await asyncio.sleep(300)  # 5分钟后重试

    def setup_handlers(self):
        """设置所有消息处理器"""
        # 命令处理器
        self.command_handlers.register_handlers(self.application)

        # 回调处理器
        self.callback_handlers.register_handlers(self.application)

        # 消息处理器
        self.message_handlers.register_handlers(self.application)

        # 媒体处理器
        self.media_handlers.register_handlers(self.application)

        logger.info("✅ 所有处理器已注册")

    async def start(self):
        """启动机器人"""
        try:
            # 创建应用
            self.application = (
                Application.builder()
                .token(self.config.TELEGRAM_TOKEN)
                .build()
            )

            # 设置机器人信息回调
            self.application.post_init = self.setup_bot_info

            # 注册处理器
            self.setup_handlers()

            # 启动轮询
            logger.info("🚀 开始轮询...")
            await self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"]
            )

        except Exception as e:
            logger.error(f"❌ 启动机器人失败: {e}")
            raise
        finally:
            # 清理资源
            await self._cleanup()

    async def _cleanup(self):
        """清理资源"""
        try:
            if self.stats_manager.redis:
                await self.stats_manager.redis.close()
            logger.info("🧹 资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

    def is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员"""
        return user_id in self.config.ADMIN_IDS

    def should_respond_in_group(self, update) -> bool:
        """判断在群组中是否应该响应"""
        if not self.bot_info:
            return False

        message = update.message
        if not message or not message.text:
            return False

        # 检查@机器人
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    if mention_text.lower() == f"@{self.bot_info.username.lower()}":
                        return True

        # 检查是否回复了机器人
        if (message.reply_to_message and
            message.reply_to_message.from_user and
            message.reply_to_message.from_user.id == self.bot_info.id):
            return True

        return False

    async def get_system_status_summary(self) -> str:
        """获取系统状态摘要"""
        try:
            system_stats = self.system_monitor.get_real_system_status()
            realtime_stats = await self.stats_manager.get_real_time_stats()

            return f"""
📊 **系统状态快照**

{system_stats.get('status_emoji', '🔍')} **服务状态:** {system_stats.get('status', '未知')}
💬 **今日消息:** {realtime_stats.get('today_messages', 0)}
👥 **在线用户:** {realtime_stats.get('online_users', 0)}
⚡ **响应时间:** {system_stats.get('avg_response_time', 0):.2f}秒
🔧 **运行时间:** {system_stats.get('uptime', '未知')}
            """.strip()

        except Exception as e:
            return f"❌ 获取状态摘要失败: {e}"