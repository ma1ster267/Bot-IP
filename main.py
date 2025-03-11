import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import requests
import base64
import json  # Необхідний імпорт
from datetime import datetime

TOKEN = '7805329225:AAFu4s5jMAlalFNCCM-0FoSqm7L2Q_7eGQY'
WEBHOOK_URL = "https://bot-ip-odhy.onrender.com"
bot = telebot.TeleBot(TOKEN)

# Flask and SQLAlchemy setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Admins configuration
ADMIN_IDS = {5223717297, 1071290377, 1234567890}  # Add new IDs here
SUPPORT_ID = 5223717297

# GitHub configuration
GITHUB_TOKEN = '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'
OWNER = 'ma1ster267'
REPO = 'homework-repo'
API_URL = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/homework.json'

# Database model for homework
class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), unique=True, nullable=False)
    task = db.Column(db.String(1000), nullable=True)

    def __repr__(self):
        return f"Homework('{self.subject}', '{self.task}')"

# Create tables
db.create_all()

# Function to load homework from the database
def load_homework():
    homework_list = Homework.query.all()
    homework_dict = {homework.subject: homework.task for homework in homework_list}
    return homework_dict

# Function to save homework to the database
def save_homework(homework_dict):
    for subject, task in homework_dict.items():
        homework = Homework.query.filter_by(subject=subject).first()
        if homework:
            homework.task = task
        else:
            new_homework = Homework(subject=subject, task=task)
            db.session.add(new_homework)
    db.session.commit()

# Function to save homework to GitHub
def save_homework_to_github(homework_dict):
    file_path = 'homework.json'
    content = json.dumps(homework_dict, ensure_ascii=False, indent=4)
    
    # Get SHA of the file to update it on GitHub
    response = requests.get(API_URL, headers={
        'Authorization': f'token {GITHUB_TOKEN}'
    })
    
    if response.status_code == 200:
        sha = response.json()['sha']
    else:
        sha = None
        print(f"Failed to get SHA: {response.status_code} - {response.text}")
        return  # Exit if error on getting SHA
    
    data = {
        'message': 'Update homework',
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    
    if sha:
        data['sha'] = sha
    
    # Update or create file on GitHub
    response = requests.put(API_URL, headers={
        'Authorization': f'token {GITHUB_TOKEN}'
    }, json=data)
    
    if response.status_code in [200, 201]:
        print(f'File successfully {"updated" if sha else "created"} on GitHub')
    else:
        print(f'Error saving to GitHub: {response.status_code} - {response.text}')

# Load the current homework data
homework_dict = load_homework()

# Save homework to the database and GitHub
save_homework(homework_dict)
save_homework_to_github(homework_dict)

# Create the keyboards
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


# Bot message handlers
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
        if message.from_user.id in ADMIN_IDS:
            bot.reply_to(
                message,
                "<b>Виберіть предмет</b> для редагування домашнього завдання:",
                reply_markup=create_subjects_keyboard(),
                parse_mode='HTML'
            )
        else:
            bot.reply_to(message, "<b>😢 Упс, вибачте, але ви не адміністратор. 🚫</b>", parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == "Назад ⬅️")
def go_back(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "Виберіть одну з опцій нижче:",
            reply_markup=create_main_keyboard(),
            parse_mode='HTML'
        )


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


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=10000, debug=True)
