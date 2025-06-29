"""
回调处理器
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """回调处理器类"""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    def register_handlers(self, application):
        """注册回调处理器"""
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        logger.info("✅ 回调处理器已注册")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理所有回调查询"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        try:
            # 根据回调数据路由到相应处理函数
            if data == "start_chat":
                await self.handle_start_chat(query)
            elif data == "settings":
                await self.handle_settings(query)
            elif data == "features":
                await self.handle_features(query)
            elif data == "help":
                await self.handle_help_menu(query)
            elif data.startswith("help_"):
                await self.handle_help_category(query, data.split("_", 1)[1])
            elif data.startswith("setting_"):
                await self.handle_setting_option(query, data.split("_", 1)[1])
            elif data.startswith("admin_"):
                await self.handle_admin_action(query, data.split("_", 1)[1])
            else:
                await query.edit_message_text("❓ 未知的操作")

        except Exception as e:
            logger.error(f"处理回调出错: {e}")
            await query.edit_message_text("❌ 处理请求时出现错误")

    async def handle_start_chat(self, query):
        """处理开始聊天"""
        text = """
🚀 **对话模式已启动！**

现在你可以：
• 💬 直接发送文字消息聊天
• 🗣️ 发送语音消息（自动转文字）
• 🖼️ 发送图片让我分析内容
• 🧮 进行数学计算
• 🌐 请求翻译服务

**特殊命令:**
• `翻译: 内容` - 翻译文本
• `计算: 1+1` - 数学计算
• `/help` - 查看帮助

开始聊天吧！有什么想聊的？ 😊
        """

        keyboard = [[InlineKeyboardButton("« 返回主菜单", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_settings(self, query):
        """处理设置菜单"""
        user_id = query.from_user.id
        user_data = await self.bot.user_service.get_user_data(user_id)

        keyboard = [
            [InlineKeyboardButton("🌍 语言设置", callback_data="setting_language")],
            [InlineKeyboardButton("🤖 聊天模式", callback_data="setting_mode")],
            [InlineKeyboardButton("🔔 通知设置", callback_data="setting_notifications")],
            [InlineKeyboardButton("📊 数据管理", callback_data="setting_data")],
            [InlineKeyboardButton("« 返回", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        settings_text = f"""
⚙️ **个人设置**

**当前配置:**
• 🌍 语言: {user_data.get('language', 'zh').upper()}
• 🤖 模式: {user_data.get('mode', 'chat').title()}
• 🔔 通知: {'开启' if user_data.get('notifications', True) else '关闭'}
• 📊 消息数: {user_data.get('total_messages', 0)}

选择要修改的设置项：
        """

        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_features(self, query):
        """处理功能介绍"""
        features_text = """
🌟 **功能特色展示**

**💬 智能对话**
• 🧠 上下文记忆对话
• 🎭 多种聊天风格
• 🔄 连续对话支持

**🛠️ 实用工具**
• 🗣️ 语音消息处理
• 🖼️ 图片内容识别  
• 🌐 多语言翻译
• 🧮 数学计算器
• 📝 文本处理工具

**🎨 创意功能**
• ✍️ 创意写作
• 🎵 诗歌创作
• 💡 头脑风暴
• 🤖 代码生成

**⚙️ 个性化**
• 👤 用户偏好记忆
• 📊 使用统计分析
• 🏆 成就系统
• ⭐ 等级进阶

**🔐 隐私安全**
• 🛡️ 数据加密存储
• 🔒 隐私信息保护
• 🗑️ 数据清除选项
        """

        keyboard = [[InlineKeyboardButton("« 返回主菜单", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            features_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_help_menu(self, query):
        """处理帮助菜单"""
        keyboard = [
            [
                InlineKeyboardButton("💬 聊天功能", callback_data="help_chat"),
                InlineKeyboardButton("🛠️ 工具功能", callback_data="help_tools")
            ],
            [
                InlineKeyboardButton("⚙️ 设置帮助", callback_data="help_settings"),
                InlineKeyboardButton("❓ 常见问题", callback_data="help_faq")
            ],
            [InlineKeyboardButton("« 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        help_text = """
📖 **帮助中心**

选择你需要了解的功能分类：

