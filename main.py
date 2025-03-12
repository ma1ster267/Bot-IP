import telebot
from flask import Flask, request
import json
import os

TOKEN = '7805329225:7805329225:AAEwl-2XjKmfCQK0aZFJy-pdOyZ3ImlWmj0'  # Замініть на свій токен
WEBHOOK_URL = 'https://bot-ip-odhy.onrender.com'  # Замініть на свій URL
GROUP_ID = -1001992854284  # Замініть на ID вашої групи

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

HOMEWORK_FILE = "homework.json"
ADMIN_IDS = {5223717297, 1071290377, 1234567890}
USER_ID = 5223717297

# Завантаження ДЗ
def load_homework():
    if os.path.exists(HOMEWORK_FILE):
        with open(HOMEWORK_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

homework_dict = load_homework()
user_state = {}

# Збереження ДЗ
def save_homework():
    try:
        with open(HOMEWORK_FILE, 'w', encoding='utf-8') as file:
            json.dump(homework_dict, file, ensure_ascii=False, indent=4)
    except Exception as e:
        bot.send_message(USER_ID, f"❌ Помилка збереження ДЗ: {e}")

# Головне меню
def create_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(telebot.types.KeyboardButton("Редагувати ДЗ ✏️"))
    keyboard.add(telebot.types.KeyboardButton("Надіслати ДЗ на завтра 📤"))
    return keyboard

# Меню предметів
def create_subjects_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in homework_dict.keys():
        keyboard.add(telebot.types.KeyboardButton(subject))
    keyboard.add(telebot.types.KeyboardButton("Назад ⬅️"))
    return keyboard

# Старт
@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type == 'private' and message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, "🔹 Оберіть опцію:", reply_markup=create_main_keyboard())

# Редагування ДЗ
@bot.message_handler(func=lambda message: message.text == "Редагувати ДЗ ✏️")
def edit_homework(message):
    if message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, "🔹 Оберіть предмет:", reply_markup=create_subjects_keyboard())
        user_state[message.from_user.id] = "editing_homework"

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "editing_homework")
def select_subject_to_edit(message):
    if message.text == "Назад ⬅️":
        bot.reply_to(message, "🔙 Повертаємося в головне меню.", reply_markup=create_main_keyboard())
        user_state.pop(message.from_user.id, None)
        return

    subject = message.text
    if subject in homework_dict:
        bot.reply_to(message, f"✏️ Введіть нове ДЗ для {subject} (попереднє: {homework_dict[subject]}):")
        user_state[message.from_user.id] = {"subject": subject}
        bot.register_next_step_handler(message, save_edited_homework)
    else:
        bot.reply_to(message, "⚠️ Невідомий предмет. Спробуйте ще раз.")

def save_edited_homework(message):
    user_id = message.from_user.id
    subject = user_state.get(user_id, {}).get("subject")

    if subject:
        if subject in homework_dict and homework_dict[subject]:
            homework_dict[subject] += f"\n{message.text}"
        else:
            homework_dict[subject] = message.text
        save_homework()

        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(telebot.types.KeyboardButton("Додати ще"), telebot.types.KeyboardButton("Завершити редагування"))
        bot.reply_to(message, f"✅ ДЗ для {subject} оновлено. Що далі?", reply_markup=keyboard)
    else:
        bot.reply_to(message, "⚠️ Помилка редагування.")

@bot.message_handler(func=lambda message: message.text in ["Додати ще", "Завершити редагування"])
def edit_more_or_finish(message):
    user_id = message.from_user.id
    if message.text == "Додати ще":
        bot.reply_to(message, "🔹 Оберіть предмет:", reply_markup=create_subjects_keyboard())
        user_state[user_id] = "editing_homework"
    elif message.text == "Завершити редагування":
        bot.reply_to(message, "✅ Редагування завершено.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)

# Надсилання ДЗ у групу
@bot.message_handler(func=lambda message: message.text == "Надіслати ДЗ на завтра 📤")
def send_homework_tomorrow(message):
    if message.from_user.id in ADMIN_IDS:
        if not homework_dict:
            bot.send_message(GROUP_ID, "⚠️ Домашнього завдання немає.")
            return

        homework_text = "\n\n".join([f"📚 <b>{subject}</b>: {hw}" for subject, hw in homework_dict.items()])
        bot.send_message(GROUP_ID, f"📢 <b>Домашнє завдання на завтра:</b>\n\n{homework_text}", parse_mode='HTML')
        bot.reply_to(message, "✅ ДЗ на завтра надіслано в групу.")

# Webhook для отримання повідомлень
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return 'OK', 200

# Встановлення Webhook
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=8080)  # Без ssl_context для тестування
