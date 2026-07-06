import os
from turtle import update
from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler , filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Willkommen auf mein App !")
    keyboard = [
        [KeyboardButton("Name"), KeyboardButton("Alter")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text("Auswahlen Sie eine Option unten, um zu beginnen:",
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


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

app.run_polling()
