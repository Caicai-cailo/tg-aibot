"""
媒体处理器
"""

import logging
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from services.media_service import MediaService

logger = logging.getLogger(__name__)


class MediaHandlers:
    """媒体处理器类"""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.media_service = MediaService()

    def register_handlers(self, application):
        """注册媒体处理器"""
        if self.config.ENABLE_VOICE:
            application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

        if self.config.ENABLE_IMAGE:
            application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

        logger.info("✅ 媒体处理器已注册")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理语音消息"""
        # 检查是否需要响应
        if not await self.should_respond(update):
            return

        await update.message.reply_text("🎧 正在处理语音消息...")

        try:
            # 处理语音转文字
            text = await self.media_service.voice_to_text(update.message.voice, context.bot)

            if text:
                await update.message.reply_text(f"🎤 识别内容: {text}")
                # 这里可以继续处理识别出的文字
            else:
                await update.message.reply_text("😅 语音识别失败，请重试")

        except Exception as e:
            logger.error(f"语音处理出错: {e}")
            await update.message.reply_text("🎤 语音处理出现问题，请稍后重试")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片消息"""
        # 检查是否需要响应
        if not await self.should_respond(update):
            return

        await update.message.reply_text("🔍 正在分析图片...")

        try:
            # 获取图片
            photo = update.message.photo[-1]  # 获取最高清版本

            # 分析图片
            description = await self.media_service.analyze_image(photo, context.bot)

            if description:
                response = f"🖼️ **图片分析结果:**\n\n{description}"

                # 如果用户有文字说明，结合分析
                if update.message.caption:
                    response += f"\n\n💭 **用户备注:** {update.message.caption}"

                await update.message.reply_text(response, parse_mode="Markdown")
            else:
                await update.message.reply_text("😅 图片分析失败，请重试")

        except Exception as e:
            logger.error(f"图片处理出错: {e}")
            await update.message.reply_text("🖼️ 图片处理出现问题，请稍后重试")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文档消息"""
        # 检查是否需要响应
        if not await self.should_respond(update):
            return

        document = update.message.document
        file_name = document.file_name
        file_size = document.file_size

        # 检查文件大小限制（20MB）
        if file_size > 20 * 1024 * 1024:
            await update.message.reply_text("📄 文件太大，请发送小于20MB的文件")
            return

        await update.message.reply_text(f"📄 收到文档: {file_name}\n文档处理功能开发中...")

    async def should_respond(self, update: Update) -> bool:
        """判断是否应该响应媒体消息"""
        chat = update.effective_chat

        # 私聊始终响应
        if chat.type == "private":
            return True

        # 群组中检查是否@机器人或回复机器人
        return self.bot.should_respond_in_group(update)