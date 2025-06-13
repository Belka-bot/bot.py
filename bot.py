import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import os

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео, и я предложу тебе выбрать качество для скачивания.")

def get_formats(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        filtered = []
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                quality = f.get('format_note') or f.get('height')
                size = f.get('filesize') or 0
                size_mb = round(size / 1024 / 1024, 1) if size else "?"
                filtered.append({
                    'format_id': f['format_id'],
                    'quality': f"{quality}p",
                    'size': f"{size_mb}MB",
                    'url': url
                })
        return filtered

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    try:
        formats = get_formats(url)
        user_links[update.effective_chat.id] = {
            "url": url,
            "formats": formats
        }
        keyboard = [
            [InlineKeyboardButton(f"{f['quality']} ({f['size']})", callback_data=f['format_id'])]
            for f in formats
        ]
        await update.message.reply_text("Выберите качество:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении форматов: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    format_id = query.data
    chat_id = update.effective_chat.id

    if chat_id not in user_links:
        await query.edit_message_text("Ошибка: нет сохранённой ссылки.")
        return

    url = user_links[chat_id]["url"]
    out_file = "video.mp4"
    ydl_opts = {
        'format': format_id,
        'outtmpl': out_file,
        'quiet': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await context.bot.send_video(chat_id=chat_id, video=open(out_file, 'rb'))
        os.remove(out_file)
    except Exception as e:
        await query.edit_message_text(f"Ошибка при загрузке: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
