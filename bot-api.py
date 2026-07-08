import os
import asyncio
import aiohttp
import numpy as np
from fastapi import FastAPI, File, UploadFile
from PIL import Image, ImageOps
import tflite_runtime.interpreter as tflite
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")

labels_path = os.path.join("converted_tflite", "labels.txt")
model_path = os.path.join("converted_tflite", "model_unquant.tflite")

with open(labels_path, "r", encoding="utf-8") as f:
    class_names = [line.strip() for line in f.readlines()]

interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Core Prediction Logic
def predict_animal(image_path):
    image = Image.open(image_path).convert('RGB')
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image, dtype=np.float32)
    normalized_image_array = (image_array / 127.5) - 1
    
    input_data = np.expand_dims(normalized_image_array, axis=0)
    
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    prediction = interpreter.get_tensor(output_details[0]['index'])
    index = np.argmax(prediction)
    
    full_class_name = class_names[index]
    cleaned_label = full_class_name.split(" ", 1)[-1] if " " in full_class_name else full_class_name

    translation_map = {
        "cats": "Katze",
        "dogs": "Hund",
        "cat": "Katze",
        "dog": "Hund"
    }
    
    german_label = translation_map.get(cleaned_label.lower(), cleaned_label)
    
    confidence_score = prediction[0][index]
    if confidence_score < 0.75:
        return "Unbekannt", f"{(1 - confidence_score) * 100:.1f}%" 
    return german_label, f"{float(confidence_score) * 100:.1f}%"

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📸 Bild senden")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Herzlich willkommen in meiner App ! \n\nBitte senden oder lade ein Foto von einer Katze oder einem Hund hoch, damit ich das Tier identifizieren kann.", 
        reply_markup=reply_markup
    )

async def handle_bot_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    await update.message.reply_text("Ihr Bild wird verarbeitet ...")
    
    temp_bot_path = f"temp_bot_{photo.file_id}.jpg"
    new_file = await context.bot.get_file(photo.file_id)
    await new_file.download_to_drive(custom_path=temp_bot_path)
    
    label, confidence = predict_animal(temp_bot_path)
    if os.path.exists(temp_bot_path):
        os.remove(temp_bot_path)
    
    await update.message.reply_text(f"Ergebnis: {label} {confidence} ")

# Anti-Sleep Keep-Alive Loop
async def keep_alive():
    await asyncio.sleep(15)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if "localhost" not in APP_URL:
                    async with session.get(f"{APP_URL}/health") as response:
                        print(f"Self-ping successful. Status: {response.status}")
                else:
                    print("Local environment detected. Skipping background self-ping.")
            except Exception as e:
                print(f"Self-ping background task warning: {e}")
            await asyncio.sleep(600)

# Modern Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_bot_photo))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    print("Telegram Bot listener activated safely.")
    
    asyncio.create_task(keep_alive())
    
    yield
    
    print("Shutting down bot polling...")
    await bot_app.updater.stop()
    await bot_app.stop()

# Initialize FastAPI with Lifespan ONLY ONCE
app = FastAPI(lifespan=lifespan)



@app.get("/health")
def health_check():
    return {"status": "alive"}

@app.post("/api/predict")
async def api_predict(file: UploadFile = File(...)):
    temp_path = f"temp_web_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    label, confidence = predict_animal(temp_path)
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return {"animal": label, "percent": confidence}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

