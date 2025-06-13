import logging
import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["TOKEN"]

def download_youtube_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео, и я скачаю его для тебя.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    try:
        await update.message.reply_text("Скачиваю видео...")
        download_youtube_video(url)

        with open("video.mp4", "rb") as video:
            await context.bot.send_video(chat_id=chat_id, video=video)

        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при скачивании: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
