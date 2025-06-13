import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from yt_dlp import YoutubeDL

TOKEN = os.environ["TOKEN"]
cookies_path = "cookies.txt" if os.path.exists("cookies.txt") else None

def get_video_formats(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "cookiefile": cookies_path
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for f in info["formats"]:
            if f.get("filesize") and f.get("height"):
                formats.append({
                    "format_id": f["format_id"],
                    "resolution": f"{f['width']}x{f['height']}",
                    "filesize": round(f["filesize"] / 1024 / 1024, 1)
                })
        return formats, info.get("webpage_url")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео, и я покажу варианты качества.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    try:
        formats, original_url = get_video_formats(url)
        context.user_data["video_url"] = url
        keyboard = [
            [InlineKeyboardButton(f'{f["resolution"]} / {f["filesize"]} MB ⚡', callback_data=f["format_id"])]
            for f in formats if f["resolution"] != "none"
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите качество:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    format_id = query.data
    url = context.user_data["video_url"]
    ydl_opts = {
        "format": format_id,
        "outtmpl": "video.mp4",
        "cookiefile": cookies_path,
        "quiet": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    await query.message.reply_video(video=open("video.mp4", "rb"))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
