# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:18
# @File    : controller.py
# @Software: PyCharm
from io import BytesIO

from asgiref.sync import sync_to_async
from loguru import logger
from telebot import types
from telebot import util, formatting
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.asyncio_storage import StateMemoryStorage

from app.event import pipeline_pass
from app_conf import settings
from setting.telegrambot import BotSetting

StepCache = StateMemoryStorage()


@sync_to_async
def sync_to_async_func():
    pass


class BotRunner(object):
    def __init__(self):
        self.bot = AsyncTeleBot(BotSetting.token, state_storage=StepCache)

    async def download(self, file):
        assert hasattr(file, "file_id"), "file_id not found"
        name = file.file_id
        _file_info = await self.bot.get_file(file.file_id)
        if isinstance(file, types.PhotoSize):
            name = f"{_file_info.file_unique_id}.jpg"
        if isinstance(file, types.Document):
            name = f"{file.file_unique_id} {file.file_name}"
        if not name.endswith(("jpg", "png", "webp")):
            return None
        downloaded_file = await self.bot.download_file(_file_info.file_path)
        return downloaded_file

    async def censor(self, file):
        file_data = await self.download(file=file)
        if file_data is None:
            return False, "🥛 Not An image"
        if isinstance(file_data, bytes):
            file_data = BytesIO(file_data)
        result = await pipeline_pass(trace_id="test", content=file_data)
        if result.risk_tag:
            return True, f"🔨 Image Content Maybe illegal: {result.risk_tag}"
        return (
            False,
            f"🥽 AnimeScore {result.anime_score}\n☕️ Content {result.anime_tags[:7]}",
        )

    async def run(self):
        logger.info("Bot Start")
        bot = self.bot
        if BotSetting.proxy_address:
            from telebot import asyncio_helper

            asyncio_helper.proxy = BotSetting.proxy_address
            logger.info("Proxy tunnels are being used!")

        @bot.message_handler(
            commands="help", chat_types=["private", "supergroup", "group"]
        )
        async def listen_help_command(message: types.Message):
            _message = await bot.reply_to(
                message=message,
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    formatting.mlink(
                        "🍀 Github", "https://github.com/sudoskys/TelegramBotTemplate"
                    ),
                ),
                parse_mode="MarkdownV2",
            )

        async def delete_or_warn(message: types.Message, reason: str):
            reason_detail = f"For User {message.from_user.last_name}[{message.from_user.id}]\n{reason}"
            try:
                await self.bot.delete_message(
                    chat_id=message.chat.id, message_id=message.message_id
                )
            except Exception as er:
                logger.exception(er)
            try:
                await self.bot.reply_to(message=message, text=reason_detail)
            except Exception as er:
                logger.exception(er)
            return True

        @bot.message_handler(
            content_types=["photo", "document"], chat_types=["supergroup", "group"]
        )
        async def handle_group_photo(message: types.Message):
            if settings.rule.only_report:
                return logger.debug("Only Report So ignore")
            if settings.mode.only_white:
                if message.chat.id not in settings.mode.white_group:
                    return logger.info(f"White List Out {message.chat.id}")
            if not settings.rule.check_spoiler_photo:
                if message.has_media_spoiler:
                    return logger.info("Ignore Spoiler Photos")
            message_ph = message.photo
            message_doc = message.document
            if message_ph:
                filtered, reason = await self.censor(file=message_ph[-1])
                if filtered:
                    await delete_or_warn(message=message, reason=reason)
            if message_doc:
                filtered, reason = await self.censor(file=message_doc)
                if filtered:
                    await delete_or_warn(message=message, reason=reason)

        @bot.message_handler(commands="report", chat_types=["supergroup", "group"])
        async def report(message: types.Message):
            if settings.mode.only_white:
                if message.chat.id not in settings.mode.white_group:
                    return logger.info(f"White List Out {message.chat.id}")

            if not message.reply_to_message:
                return await bot.reply_to(
                    message,
                    text=f"🍡 please reply to spam message with this command ({message.chat.id})",
                )
            logger.info(f"Report in {message.chat.id} {message.from_user.id}")
            reply_message = message.reply_to_message
            reply_message_ph = reply_message.photo
            reply_message_doc = reply_message.document
            if reply_message_ph:
                filtered, reason = await self.censor(file=reply_message_ph[-1])
                if filtered:
                    return await delete_or_warn(message=reply_message, reason=reason)
                else:
                    return await bot.reply_to(message, text=reason)
            if reply_message_doc:
                filtered, reason = await self.censor(file=reply_message_doc)
                if filtered:
                    return await delete_or_warn(message=reply_message, reason=reason)
                else:
                    return await bot.reply_to(message, text=reason)
            return await bot.reply_to(message, text="🥛 Not image")

        try:
            await bot.polling(
                non_stop=True, allowed_updates=util.update_types, skip_pending=True
            )
        except ApiTelegramException as e:
            logger.opt(exception=e).exception("ApiTelegramException")
        except Exception as e:
            logger.exception(e)
