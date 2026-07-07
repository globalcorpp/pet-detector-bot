import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from aiohttp import web

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
# Render provides the public URL in the RENDER_EXTERNAL_URL environment variable
APP_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Start def called")
    await update.message.reply_text("Willkommen auf mein App !")
    keyboard = [
        [KeyboardButton("Name"), KeyboardButton("Alter")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Auswahlen Sie eine Option unten, um zu beginnen:",
        reply_markup=reply_markup
    )

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_data = context.user_data

    if user_text == "Name":
        user_data['state'] = 'waiting_for_name'
        await update.message.reply_text("Wie heißen Sie? Bitte geben Sie Ihren Namen ein:")
        return

    if user_text == "Alter":
        user_data['state'] = 'waiting_for_age'
        await update.message.reply_text("Wie alt sind Sie? Bitte geben Sie Ihr Alter ein:")
        return

    current_state = user_data.get('state')

    if current_state == 'waiting_for_name':
        user_data['state'] = None
        await update.message.reply_text(f"Hallo {user_text}, Guten Tag 👋 .")
        
    elif current_state == 'waiting_for_age':
        user_data['state'] = None
        await update.message.reply_text(f"Bist du {user_text} Jahre alt? 😎")
        
    else:
        await update.message.reply_text("Bitte verwenden Sie die Menüoptionen unten.")

# HTTP handler for Render's port scan / health check
async def home(request):
    return web.Response(text="Bot is perfectly running! 🚀")

# Background loop that pings the web server every 10 minutes to prevent sleep
async def keep_alive():
    await asyncio.sleep(15)  # Wait for the server to fully start up first
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Only ping if we are deployed on Render (URL contains http)
                if "localhost" not in APP_URL:
                    async with session.get(APP_URL) as response:
                        print(f"Self-ping sent to {APP_URL}. Response status: {response.status}")
                else:
                    print("Running locally. Self-ping skipped.")
            except Exception as e:
                print(f"Self-ping failed: {e}")
            
            await asyncio.sleep(600)  # 600 seconds = 10 minutes

async def main():
    # 1. Initialize and start the Telegram bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("Telegram Bot polling started.")

    # 2. Setup the aiohttp web server
    web_app = web.Application()
    web_app.add_routes([web.get('/', home)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    # Use Render's assigned port or fallback to 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

    # 3. Run the keep-alive ping loop alongside the application
    asyncio.create_task(keep_alive())

    # Keep the main loop running infinitely
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping application...")
        await app.updater.stop()
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
