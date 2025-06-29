"""
命令处理器
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode
from utils.decorators import rate_limit, log_user_action

logger = logging.getLogger(__name__)


class CommandHandlers:
    """命令处理器类"""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    def register_handlers(self, application):
        """注册命令处理器"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("settings", self.settings_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("admin", self.admin_command))

        logger.info("✅ 命令处理器已注册")

    @rate_limit
    @log_user_action
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        chat_type = update.effective_chat.type

        # 注册用户
        await self.bot.user_service.register_user(user)

        # 创建欢迎键盘
        keyboard = [
            [InlineKeyboardButton("🚀 开始聊天", callback_data="start_chat")],
            [
                InlineKeyboardButton("⚙️ 设置", callback_data="settings"),
                InlineKeyboardButton("📚 功能", callback_data="features")
            ],
            [InlineKeyboardButton("❓ 帮助", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
🎉 **欢迎使用 AI 助手！**

你好 {user.first_name}！我是一个多功能AI助手，可以帮你：

🤖 **智能对话** - 上下文记忆聊天
🗣️ **语音处理** - 语音转文字回复  
🖼️ **图片分析** - 识别图片内容
🌐 **多语翻译** - 支持多种语言
🧮 **数学计算** - 解决计算问题
📝 **文本处理** - 摘要、改写等

**使用方式:**
{'• 私聊：直接发消息即可' if chat_type == 'private' else '• 群组：@我 或回复我的消息'}

点击下方按钮开始体验！ 👇
        """

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @rate_limit
    @log_user_action
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        keyboard = [
            [
                InlineKeyboardButton("💬 聊天功能", callback_data="help_chat"),
                InlineKeyboardButton("🛠️ 工具功能", callback_data="help_tools")
            ],
            [
                InlineKeyboardButton("⚙️ 设置选项", callback_data="help_settings"),
                InlineKeyboardButton("❓ 常见问题", callback_data="help_faq")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        help_text = """
📖 **功能帮助中心**

选择下方分类查看详细说明：

• **聊天功能** - 对话交流相关
• **工具功能** - 实用工具介绍  
• **设置选项** - 个性化配置
• **常见问题** - 使用中的疑问
        """

        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @rate_limit
    @log_user_action
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /settings 命令"""
        user_id = update.effective_user.id
        user_data = await self.bot.user_service.get_user_data(user_id)

        keyboard = [
            [InlineKeyboardButton("🌍 语言设置", callback_data="setting_language")],
            [InlineKeyboardButton("🤖 聊天模式", callback_data="setting_mode")],
            [InlineKeyboardButton("🔔 通知设置", callback_data="setting_notifications")],
            [InlineKeyboardButton("🗑️ 清除数据", callback_data="setting_clear")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        settings_text = f"""
⚙️ **个人设置面板**

**当前配置:**
• 🌍 语言: {user_data.get('language', 'zh').upper()}
• 🤖 模式: {user_data.get('mode', 'chat').title()}
• 🔔 通知: {'开启' if user_data.get('notifications', True) else '关闭'}
• 📊 消息数: {user_data.get('total_messages', 0)}

选择要修改的设置项：
        """

        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @rate_limit
    @log_user_action
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /stats 命令"""
        user_id = update.effective_user.id
        stats = await self.bot.user_service.get_user_stats(user_id)

        stats_text = f"""
📊 **你的使用统计**

💬 **消息统计:**
• 总消息数: {stats.get('total_messages', 0)}
• 今日消息: {stats.get('today_messages', 0)}
• 本周消息: {stats.get('week_messages', 0)}

⭐ **用户信息:**
• 用户等级: {stats.get('level', 'Bronze')}
• 注册时间: {stats.get('join_date', 'Unknown')}
• 最后活跃: {stats.get('last_activity', 'Unknown')}

🏆 **成就徽章:** {stats.get('badges', '暂无')}
        """

        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    @log_user_action
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """管理员命令"""
        user_id = update.effective_user.id

        if not self.bot.is_admin(user_id):
            await update.message.reply_text("❌ 权限不足")
            return

        keyboard = [
            [
                InlineKeyboardButton("📊 系统状态", callback_data="admin_status"),
                InlineKeyboardButton("👥 用户统计", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📢 发送广播", callback_data="admin_broadcast"),
                InlineKeyboardButton("🔧 系统设置", callback_data="admin_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        admin_text = """
🔐 **管理员面板**

选择管理功能：
• **系统状态** - 查看运行状态
• **用户统计** - 用户数据分析
• **发送广播** - 群发消息
• **系统设置** - 修改配置
        """

        await update.message.reply_text(
            admin_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )