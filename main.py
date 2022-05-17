import json
from string import Template

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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Критическая ситуация 🆘"))
    markup.add(types.KeyboardButton("Подписаться на рассылку"))
    name = message.from_user.first_name
    msg = Template(messages.commands['greeting']).safe_substitute(name=name)
    bot.send_message(message.chat.id, msg, reply_markup=markup)


@bot.message_handler(content_types=["text"])
def ask_problem(message):
    if message.chat.type == "private":
        if message.text == "Критическая ситуация 🆘":
            markup = types.InlineKeyboardMarkup()
            for pet_id, pet_emergency in messages.emergency.items():
                item = types.InlineKeyboardButton(text=pet_emergency.name, callback_data=pet_emergency.id)
                markup.add(item)
            bot.send_message(message.chat.id, messages.commands['pet_select'], reply_markup=markup)

        if message.text == "Подписаться на рассылку":
            bot.send_message(message.chat.id, "Подписка в разработке")

def match_pet_query(pet_query):
    return pet_query.data in messages.emergency

@bot.callback_query_handler(func=match_pet_query)
def select_pet(pet_query):
    bot.session["pet"] = pet_query.data
    markup = types.InlineKeyboardMarkup()
    pet_id = bot.session["pet"]
    for problem in messages.emergency[pet_id].problems:
        item = types.InlineKeyboardButton(text=problem.title, callback_data=problem.id)
        markup.add(item)
    pet_name = bot.session['pet']
    bot.send_message(pet_query.message.chat.id, messages.commands['emergency_select'], reply_markup=markup)


def match_problem_query(problem_query):
    pet_name = bot.session["pet"]
    pet_selected = pet_name is not None
    match_problem = problem_query.data in messages.emergency[pet_name].problems
    return pet_selected and match_problem

@bot.callback_query_handler(func=match_problem_query)
def select_problem(query):
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
