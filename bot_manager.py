import db_manager as dbm
import configparser
import random
import telebot
from telebot import types, State
from telebot.handler_backends import State, StatesGroup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove

from models import RussianWord, EnglishWord, RussianEnglishAssociation

config = configparser.ConfigParser()
config.read('settings.ini')
TOKEN = config['Tokens']['TOKEN']

bot=telebot.TeleBot(TOKEN)

engine = dbm.create_engine()
session = dbm.create_session(engine)

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово ➖'
    NEXT_WORD = 'Следующее слово ⏩'
    BACK = 'Назад ↩️'
    END = 'Закончить урок ❌'

class Labels:
    START_LABEL = 'Начинаем!🆕\nВыбери направление перевода:'

class SessionDataSet():
    current_word = ''
    target_word = ''
    other_words = []
    used_words = []
    translate_direction = ''

class AddWordStates(StatesGroup):
    waiting_for_russian = State()
    waiting_for_english = State()

class DeleteWordStates(StatesGroup):
    waiting_for_word = State()


def get_start_menu():
    markup = types.InlineKeyboardMarkup(row_width = 2)
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

def get_translation_menu():
    markup = types.ReplyKeyboardMarkup(row_width = 2)
    target_word_btn = types.KeyboardButton(SessionDataSet.target_word)
    other_word_btns = [types.KeyboardButton(word) for word in
                       SessionDataSet.other_words]
    buttons = [target_word_btn] + other_word_btns
    random.shuffle(buttons)
    next_word_btn = types.KeyboardButton(Command.NEXT_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    close_btn = types.InlineKeyboardButton(Command.END)
    buttons.extend([add_word_btn, delete_word_btn, next_word_btn, close_btn])
    return markup.add(*buttons)

@bot.message_handler(commands = ['start'])
def start_command(message):
    bot.send_message(message.chat.id, Labels.START_LABEL,
                     reply_markup = get_start_menu())
    # data_set['user_id'] = message.from_user.id

@bot.callback_query_handler(func = lambda call:True)
def callback_start_command(call):
    if not call.message:
        return
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id

    if call.data in ['en_ru_direction', 'ru_en_direction']:
        SessionDataSet.translate_direction = call.data
        direction = 'EN ➡️ RU' if call.data == 'en_ru_direction' else 'RU ➡️ EN'
        text = f'Вы выбрали {direction} перевод.\nВыберите словарь для изучения:'
        bot.edit_message_text(chat_id = chat_id, message_id = message_id,
                              text = text,
                              reply_markup = get_select_dict_menu())
    elif call.data == 'go_back_direction':
        bot.edit_message_text(chat_id = chat_id, message_id = message_id,
                              text = Labels.START_LABEL,
                              reply_markup = get_start_menu())
    elif call.data in ['all_words', 'my_words']:
        word_list = dbm.get_word_for_study(call.data,
                                           SessionDataSet.translate_direction,
                                           user_id, session)

        if len([word for word in word_list if word]) < 5:
            notification = ('Недостаточно слов в словаре. Пожалуйста, '
                            'добавьте больше слов для изучения.')
            bot.answer_callback_query(call.id, text = notification,
                                      show_alert = True)
            return

        SessionDataSet.current_word, SessionDataSet.target_word, *SessionDataSet.other_words = word_list
        SessionDataSet.used_words.append(SessionDataSet.current_word)
        is_en_ru = SessionDataSet.translate_direction == 'en_ru_direction'
        header_text = (f'{'Translate word:' if is_en_ru else 'Переведи слово'} :\n'
                       f'👉{SessionDataSet.current_word}👈')
        task_text = f'{'Choose a translation option' if is_en_ru else 'Выбери вариант перевода'}:'
        bot.edit_message_text(chat_id = chat_id, message_id = message_id,
                              text = header_text)
        bot.send_message(chat_id, text = task_text,
                         reply_markup = get_translation_menu())

@bot.message_handler(func = lambda message: message.text == Command.ADD_WORD)
def handle_add_word(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите русское слово:",
                     reply_markup = ReplyKeyboardRemove())
    bot.set_state(message.from_user.id, AddWordStates.waiting_for_russian, chat_id)

@bot.message_handler(state  = AddWordStates.waiting_for_russian)
def handle_russian_word(message):
    chat_id = message.chat.id
    russian_word = message.text.lower()
    bot.send_message(chat_id, "Теперь введите английский перевод:")
    bot.set_state(message.from_user.id, AddWordStates.waiting_for_english, chat_id)
    bot.add_data(message.from_user.id, chat_id, russian_word = russian_word)

@bot.message_handler(state = AddWordStates.waiting_for_english)
def handle_english_word(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    english_word = message.text.lower()
    russian_word = bot.get_data(user_id, chat_id)['russian_word']

    try:
        # Add words to the database
        ru_word = RussianWord(ru_word = russian_word, user_name=user_id)
        en_word = EnglishWord(en_word=english_word)
        session.add_all([ru_word, en_word])
        session.flush()

        association = RussianEnglishAssociation(russian_word_id=ru_word.id,
                                                english_word_id=en_word.id)
        session.add(association)
        session.commit()

        bot.send_message(chat_id, f'Слово {russian_word} - {english_word} '
                                  f'успешно добавлено в словарь.')
    except Exception as e:
        session.rollback()
        bot.send_message(chat_id, f"Произошла ошибка при добавлении слова: {str(e)}")
    finally:
        bot.delete_state(user_id, chat_id)
        bot.send_message(chat_id, "Выберите следующее действие:", reply_markup=get_translation_menu())

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def handle_delete_word(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите слово для удаления (на русском или английском):", reply_markup=ReplyKeyboardRemove())
    bot.set_state(message.from_user.id, DeleteWordStates.waiting_for_word, chat_id)

@bot.message_handler(state=DeleteWordStates.waiting_for_word)
def handle_word_to_delete(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    word_to_delete = message.text.lower()

    try:
        # Check if the word exists in Russian or English
        ru_word = session.query(RussianWord).filter(RussianWord.ru_word == word_to_delete).first()
        en_word = session.query(EnglishWord).filter(EnglishWord.en_word == word_to_delete).first()

        if ru_word:
            # Delete the Russian word and its associations
            session.query(RussianEnglishAssociation).filter_by(russian_word_id=ru_word.id).delete()
            session.delete(ru_word)
            session.commit()
            bot.send_message(chat_id, f"Слово '{word_to_delete}' и его переводы успешно удалены из словаря.")
        elif en_word:
            # Delete the English word and its associations
            session.query(RussianEnglishAssociation).filter_by(english_word_id=en_word.id).delete()
            session.delete(en_word)
            session.commit()
            bot.send_message(chat_id, f"Слово '{word_to_delete}' и его переводы успешно удалены из словаря.")
        else:
            bot.send_message(chat_id, f"Слово '{word_to_delete}' не найдено в словаре.")
    except Exception as e:
        session.rollback()
        bot.send_message(chat_id, f"Произошла ошибка при удалении слова: {str(e)}")
    finally:
        bot.delete_state(user_id, chat_id)
        bot.send_message(chat_id, "Выберите следующее действие:", reply_markup=get_translation_menu())







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