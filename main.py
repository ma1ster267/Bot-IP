import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os
import sqlite3
from datetime import datetime

TOKEN = '7805329225:AAEENYaeSeA7afi0Fa2_OUvCTo7rf0aVaO0'
bot = telebot.TeleBot(TOKEN)

DB_FILE = "homework.db"
OWNER_ID = 5223717297
SECOND_OWNER_ID = 5223717297
SUPPORT_ID = 5223717297

# Підключення до бази даних
def connect_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

# Створення таблиці в базі даних
def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

# Завантаження домашнього завдання з бази даних
def load_homework():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM homework ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    else:
        return create_default_homework()

# Створення стандартного домашнього завдання
def create_default_homework():
    return {
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
        "іноземна мова(ляшенко)": "",
    }

# Збереження домашнього завдання в базі даних
def save_homework(homework_dict):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO homework (data) VALUES (?)", (json.dumps(homework_dict),))
    conn.commit()
    conn.close()

# Ініціалізація бази даних та таблиці
create_table()

# Завантаження домашнього завдання
homework_dict = load_homework()
user_state = {}


def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("ДЗ 📖")
    button3 = KeyboardButton("Для адмінів")
    button4 = KeyboardButton("Поставити питання❓")
    button5 = KeyboardButton("Інформація")
    keyboard.add(button1)
    keyboard.add(button5, button4)
    keyboard.add(button3)
    return keyboard


def create_subjects_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for subject in homework_dict.keys():
        keyboard.add(KeyboardButton(subject))
    keyboard.add(KeyboardButton("Назад ⬅️"))
    return keyboard


def create_edit_options_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button_add_text = KeyboardButton("Додати ще текст 📝")
    button_finish_editing = KeyboardButton("Завершити редагування ✅")
    keyboard.add(button_add_text, button_finish_editing)
    return keyboard


def create_support_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button_complaint = KeyboardButton("Описати питання")
    button_back = KeyboardButton("Назад ⬅️")
    keyboard.add(button_complaint, button_back)
    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "<b>Привіт!</b>\n"
            "Виберіть одну з опцій нижче:",
            reply_markup=create_main_keyboard(),
            parse_mode='HTML'
        )


@bot.message_handler(func=lambda message: message.text == "ДЗ 📖")
def get_homework(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "<b>Виберіть предмет</b>, щоб дізнатись домашнє завдання:",
            reply_markup=create_subjects_keyboard(),
            parse_mode='HTML'
        )


@bot.message_handler(func=lambda message: message.text == "Інформація")
def bot_info(message):
    bot.send_message(
        message.chat.id,
        "🤖 <b>Цей бот створений для зручного перегляду та редагування домашнього завдання.</b>\n\n"
        "📌 <b>Можливості бота:</b>\n"
        "🔹 Швидкий перегляд домашніх завдань всіх предметів\n"
        "🔹 Додавання, редагування та видалення ДЗ (доступно адміністраторам)\n"
        "🔹 Можливість ставити питання адміністраторам безпосередньо через бота\n\n"
        "⚙ <b>Як користуватися ботом?</b>\n"
        "🔹 Оберіть предмет, щоб переглянути завдання.\n"
        "🔹 Натисніть кнопку (Поставити питання❓) та опишіть ого.\n\n"
        "💡 <b>Розробник:</b> @ma1ster\n"
        "📬 Якщо у вас є пропозиції щодо покращення або ви знайшли помилки, звертайтеся до розробника!",
        parse_mode='HTML'
    )




@bot.message_handler(func=lambda message: message.text == "Для адмінів")
def edit_homework(message):
    if message.chat.type == 'private':
        if message.from_user.id in [OWNER_ID, SECOND_OWNER_ID]:
            bot.reply_to(
                message,
                "<b>Виберіть предмет</b> для редагування домашнього завдання:",
                reply_markup=create_subjects_keyboard(),
                parse_mode='HTML'
            )
            user_state[message.from_user.id] = 'editing_homework'
            bot.register_next_step_handler(message, prompt_new_homework)
        else:
            bot.reply_to(message, "<b>😢 Упс, вибачте, але ви не адміністратор. 🚫</b>", parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == "Поставити питання❓")
