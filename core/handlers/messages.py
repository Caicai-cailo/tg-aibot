"""
消息处理器
"""

import logging
import asyncio
import random
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction, ParseMode
from services.openai_service import OpenAIService
from utils.decorators import rate_limit, log_user_action
from utils.helpers import split_long_message

logger = logging.getLogger(__name__)


class MessageHandlers:
    """消息处理器类"""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.openai_service = OpenAIService()

        # 表情反应池
        self.reactions = ["👍", "❤️", "🔥", "🎉", "😊", "🤔", "👏", "💯"]

    def register_handlers(self, application):
        """注册消息处理器"""
        # 文本消息处理器
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )

        logger.info("✅ 消息处理器已注册")

    async def should_respond(self, update: Update) -> bool:
        """判断是否应该响应消息"""
        chat = update.effective_chat

        # 私聊始终响应
        if chat.type == "private":
            return True

        # 群组中检查是否@机器人或回复机器人
        return self.bot.should_respond_in_group(update)

    @rate_limit
    @log_user_action
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        # 检查是否需要响应
        if not await self.should_respond(update):
            return

        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        text = message.text

        # 显示正在输入状态
        await self.show_typing_with_delay(context, chat.id)

        try:
            # 更新用户活动
            await self.bot.user_service.update_user_activity(user.id)

            # 检查特殊命令模式
            response = await self.process_special_commands(text)

            if not response:
                # 普通AI对话
                response = await self.process_ai_chat(user.id, text)

            # 发送回复
            await self.send_smart_reply(update, response)

            # 随机添加表情反应
            if self.config.ENABLE_REACTIONS and random.random() < 0.3:
                await self.add_random_reaction(message)

        except Exception as e:
            logger.error(f"处理文本消息出错: {e}")
            await self.send_error_message(update, e)

    async def process_special_commands(self, text: str) -> str:
        """处理特殊命令"""
        text_lower = text.lower().strip()

        # 翻译请求
        if any(keyword in text_lower for keyword in ['翻译', 'translate', '译']):
            return await self.handle_translation_request(text)

        # 计算请求
        if any(op in text for op in ['+', '-', '*', '/', '=']) or '计算' in text_lower:
            return await self.handle_calculation_request(text)

        # 天气请求
        if any(keyword in text_lower for keyword in ['天气', 'weather']):
            return await self.handle_weather_request(text)

        return None

    async def handle_translation_request(self, text: str) -> str:
        """处理翻译请求"""
        # 简单的翻译处理逻辑
        import re

        patterns = [
            r'翻译[:：]\s*(.+)',
            r'translate[:：]\s*(.+)',
            r'译[:：]\s*(.+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # 这里可以集成真实的翻译API
                return f"🌐 **翻译结果:**\n\n原文: {content}\n译文: [需要集成翻译API]"

        return "请使用格式: 翻译: 要翻译的内容"

    async def handle_calculation_request(self, text: str) -> str:
        """处理计算请求"""
        try:
            import re

            # 提取计算表达式
            calc_match = re.search(r'计算[:：]\s*(.+)', text)
            if calc_match:
                expression = calc_match.group(1).strip()
            else:
                # 直接包含数学符号的文本
                expression = text.strip()

            # 安全的数学计算
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression.replace(' ', '')):
                try:
                    result = eval(expression)
                    return f"🧮 **计算结果:**\n\n{expression} = {result}"
                except:
                    return "❌ 计算表达式有误，请检查格式"
            else:
                return "⚠️ 只支持基本数学运算 (+, -, *, /, 括号)"

        except Exception as e:
            logger.error(f"计算处理出错: {e}")
            return f"❌ 计算出错: {str(e)}"

    async def handle_weather_request(self, text: str) -> str:
        """处理天气请求"""
        # 这里可以集成天气API
        return "🌤️ 天气功能正在开发中，敬请期待！"

    async def process_ai_chat(self, user_id: int, text: str) -> str:
        """处理AI对话"""
        # 获取用户对话历史
        context_messages = await self.bot.user_service.get_conversation_context(user_id)

        # 构建完整上下文
        if context_messages:
            full_context = '\n'.join(context_messages[-10:]) + '\n' + f"用户: {text}"
        else:
            full_context = f"用户: {text}"

        # 调用AI服务
        response = await self.openai_service.get_chat_response(full_context)

        # 保存对话历史
        await self.bot.user_service.add_to_conversation_history(
            user_id, f"用户: {text}", f"助手: {response}"
        )

        return response

    async def show_typing_with_delay(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        """显示正在输入状态并延迟"""
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(self.config.SHOW_TYPING_DELAY)

    async def send_smart_reply(self, update: Update, response: str):
        """智能发送回复（处理长消息分割）"""
        if len(response) <= self.config.MAX_MESSAGE_LENGTH:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            # 分割长消息
            parts = split_long_message(response, self.config.MAX_MESSAGE_LENGTH)
            for i, part in enumerate(parts):
                if i > 0:
                    await asyncio.sleep(0.5)  # 避免消息发送过快
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)

    async def add_random_reaction(self, message):
        """添加随机表情反应"""
        try:
            from telegram import ReactionTypeEmoji
            reaction = random.choice(self.reactions)
            await message.set_reaction(ReactionTypeEmoji(reaction))
        except Exception as e:
            logger.debug(f"添加反应失败: {e}")

    async def send_error_message(self, update: Update, error: Exception):
        """发送错误消息"""
        error_messages = [
            "😅 出了点小问题，让我重新整理一下思路...",
            "🤔 系统有点忙，请稍后再试",
            "⚠️ 遇到了技术问题，正在修复中",
            "🔧 服务暂时不稳定，请耐心等待"
        ]

        message = random.choice(error_messages)
        await update.message.reply_text(message)