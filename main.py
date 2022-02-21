import json

import telebot
from telebot import apihelper, types

import config

apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(config.TOKEN)

with open("data/meta.json") as f:
    data_meta = json.load(f)

sessions = dict()


def get_or_create_session(user_id):
    try:
        return sessions[user_id]
    except KeyError:
        sessions[user_id] = dict()
        return sessions[user_id]


@bot.middleware_handler(update_types=["message"])
def set_session(bot_instance, message):
    bot_instance.session = get_or_create_session(message.from_user.id)


@bot.message_handler(commands=["start"])
def welcome(message):
    print(bot.session)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Критическая ситуация")
    item2 = types.KeyboardButton("Дополнительная информация")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Добро пожаловать. выберите действие", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def ask_problem(message):
    print(bot.session)
    if message.chat.type == "private":
        if message.text == "Критическая ситуация":
            markup = types.InlineKeyboardMarkup()
            for pet_id, pet_info in data_meta["pet_help"].items():
                item = types.InlineKeyboardButton(text=pet_info["name"], callback_data=pet_id)
                markup.add(item)
            bot.send_message(message.chat.id, "Какое у вас животное?", reply_markup=markup)

        if message.text == "Дополнительная информация":
            bot.send_message(message.chat.id, "Что вы хотите узнать?")


@bot.callback_query_handler(func=lambda query: query.data in data_meta["pet_help"])
def select_pet(query):
    print(bot.session)
    bot.session["pet"] = query.data
    markup = types.InlineKeyboardMarkup()
    for problem_id, problem_info in data_meta["pet_help"][bot.session["pet"]]["problems"].items():
        item = types.InlineKeyboardButton(text=problem_info["title"], callback_data=problem_id)
        markup.add(item)
    bot.send_message(query.message.chat.id, f"хорошо. у вас {bot.session['pet']}. Что случилось?", reply_markup=markup)


@bot.callback_query_handler(
    func=lambda query: bot.session["pet"] is not None
    and query.data in data_meta["pet_help"][bot.session["pet"]]["problems"]
)
def select_problem(query):
    print(bot.session)
    bot.session["problem"] = query.data
    filename = data_meta["pet_help"][bot.session["pet"]]["problems"][bot.session["problem"]]["text"]
    with open(f"data/pet_help/{bot.session['pet']}/{filename}") as f:
        solution = f.read()
    bot.send_message(query.message.chat.id, solution)


bot.polling(none_stop=True)