• **💬 聊天功能** - 对话交流相关
• **🛠️ 工具功能** - 实用工具使用
• **⚙️ 设置帮助** - 个性化配置
• **❓ 常见问题** - 疑问解答
        """

        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_help_category(self, query, category: str):
        """处理帮助分类"""
        help_content = {
            "chat": """
💬 **聊天功能帮助**

**基本对话:**
• 直接发送消息即可开始对话
• 支持上下文连续对话
• 可以讨论各种话题

**对话技巧:**
• 描述越详细，回答越准确
• 可以要求特定风格的回答
• 支持角色扮演对话

**私聊 vs 群组:**
• 私聊：直接发消息
• 群组：@机器人 或回复机器人消息
            """,
            "tools": """
🛠️ **工具功能帮助**

**翻译工具:**
• 格式：`翻译: 要翻译的内容`
• 支持多种语言互译

**计算工具:**
• 格式：`计算: 1+2*3`
• 支持基本数学运算

**语音功能:**
• 发送语音消息自动转文字
• 然后进行AI回复

**图片分析:**
• 发送图片进行内容识别
• 可配合文字询问图片相关问题
            """,
            "settings": """
⚙️ **设置帮助**

**语言设置:**
• 切换机器人回复语言
• 支持中文、英文等

**聊天模式:**
• 普通模式：日常对话
• 专业模式：专业问题回答
• 创意模式：创意写作协助

**通知设置:**
• 开启/关闭消息通知
• 管理提醒频率

**数据管理:**
• 查看使用统计
• 清除对话历史
• 导出个人数据
            """,
            "faq": """
❓ **常见问题**

**Q: 机器人不回复我？**
A: 检查是否在群组中@了机器人，或者是否触发了速率限制。

**Q: 回复速度慢？**
A: 复杂问题需要更多处理时间，请耐心等待。

**Q: 如何重置对话？**
A: 使用 /start 命令或在设置中清除历史。

**Q: 支持哪些文件类型？**
A: 目前支持图片、语音消息，文档功能开发中。

**Q: 如何反馈问题？**
A: 联系管理员或使用 /admin 命令（管理员）。

