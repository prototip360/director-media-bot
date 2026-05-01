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

@dp.message()
async def handle_media_messages(message: types.Message):
    if message.sender_tag != TARGET_TAG:
        return

    # Игнорируем текст (его обрабатывает первый бот)
    if message.text:
        return

    logger.info(f"Получено медиа: {message.content_type}")

    try:
        caption = "🎬 От Режиссёра"

        # Фото
        if message.photo:
            photo = message.photo[-1]  # самое большое фото
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo.file_id,
                caption=caption
            )
            logger.info("Фото отправлено с подписью")
        # Видео
        elif message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=message.video.file_id,
                caption=caption
            )
            logger.info("Видео отправлено с подписью")
        # Документ (файл)
        elif message.document:
            await bot.send_document(
                chat_id=message.chat.id,
                document=message.document.file_id,
                caption=caption
            )
            logger.info("Документ отправлен с подписью")
        # Голосовое (подпись не поддерживается)
        elif message.voice:
            await bot.send_voice(
                chat_id=message.chat.id,
                voice=message.voice.file_id
            )
            logger.info("Голосовое отправлено")
        # Опрос (копируем как есть)
        elif message.poll:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            logger.info("Опрос скопирован")
        # Все остальные типы — копируем как есть
        else:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            logger.info("Медиа скопировано")
        
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
    
    print("✅ Медиа-бот запущен (с подписью)")
    print("✅ Фото, видео, файлы получают подпись: '🎬 От Режиссёра'")
    
    await polling_task

if __name__ == "__main__":
    asyncio.run(main())
