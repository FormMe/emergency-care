import json
from string import Template

import telebot
from telebot import apihelper, types

import config
from messages import Messages
from vets import Vets

apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(config.TOKEN)

messages = Messages("data/messages.json")
vets = Vets("data/vets.json")

sessions = dict()


def get_or_create_session(user_id):
    try:
        return sessions[user_id]
    except KeyError:
        sessions[user_id] = dict()
        return sessions[user_id]


@bot.middleware_handler(update_types=["message", "callback_query"])
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
    pet_name = bot.session.get("pet")
    if pet_name is None:
        error_msg = 'Сначала выберите какой у вас питомец. Выберите "Критическая ситуация 🆘" в меню и следуйте инструкциям'
        bot.send_message(problem_query.message.chat.id, error_msg)
        return False
    match_problem = problem_query.data in messages.emergency[pet_name].problems
    return match_problem

@bot.callback_query_handler(func=match_problem_query)
def select_problem(problem_query):
    bot.session["problem"] = problem_query.data
    selected_pet = bot.session.get("pet")
    selected_problem = bot.session["problem"]
    problem = messages.emergency[selected_pet][selected_problem]
    if problem is not None:
        msg = problem.msg
    else:
        msg = "Problem not found"
    
    bot.send_message(problem_query.message.chat.id, msg)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Выбрать клинику в своем районе", callback_data="select_vet"))
    bot.send_message(problem_query.message.chat.id, "Главное сейчас - действовать оперативно и спокойно!", reply_markup=markup)


def match_vet_query(vet_query):
    return vet_query.data == "select_vet"

@bot.callback_query_handler(func=match_vet_query)
def select_vet(vet_query):
    bot.session["city"] = "Санкт-Петербург"
    markup = types.InlineKeyboardMarkup()
    for district in vets.get_districts(bot.session["city"]):
        item = types.InlineKeyboardButton(text=district, callback_data=district)
        markup.add(item)
    bot.send_message(vet_query.message.chat.id, "Чтобы мы могли найти список ближайших ветклиник, выбери, пожалуйста, свой район", reply_markup=markup)


def match_disctrict_query(disctrict_query):
    city = bot.session.get("city", "Санкт-Петербург")
    match_discrict = disctrict_query.data in vets.get_districts(city)
    return match_discrict

@bot.callback_query_handler(func=match_disctrict_query)
def select_disctrict(disctrict_query):
    bot.session["discrict"] = disctrict_query.data
    city = bot.session.get("city", "Санкт-Петербург")
    district = bot.session["discrict"]
    
    selected_vets = vets.get_vets(city, district)
    msg = "\n\n".join(map(str, selected_vets))
    msg = f"*{district} район.* Список клиник:\n\n{msg}"
    bot.send_message(disctrict_query.message.chat.id, msg, parse_mode= 'Markdown')


bot.polling(none_stop=True)
