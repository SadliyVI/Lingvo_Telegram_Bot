import configparser
import random
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


config = configparser.ConfigParser()
config.read('settings.ini')
TOKEN = config['Tokens']['TOKEN']

bot=telebot.TeleBot(TOKEN)

data_set = {'user_id': '', 'translate_direction': '', 'current_word': '' }

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово ➖'
    NEXT_WORD = 'Следующее слово ⏩'
    BACK = 'Назад ↩️'
    END = 'Закончить урок ❌'

class Labels:
    START_LABEL = 'Начинаем!🆕\nВыбери направление перевода:'

def get_start_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    en_ru_btn = types.InlineKeyboardButton('EN ➡️ RU', callback_data =
    'en_ru_direction')
    ru_en_btn = types.InlineKeyboardButton('RU ➡️ EN', callback_data =
    'ru_en_direction')
    return markup.add(en_ru_btn, ru_en_btn)


def get_select_dict_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    base_dict = types.InlineKeyboardButton('Все слова 📚',
                                           callback_data='all_words')
    user_dict = types.InlineKeyboardButton('Мои слова 📖',
                                           callback_data='my_words')
    backstate_btn = types.InlineKeyboardButton(Command.BACK,
                                               callback_data='go_back_direction')
    return markup.add(base_dict, user_dict, backstate_btn)

def get_translation_menu(target_word, other_words):
    markup = types.ReplyKeyboardMarkup(row_width = 2)
    target_word_btn = types.KeyboardButton(target_word)
    other_word_btns = [types.KeyboardButton(word) for word in other_words]
    buttons = [target_word_btn] + other_word_btns
    random.shuffle(buttons)
    next_word_btn = types.KeyboardButton(Command.NEXT_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    close_btn = types.InlineKeyboardButton(Command.END,
                                           callback_data='end_lesson')
    buttons.extend([add_word_btn, delete_word_btn, next_word_btn, close_btn])
    return markup.add(*buttons)

@bot.message_handler(commands = ['start'])
def start_command(message):
    bot.send_message(message.chat.id, Labels.START_LABEL,
                     reply_markup = get_start_menu())
    data_set['user_id'] = message.from_user.id

@bot.callback_query_handler(func = lambda call:True)
def callback_start_command(call):
    if call.message:
        if call.data == 'en_ru_direction':
            data_set['translate_direction'] = 'en_ru_direction'
            bot.edit_message_text(chat_id = call.message.chat.id,
                             message_id = call.message.message_id,
                             text = 'Вы выбрали EN ➡️ RU перевод.\n'
                                    'Выберите словарь для изучения:',
                             reply_markup = get_select_dict_menu())
        elif call.data == 'ru_en_direction':
            data_set['translate_direction'] = 'ru_en_direction'
            bot.edit_message_text(chat_id = call.message.chat.id,
                             message_id = call.message.message_id,
                             text = 'Вы выбрали RU ➡️ EN перевод\n'
                                    'Выберите словарь для изучения:',
                             reply_markup = get_select_dict_menu())
        elif call.data == 'go_back_direction':
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text = Labels.START_LABEL,
                                  reply_markup = get_start_menu())
        elif call.data == 'all_words':
            data_set['current_word'] = 'one'
            if data_set['translate_direction'] == 'en_ru_direction':
                header_text = f'Translate word:\n➡️ {data_set['current_word']}'
            else:
                header_text = (f'Переведи слово:\n➡️'
                               f' {data_set['current_word']}')
            bot.send_message(call.message.chat.id, header_text,
                             reply_markup = get_translation_menu('1',
                                                    ['2', '3', '4']))






# @bot.message_handler(func = lambda message: True, content_types = 'text')
# def select_dict_reply(message):
#     if message.text == 'all_words':
#             data_set['current_word'] = 'one'
#             if data_set['translate_direction'] == 'en_ru_direction':
#                 header_text = f'Translate word:\n➡️ {data_set['current_word']}'
#             else:
#                 header_text = (f'Переведи слово:\n➡️'
#                                f' {data_set['current_word']}')
#             bot.send_message(message.chat.id, header_text,
#                              reply_markup = get_translation_menu('1',
#                                                     ['2', '3', '4']))




# @bot.message_handler(content_types = ['text'])
# def translate_word(message):
#     header_text = ''
#     if data_set['translate_direction'] == 'en_ru_direction':
#         header_text = 'Translate word: '
#     else: header_text = 'Переведи слово: '
#
#     if message.text == 'all_words':
#         bot.send_message(message.chat.id, header_text,
#                          reply_markup = get_translation_menu('1',
#                                                    ['2','3', '4']))


    # original_word = ''
    # target_word = ''
    # first_word = ''
    # second_word = ''
    # third_word = ''
    # other_words = [first_word, second_word, third_word]


# @bot.callback_query_handler(func=lambda call: True)
# def callback_query(call):
#     if call.data == "button1":
#         bot.answer_callback_query(call.id, "Вы нажали кнопку 1")
#     elif call.data == "button2":
#         bot.answer_callback_query(call.id, "Вы нажали кнопку 2")

    # markup = types.ReplyKeyboardMarkup(row_width = 2)
    # target_word_btn = types.KeyboardButton(target_word)
    # other_word_btns = [types.KeyboardButton(word) for word in other_words]
    # buttons = [target_word_btn] + other_word_btns
    # random.shuffle(buttons)
    # next_word_btn = types.KeyboardButton(Command.NEXT_WORD)
    # delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    # add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    # buttons.extend([add_word_btn, delete_word_btn, next_word_btn,])
    # markup.add(*buttons)

    # bot.send_message(message.chat.id, f'Переведи слово:\n {rus_word}',
    #                  reply_markup = markup)

# @bot.message_handler(commands = ['start'])
# def welcome(message):
#     chat_id = message.chat.id
#     keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True)
#     button_support = telebot.types.KeyboardButton(text = 'Написать в '
#                                                          'поддержку')
#     keyboard.add(button_support)
#     bot.send_message(chat_id,
#                      f'Добро пожаловать в бота сбора обратной связи',
#                      reply_markup = keyboard)

# @bot.message_handler(commands = ['start'])
# def start_command(message):
# 	bot.send_message(message.chat.id,'Привет')

# @bot.message_handler(commands = ['button'])
# def button_command(message):
#     chat_id = message.chat.id
# 	keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
# 	button_support = types.KeyboardButton('Начать')
#     keyboard.add(button_support)
#     bot.send_message(chat_id,'Выберите что вам надо',
#                     reply_markup = keyboard)
# def start_markup():
#     markup = InlineKeyboardMarkup()
#     markup.row_width = 1
#     markup.add(InlineKeyboardButton("Старт", callback_data="start_command"))
#     return markup
#
# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.reply_to(message, "Нажмите кнопку 'Старт' для начала:", reply_markup=start_markup())
#
# @bot.callback_query_handler(func=lambda call: True)
# def callback_query(call):
#     if call.data == "start_command":
#         bot.answer_callback_query(call.id, "Выполняется команда /start")
#         bot.send_message(call.message.chat.id, "Вы нажали кнопку Старт! Бот запущен.")
# @bot.message_handler(commands=['start'])
# def welcome(message):
#     chat_id = message.chat.id
#     keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
#     button_support = telebot.types.KeyboardButton(text='Написать в поддержку')
#     keyboard.add(button_support)
#     bot.send_message(chat_id,
#                      'Добро пожаловать в бота сбора обратной связи',
#                      reply_markup = keyboard)

# bot.infinity_polling()
if __name__ == '__main__':
    bot.polling(none_stop=True)