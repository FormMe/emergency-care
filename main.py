import json

import telebot
from telebot import apihelper, types

import config
from messages import Messages

apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(config.TOKEN)

messages = Messages("data/messages.json")

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
            for pet_id, pet_emergency in messages.emergency.items():
                item = types.InlineKeyboardButton(text=pet_emergency.name, callback_data=pet_emergency.id)
                markup.add(item)
            bot.send_message(message.chat.id, "Какое у вас животное?", reply_markup=markup)

        if message.text == "Дополнительная информация":
            bot.send_message(message.chat.id, "Что вы хотите узнать?")

def match_pet_query(pet_query):
    return pet_query.data in messages.emergency

@bot.callback_query_handler(func=match_pet_query)
def select_pet(pet_query):
    print(bot.session)
    bot.session["pet"] = pet_query.data
    markup = types.InlineKeyboardMarkup()
    pet_id = bot.session["pet"]
    for problem in messages.emergency[pet_id].problems:
        item = types.InlineKeyboardButton(text=problem.title, callback_data=problem.id)
        markup.add(item)
    pet_name = bot.session['pet']
    bot.send_message(pet_query.message.chat.id, f"хорошо. у вас {pet_name}. Что случилось?", reply_markup=markup)


def match_problem_query(problem_query):
    pet_name = bot.session["pet"]
    pet_selected = pet_name is not None
    match_problem = problem_query.data in messages.emergency[pet_name].problems
    return pet_selected and match_problem

@bot.callback_query_handler(func=match_problem_query)
def select_problem(query):
    print(bot.session)
    bot.session["problem"] = query.data
    selected_pet = bot.session["pet"]
    selected_problem = bot.session["problem"]
    problem = messages.emergency[selected_pet][selected_problem]
    if problem is not None:
        msg = problem.msg
    else:
        msg = "Problem not found"
    
    bot.send_message(query.message.chat.id, msg)


bot.polling(none_stop=True)
