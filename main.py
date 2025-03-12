import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os
import requests
import base64
from datetime import datetime, timedelta
from flask import Flask, request

TOKEN = "7805329225:AAFu4s5jMAlalFNCCM-0FoSqm7L2Q_7eGQY"
WEBHOOK_URL = "https://bot-ip-odhy.onrender.com"
bot = telebot.TeleBot(TOKEN)

HOMEWORK_FILE = "homework.json"
ADMIN_IDS = {5223717297} 
GROUP_ID = -1001992854284

GITHUB_TOKEN = "ТОКЕН_GITHUB"
OWNER = "ma1ster267"
REPO = "homework-repo"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/homework.json"

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK'

def load_homework():
    if os.path.exists(HOMEWORK_FILE):
        with open(HOMEWORK_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_homework(homework_dict):
    try:
        with open(HOMEWORK_FILE, 'w', encoding='utf-8') as file:
            json.dump(homework_dict, file, ensure_ascii=False, indent=4)
    except Exception as e:
        bot.send_message(ADMIN_IDS, f"❌ Помилка збереження ДЗ: {e}")

def save_homework_to_github(homework_dict):
    content = json.dumps(homework_dict, ensure_ascii=False, indent=4)
    response = requests.get(API_URL, headers={'Authorization': f'token {GITHUB_TOKEN}'})

    sha = response.json().get('sha') if response.status_code == 200 else None
    data = {
        'message': 'Оновлення ДЗ',
        'content': base64.b64encode(content.encode()).decode(),
    }
    if sha:
        data['sha'] = sha

    response = requests.put(API_URL, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json=data)
    if response.status_code not in [200, 201]:
        bot.send_message(ADMIN_IDS, f"❌ Помилка GitHub: {response.text}")

homework_dict = load_homework()
user_state = {}

def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📖 Додати ДЗ"), KeyboardButton("📢 Надіслати ДЗ"))
    keyboard.add(KeyboardButton("✏️ Редагувати ДЗ"), KeyboardButton("📜 Переглянути ДЗ"))
    return keyboard

def create_subjects_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in homework_dict.keys():
        keyboard.add(KeyboardButton(subject))
    keyboard.add(KeyboardButton("⬅️ Назад"))
    return keyboard

@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "🔹 Вітаю, адміністраторе!", reply_markup=create_main_keyboard())
    else:
        bot.send_message(message.chat.id, "🚫 Тільки для адміністраторів!")

@bot.message_handler(func=lambda message: message.text == "📖 Додати ДЗ")
def add_homework(message):
    bot.send_message(message.chat.id, "📚 Оберіть предмет:", reply_markup=create_subjects_keyboard())
    user_state[message.from_user.id] = "adding_homework"

@bot.message_handler(func=lambda message: message.text in homework_dict and user_state.get(message.from_user.id) == "adding_homework")
def prompt_new_homework(message):
    subject = message.text
    bot.send_message(message.chat.id, f"✏️ Надішліть ДЗ для {subject} (можна текст, фото, файли):")
    user_state[message.from_user.id] = {"subject": subject, "text": "", "files": [], "date": None}
    bot.register_next_step_handler(message, handle_homework_input)

def handle_homework_input(message):
    user_id = message.from_user.id
    state = user_state.get(user_id, {})

    if "subject" not in state:
        return

    if message.text and message.text != "✅ Завершити":
        state["text"] += message.text + "\n"

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        state["files"].append(file_url)

    if message.document:
        file_info = bot.get_file(message.document.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        state["files"].append(file_url)

    bot.send_message(
        message.chat.id,
        "➕ Надсилайте ще або натисніть ✅ Завершити.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("✅ Завершити"))
    )
    bot.register_next_step_handler(message, finish_editing)

@bot.message_handler(func=lambda message: message.text == "✅ Завершити")
def finish_editing(message):
    user_id = message.from_user.id
    state = user_state.pop(user_id, {})

    if "subject" not in state:
        return

    subject = state["subject"]
    homework_text = state["text"].strip()
    files = "\n".join([f"📎 <a href='{link}'>Файл</a>" for link in state["files"]])

    homework_dict[subject] = f"{homework_text}\n{files}".strip()
    save_homework(homework_dict)
    save_homework_to_github(homework_dict)

    bot.send_message(message.chat.id, f"✅ ДЗ для {subject} збережено!", parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "📜 Переглянути ДЗ")
def view_homework(message):
    text = "\n\n".join([f"📌 <b>{subject}:</b>\n{hw}" for subject, hw in homework_dict.items()])
    bot.send_message(message.chat.id, f"📚 <b>Домашні завдання:</b>\n\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "📢 Надіслати ДЗ")
def send_homework(message):
    bot.send_message(message.chat.id, "📚 Оберіть предмети для відправки:", reply_markup=create_subjects_keyboard())
    user_state[message.from_user.id] = "sending_homework"

@bot.message_handler(func=lambda message: message.text in homework_dict and user_state.get(message.from_user.id) == "sending_homework")
def confirm_send_homework(message):
    subject = message.text
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    homework = homework_dict.get(subject, "Немає")

    text = f"📢 <b>ДЗ на {tomorrow}</b>\n\n📚 <b>{subject}</b>:\n{homework}"
    bot.send_message(GROUP_ID, text, parse_mode="HTML")

    bot.send_message(message.chat.id, "✅ ДЗ надіслано в групу!")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=10000, debug=True)