**Q: 数据隐私如何保护？**
A: 所有数据本地存储，可随时删除个人信息。
            """
        }

        content = help_content.get(category, "❓ 帮助内容未找到")

        keyboard = [
            [InlineKeyboardButton("« 返回帮助", callback_data="help")],
            [InlineKeyboardButton("🏠 主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            content,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_setting_option(self, query, option: str):
        """处理设置选项"""
        if option == "language":
            await self.handle_language_setting(query)
        elif option == "mode":
            await self.handle_mode_setting(query)
        elif option == "notifications":
            await self.handle_notification_setting(query)
        elif option == "data":
            await self.handle_data_setting(query)

    async def handle_language_setting(self, query):
        """处理语言设置"""
        keyboard = [
            [
                InlineKeyboardButton("🇨🇳 中文", callback_data="set_lang_zh"),
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")
            ],
            [InlineKeyboardButton("« 返回设置", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🌍 **选择语言 / Choose Language**",
            reply_markup=reply_markup
        )

    async def handle_admin_action(self, query, action: str):
        """处理管理员操作"""
        user_id = query.from_user.id

        if not self.bot.is_admin(user_id):
            await query.edit_message_text("❌ 权限不足")
            return

        if action == "status":
            await self.show_system_status(query)
        elif action == "users":
            await self.show_user_statistics(query)
        elif action == "broadcast":
            await query.edit_message_text("📢 广播功能开发中...")
        elif action == "settings":
            await query.edit_message_text("🔧 系统设置开发中...")

    async def show_system_status(self, query):
        """显示真实的系统状态"""
        if not self.bot.is_admin(query.from_user.id):
            await query.edit_message_text("❌ 权限不足")
            return

        try:
            # 获取真实系统状态
            system_stats = self.bot.system_monitor.get_real_system_status()
            realtime_stats = await self.bot.stats_manager.get_real_time_stats()
            performance_metrics = await self.bot.stats_manager.get_performance_metrics()

            # 生成状态文本
            status_text = f"""
    📊 **实时系统状态**

    {system_stats.get('status_emoji', '🔍')} **系统状态:** {system_stats.get('status', '未知')}

    💻 **系统资源:**
    • CPU使用: {system_stats.get('cpu_percent', 0):.1f}%
    • 内存使用: {system_stats.get('memory_percent', 0):.1f}% ({system_stats.get('memory_used_gb', 0):.1f}GB/{system_stats.get('memory_total_gb', 0):.1f}GB)
    • 磁盘使用: {system_stats.get('disk_percent', 0):.1f}% (剩余 {system_stats.get('disk_free_gb', 0):.1f}GB)

    📊 **实时统计:**
    • 今日消息: {realtime_stats.get('today_messages', 0):,}
    • 今日用户: {realtime_stats.get('today_active_users', 0):,}
    • 当前小时: {realtime_stats.get('current_hour_messages', 0):,}
    • 在线用户: {realtime_stats.get('online_users', 0):,}

    ⚡ **性能指标:**
    • 总请求数: {system_stats.get('total_requests', 0):,}
    • API调用: {system_stats.get('api_calls', 0):,}
    • 错误次数: {system_stats.get('error_count', 0):,}
    • 错误率: {system_stats.get('error_rate', 0):.2f}%
    • 平均响应: {system_stats.get('avg_response_time', 0):.2f}秒

    🔧 **服务信息:**
    • 运行时间: {system_stats.get('uptime', '未知')}
    • 最后错误: {system_stats.get('last_error_time', '无')}
    • 数据源: {realtime_stats.get('data_source', '未知')}

    🕐 **更新时间:** {system_stats.get('current_time', '未知')}
            """

            # 如果有错误信息，添加到状态中
            if 'error' in system_stats:
                status_text += f"\n⚠️ **监控错误:** {system_stats['error']}"

            keyboard = [
                [InlineKeyboardButton("🔄 刷新", callback_data="admin_status")],
                [InlineKeyboardButton("📈 性能趋势", callback_data="admin_performance")],
                [InlineKeyboardButton("« 返回管理", callback_data="admin")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"显示系统状态失败: {e}")
            await query.edit_message_text(f"❌ 获取系统状态失败: {e}")

    async def show_user_statistics(self, query):
        """显示用户统计"""
        if not self.bot.is_admin(query.from_user.id):
            await query.edit_message_text("❌ 权限不足")
            return

        try:
            realtime_stats = await self.bot.stats_manager.get_real_time_stats()
            user_stats = await self.bot.stats_manager.get_user_statistics()

            # 生成动作类型分布
            action_types = realtime_stats.get('today_action_types', {})
            action_text = "\n".join([
                f"• {action}: {count}"
                for action, count in sorted(action_types.items(), key=lambda x: int(x[1]), reverse=True)[:5]
            ]) or "暂无数据"

            stats_text = f"""
    👥 **用户统计数据**

    📊 **今日活跃:**
    • 活跃用户: {realtime_stats.get('today_active_users', 0):,}
    • 消息总数: {realtime_stats.get('today_messages', 0):,}
    • 当前在线: {realtime_stats.get('online_users', 0):,}

    💬 **聊天类型分布:**
    {self._format_chat_types(realtime_stats.get('chat_types', {}))}

    🎯 **热门功能 (今日):**
    {action_text}

    📈 **总体数据:**
    • 注册用户: {user_stats.get('total_registered_users', 0):,}
    • 数据源: {realtime_stats.get('data_source', '未知')}

    🕐 **更新时间:** {realtime_stats.get('last_updated', '未知')}
            """

            keyboard = [
                [InlineKeyboardButton("🔄 刷新", callback_data="admin_users")],
                [InlineKeyboardButton("📊 详细报告", callback_data="admin_detailed_stats")],
                [InlineKeyboardButton("« 返回管理", callback_data="admin")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"显示用户统计失败: {e}")
            await query.edit_message_text(f"❌ 获取用户统计失败: {e}")

    def _format_chat_types(self, chat_types: dict) -> str:
        """格式化聊天类型统计"""
        if not chat_types:
            return "暂无数据"

        total = sum(int(count) for count in chat_types.values())
        if total == 0:
            return "暂无数据"

        formatted = []
        for chat_type, count in chat_types.items():
            percentage = (int(count) / total) * 100
            emoji = "💬" if chat_type == "private" else "👥"
            formatted.append(f"{emoji} {chat_type}: {count} ({percentage:.1f}%)")

        return "\n".join(formatted)

        keyboard = [[InlineKeyboardButton("« 返回管理", callback_data="admin")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )