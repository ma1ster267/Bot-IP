import telebot
from flask import Flask, request
import json

TOKEN = "7805329225:AAGysumTy8PyJKIaywur0ZRtWGpbAdvAM0k"
OWNER_ID = 5223717297
GROUP_ID = -1002207273836
ADMIN_IDS = {5223717297, 1071290377, 1474741889}
WEBHOOK_URL = 'https://ma1ster.onrender.com' 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Головна сторінка (щоб Render не засинав)
@app.route("/", methods=["GET"])
def home():
    return "Бот працює!", 200

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
    

homework_dict = {
    "фізика 🪐": "",
    "фізкультура 🏋️‍♂️": "",
    "географія 🌍": "",
    "технології ⚙️": "",
    "історія україни ⚔️": "",
    "зарубіжна література 📚": "",
    "всесвітня історія ⚔️": "",
    "хімія 🧪": "",
    "інформатика 💻": "",
    "захист україни 🪖": "",
    "українська мова 📝": "",
    "українська література 📖": "",
    "математика ➗": "",
    "біологія 🦠": "",
    "іноземна мова(лин)": "",
    "іноземна мова(ляшенко)": ""
}

try:
    with open("homework.json", "r", encoding="utf-8") as file:
        homework_dict.update(json.load(file))
except FileNotFoundError:
    pass

user_state = {}
user_homework = {}
selected_subjects = {}

def save_homework():
    with open("homework.json", "w", encoding="utf-8") as file:
        json.dump(homework_dict, file, ensure_ascii=False, indent=4)
    with open("homework.json", "rb") as file:
        bot.send_document(OWNER_ID, file)

def create_subjects_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in homework_dict:
        keyboard.add(telebot.types.KeyboardButton(subject))
    keyboard.add(telebot.types.KeyboardButton("✅ Відправити в групу"), telebot.types.KeyboardButton("Назад ⬅️"))
    return keyboard

def create_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Редагувати ДЗ ✏️", "ДЗ в групу 📩", "Переглянути ДЗ 👀")
    return keyboard

def create_finish_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("✅ Завершити", "➕ Додати ще")
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "🔹 Вітаю! Оберіть дію:", reply_markup=create_main_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ У вас немає доступу до цього бота.")

@bot.message_handler(func=lambda message: message.text == "Редагувати ДЗ ✏️")
def edit_homework(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "🔹 Оберіть предмет для редагування:", reply_markup=create_subjects_keyboard())
        user_state[message.from_user.id] = "choosing_subject"

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "choosing_subject")
def enter_homework(message):
    user_id = message.from_user.id
    if message.text == "Назад ⬅️":
        bot.send_message(message.chat.id, "🔙 Повертаємося в головне меню.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        return

    if message.text in homework_dict:
        homework_dict[message.text] = ""
        bot.send_message(message.chat.id, f"🔹 Старе ДЗ для {message.text} було видалено. Введіть нове ДЗ:",
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        user_state[user_id] = "editing_homework"
        user_homework[user_id] = message.text
    else:
        bot.send_message(message.chat.id, "⚠️ Невідомий предмет. Спробуйте ще раз.")

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "editing_homework")
def save_homework_entry(message):
    user_id = message.from_user.id
    subject = user_homework[user_id]
    homework_dict[subject] += ("\n\n" if homework_dict[subject] else "") + message.text
    bot.send_message(message.chat.id, "✅ ДЗ додано. Що робимо далі?", reply_markup=create_finish_keyboard())
    user_state[user_id] = "finish_or_add"

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "finish_or_add")
def finish_or_add_more(message):
    user_id = message.from_user.id
    if message.text == "✅ Завершити":
        save_homework()
        bot.send_message(message.chat.id, "✅ ДЗ збережено.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        user_homework.pop(user_id, None)
    elif message.text == "➕ Додати ще":
        bot.send_message(message.chat.id, "✏️ Введіть додаткове ДЗ:", reply_markup=telebot.types.ReplyKeyboardRemove())
        user_state[user_id] = "editing_homework"
    else:
        bot.send_message(message.chat.id, "⚠️ Оберіть дію зі списку.")

@bot.message_handler(func=lambda message: message.text == "ДЗ в групу 📩")
def send_homework_to_group(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "🔹 Оберіть предмети для відправки (натискайте по черзі):",
                         reply_markup=create_subjects_keyboard())
        user_state[message.from_user.id] = "choosing_subjects"
        selected_subjects[message.from_user.id] = []

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "choosing_subjects")
def choose_subjects_for_group(message):
    user_id = message.from_user.id
    if message.text == "Назад ⬅️":
        bot.send_message(message.chat.id, "🔙 Повертаємося в головне меню.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        selected_subjects.pop(user_id, None)
        return

    if message.text == "✅ Відправити в групу":
        if user_id not in selected_subjects or not selected_subjects[user_id]:
            bot.send_message(message.chat.id, "⚠️ Ви не обрали жодного предмета.")
            return

        message_text = "💬 <b>Домашнє завдання:</b>\n\n"
        for subject in selected_subjects[user_id]:
            message_text += f"\n🧷 <b>{subject}:</b>\n{homework_dict.get(subject, '❌ Немає завдання')}\n"
            message_text += "_______________________\n"
        message_text += "Більше ДЗ тут: <a href='https://sites.google.com/view/ip31253456'>https://sites.google.com/view/ip31253456</a>"

        bot.send_message(message.chat.id, message_text, parse_mode="HTML")
        bot.send_message(GROUP_ID, message_text, parse_mode="HTML")

        bot.send_message(message.chat.id, "✅ ДЗ відправлено в групу.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        selected_subjects.pop(user_id, None)
        return

    subject = message.text
    if subject in homework_dict:
        if user_id not in selected_subjects:
            selected_subjects[user_id] = []

        if subject not in selected_subjects[user_id]:
            selected_subjects[user_id].append(subject)
            bot.send_message(message.chat.id, f"✅ {subject} додано до списку.")
    else:
        bot.send_message(message.chat.id, "⚠️ Невідомий предмет. Спробуйте ще раз.")

@bot.message_handler(func=lambda message: message.text == "Переглянути ДЗ 👀")
def view_homework(message):
    bot.send_message(message.chat.id, "🔹 Оберіть предмет для перегляду:", reply_markup=create_subjects_keyboard())
    user_state[message.from_user.id] = "choosing_subject_for_view"


@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "choosing_subject_for_view")
def send_homework_for_subject(message):
    user_id = message.from_user.id
    subject = message.text

    if subject == "Назад ⬅️":
        bot.send_message(message.chat.id, "🔙 Повертаємося в головне меню.", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
        return

    if subject in homework_dict:
        homework = homework_dict[subject] if homework_dict[subject] else "❌ Немає завдання"
        bot.send_message(message.chat.id, f"💬 <b>Домашнє завдання з {subject}:</b>\n\n{homework}", parse_mode="HTML", reply_markup=create_main_keyboard())
        user_state.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "⚠️ Невідомий предмет. Спробуйте ще раз.")



# Запуск програми
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=8080)