def support(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "Якщо ви хочете поставити питання адміністратору, натискайте 'Описати питання' або поверніться назад.",
            reply_markup=create_support_keyboard(),
            parse_mode='HTML'
        )


@bot.message_handler(func=lambda message: message.text == "Назад ⬅️")
def go_back(message):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        if user_id in user_state and user_state[user_id] == 'editing_homework':
            bot.reply_to(
                message,
                "<b>Редагування скасовано.</b> Ви повернулись до вибору предмета.",
                reply_markup=create_subjects_keyboard(),
                parse_mode='HTML'
            )
            user_state[user_id] = 'viewing_homework'
        else:
            bot.reply_to(
                message,
                "Виберіть одну з опцій нижче:",
                reply_markup=create_main_keyboard(),
                parse_mode='HTML'
            )
            user_state[user_id] = 'viewing_homework'


@bot.message_handler(func=lambda message: message.text in homework_dict)
def handle_subject(message):
    subject = message.text
    if homework_dict[subject]:
        bot.reply_to(
            message,
            f"<b>Домашнє завдання з {subject}:</b>\n\n{homework_dict[subject]}\n\n<b>Питання:</b> @ma1ster",
            parse_mode='HTML'
        )
    else:
        bot.reply_to(
            message,
            f"<b>Домашнє завдання з {subject} ще не створене.</b>\n\n<b>Питання:</b> @ma1ster",
            parse_mode='HTML'
        )
    bot.reply_to(
        message,
        "Виберіть інший предмет або натисніть кнопку 'Назад ⬅️', щоб повернутись.",
        reply_markup=create_subjects_keyboard(),
        parse_mode='HTML'
    )


def prompt_new_homework(message):
    subject = message.text
    if subject in homework_dict:
        bot.reply_to(message,
                     f"Надішліть <b>нове завдання</b> для {subject}",
                     parse_mode='HTML')
        user_state[message.from_user.id] = {'subject': subject, 'new_homework': ''}
        bot.register_next_step_handler(message, handle_homework_input)
    else:
        bot.reply_to(message, "<b>Невідомий предмет.</b> Спробуйте ще раз.", parse_mode='HTML')


def handle_homework_input(message):
    user_id = message.from_user.id
    subject = user_state[user_id]["subject"]

    if message.text:
        if user_state[user_id]["new_homework"]:
            user_state[user_id]["new_homework"] += "\n\n" + message.text
        else:
            user_state[user_id]["new_homework"] = message.text

    bot.reply_to(
        message,
        "Ви можете додати ще текст або завершити редагування.",
        reply_markup=create_edit_options_keyboard(),
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda message: message.text == "Додати ще текст 📝")
def add_more_text(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Надішліть ще частину домашнього завдання:", parse_mode='HTML')
    bot.register_next_step_handler(message, handle_homework_input)


@bot.message_handler(func=lambda message: message.text == "Завершити редагування ✅")
def finish_editing(message):
    user_id = message.from_user.id
    subject = user_state[user_id]["subject"]
    new_homework = user_state[user_id]["new_homework"]

    homework_dict[subject] = new_homework
    save_homework(homework_dict)  # Передаємо homework_dict у функцію save_homework

    bot.reply_to(message, "✅ Домашнє завдання оновлено успішно.")
    user_state.pop(user_id)
    bot.reply_to(
        message,
        "Виберіть одну з опцій нижче:",
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda message: message.text == "Описати питання")
def new_complaint(message):
    user_state[message.from_user.id] = 'new_complaint'
    bot.reply_to(message, "Опишіть ваше питання:")


@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == 'new_complaint')
def handle_complaint(message):
    user_id = message.from_user.id
    complaint_text = message.text

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    bot.send_message(
        OWNER_ID,
        f"🔴 <b>Нове питання</b>\n\n📝 <b>Питання</b> від користувача {message.from_user.first_name} (ID: {user_id}, @ {message.from_user.username})\n"
        f"⏰ <b>Час:</b> {current_time}\n\n<b>Питання:</b> {complaint_text}",
        parse_mode='HTML'
    )

    bot.reply_to(message, "✅ Ваше питання було надіслано адміністратору. Дякуємо за звернення!")

    user_state.pop(user_id, None)
    bot.reply_to(
        message,
        "Виберіть одну з опцій нижче:",
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )


bot.polling(non_stop=True)