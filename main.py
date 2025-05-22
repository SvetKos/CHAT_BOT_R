
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from datetime import datetime, time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz

from config import BOT_TOKEN, SPREADSHEET_ID

# Авторизація Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Меню вибору локації
def location_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1. S1- Бульвар Данила Галицького", callback_data='S1')],
        [InlineKeyboardButton("2. S2- Миру", callback_data='S2')],
        [InlineKeyboardButton("3. S3- Злуки", callback_data='S3')],
        [InlineKeyboardButton("4. S4- Білогірська", callback_data='S4')],
    ])

# Підменю касирів для кожної локації
def cashier_menu(location):
    buttons = [
        InlineKeyboardButton(f"а) Касир {location.lower()}-1", callback_data=f"{location}_1"),
        InlineKeyboardButton(f"б) Касир {location.lower()}-2", callback_data=f"{location}_2"),
        InlineKeyboardButton(f"в) Касир {location.lower()}-3", callback_data=f"{location}_3"),
        InlineKeyboardButton(f"г) Касир {location.lower()}-4", callback_data=f"{location}_4"),
        InlineKeyboardButton("д) Касир підміна", callback_data=f"{location}_sub"),
        InlineKeyboardButton("ж) Завмаг", callback_data=f"{location}_boss"),
    ]
    return InlineKeyboardMarkup([[b] for b in buttons])

# Відправка повідомлення о 7:45
async def send_morning_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    context.chat_data['task_time'] = datetime.now(pytz.timezone('Europe/Kyiv')).strftime("%H:%M:%S")
    await context.bot.send_message(chat_id, "Включіть кавовий автомат", reply_markup=location_menu())

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активовано. Щоденне повідомлення налаштоване.")
    context.job_queue.run_daily(send_morning_message, time(hour=7, minute=45), chat_id=update.message.chat_id)

# Обробка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    if data.startswith("S") and "_" not in data:
        context.user_data["location"] = data
        await query.edit_message_text(f"Обрана локація: {data}", reply_markup=cashier_menu(data))
    elif "_" in data:
        location, choice = data.split("_")
        sheet = spreadsheet.worksheet(location)
        now = datetime.now(pytz.timezone('Europe/Kyiv'))
        sheet.append_row([
            now.strftime("%Y-%m-%d"),
            "Включіть кавовий автомат",
            context.chat_data.get('task_time', ''),
            now.strftime("%H:%M:%S"),
            location,
            f"Касир {data.lower().replace('_', '-')}", 
            f"{user.first_name} {user.last_name or ''} ({user.id})"
        ])
        await query.edit_message_text("Дякуємо, відповідь збережено.")

# Запуск
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
