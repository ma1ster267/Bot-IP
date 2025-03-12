import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os

TOKEN = '7805329225:AAFhcb1Hngf6lMWag9g9Ttycvpu1TdiUdJY'
GROUP_ID = -1001992854284  # ID групи для надсилання ДЗ
bot = telebot.TeleBot(TOKEN)

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
        bot.send_message(USER_ID, "✅ Домашнє завдання оновлено.", parse_mode='HTML')
    except Exception as e:
        bot.send_message(USER_ID, f"❌ Помилка збереження ДЗ: {e}")

# Головне меню
def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Редагувати ДЗ ✏️"))
    keyboard.add(KeyboardButton("Надіслати ДЗ на завтра 📤"))
    return keyboard

# Меню предметів
def create_subjects_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in homework_dict.keys():
        keyboard.add(KeyboardButton(subject))
    keyboard.add(KeyboardButton("Назад ⬅️"))
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
        user_state[message.from_user.id] = {"subject": subject, "new_homework": ""}
        bot.register_next_step_handler(message, save_edited_homework)
    else:
        bot.reply_to(message, "⚠️ Невідомий предмет. Спробуйте ще раз.")

def save_edited_homework(message):
    user_id = message.from_user.id
    if isinstance(user_state.get(user_id), dict):
        subject = user_state[user_id]["subject"]
        if subject:
            homework_dict[subject] = message.text
            save_homework()
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("Додати ще"), KeyboardButton("Завершити редагування"))
            bot.reply_to(message, f"✅ ДЗ для {subject} оновлено. Що далі?", reply_markup=keyboard)
            user_state[user_id]["new_homework"] = message.text
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

# Надсилання ДЗ на завтра
@bot.message_handler(func=lambda message: message.text == "Надіслати ДЗ на завтра 📤")
def send_homework_tomorrow(message):
    if message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, "🔹 Оберіть предмети для відправки (відправляйте їх по черзі). Завершіть командою 'Готово ✅':",
                     reply_markup=create_subjects_keyboard())
        user_state[message.from_user.id] = {"sending_homework": []}

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get("sending_homework") is not None)
def collect_subjects_to_send(message):
    user_id = message.from_user.id
    if message.text == "Назад ⬅️":
        bot.reply_to(message, "🔙 Повертаємося в головне меню.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        return
    if message.text == "Готово ✅":
        subjects = user_state[user_id]["sending_homework"]
        if subjects:
            homework_text = "\n\n".join([f"📚 <b>{subj}</b>: {homework_dict.get(subj, 'Немає ДЗ')}" for subj in subjects])
            bot.send_message(GROUP_ID, f"📢 <b>Домашнє завдання на завтра:</b>\n\n{homework_text}", parse_mode='HTML')
            bot.reply_to(message, "✅ ДЗ на завтра надіслано в групу.", reply_markup=create_main_keyboard())
        else:
            bot.reply_to(message, "⚠️ Ви не вибрали жодного предмета.")
        user_state.pop(user_id, None)
    elif message.text in homework_dict:
        user_state[user_id]["sending_homework"].append(message.text)
        bot.reply_to(message, f"✅ {message.text} додано. Оберіть ще або натисніть 'Готово ✅'.")
    else:
        bot.reply_to(message, "⚠️ Невідомий предмет. Спробуйте ще раз.")

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
