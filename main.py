import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_TAG = "Режиссёр"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def make_bold(text: str) -> str:
    """Превращает текст в полужирный с помощью HTML-тегов"""
    return f"<b>{text}</b>" if text else ""

@dp.message()
async def handle_media_messages(message: types.Message):
    # Проверяем тег
    if message.sender_tag != TARGET_TAG:
        return

    # Игнорируем текст (его обрабатывает первый бот)
    if message.text:
        return

    logger.info(f"Получено медиа: {message.content_type}")

    # Определяем ID темы (если сообщение из темы)
    thread_id = message.message_thread_id

    try:
        # Формируем подпись: полужирная пометка + полужирный оригинальный текст
        original_caption = message.caption or ""
        bold_sign = make_bold("🎬 От Режиссёра")
        bold_original = make_bold(original_caption)
        
        # Собираем итоговую подпись
        if original_caption:
            final_caption = f"{bold_sign}\n\n{bold_original}"
        else:
            final_caption = bold_sign

        # Фото
        if message.photo:
            photo = message.photo[-1]
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo.file_id,
                caption=final_caption,
                message_thread_id=thread_id,
                parse_mode="HTML"
            )
            logger.info(f"Фото отправлено в тему {thread_id or 'основную'}")
        
        # Видео
        elif message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=message.video.file_id,
                caption=final_caption,
                message_thread_id=thread_id,
                parse_mode="HTML"
            )
            logger.info(f"Видео отправлено в тему {thread_id or 'основную'}")
        
        # Документ (файл)
        elif message.document:
            await bot.send_document(
                chat_id=message.chat.id,
                document=message.document.file_id,
                caption=final_caption,
                message_thread_id=thread_id,
                parse_mode="HTML"
            )
            logger.info(f"Документ отправлен в тему {thread_id or 'основную'}")
        
        # Голосовое (подпись не поддерживается)
        elif message.voice:
            await bot.send_voice(
                chat_id=message.chat.id,
                voice=message.voice.file_id,
                message_thread_id=thread_id
            )
            logger.info(f"Голосовое отправлено в тему {thread_id or 'основную'}")
        
        # Опрос (копируем как есть)
        elif message.poll:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                message_thread_id=thread_id
            )
            logger.info(f"Опрос скопирован в тему {thread_id or 'основную'}")
        
        # Все остальные типы — копируем как есть
        else:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                message_thread_id=thread_id
            )
            logger.info(f"Медиа скопировано в тему {thread_id or 'основную'}")
        
        # Удаляем оригинал
        await message.delete()
        logger.info("Оригинал удалён")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def main():
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    
    async def health_check(request):
        return web.Response(text="OK")
    
    app.router.add_get("/healthz", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    
    print("✅ Медиа-бот запущен с поддержкой тем")
    print("✅ Отправляет ответы в ту же тему, откуда пришло сообщение")
    
    await polling_task

if __name__ == "__main__":
    asyncio.run(main())
