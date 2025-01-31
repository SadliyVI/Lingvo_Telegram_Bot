import logging
import db_manager as dbm
import configparser
import random
import telebot
from telebot import types, TeleBot, State
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from models import (RussianWord, EnglishWord, RussianEnglishAssociation,
                    LearnedWord, User)

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('settings.ini')
TOKEN = config['Tokens']['TOKEN']

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage = state_storage)

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
    russian_added_word = State()
    english_added_word = State()

class DeleteWordStates(StatesGroup):
    deleted_word = State()


def get_start_menu():
    markup = types.InlineKeyboardMarkup(row_width = 2)
    en_ru_btn = types.InlineKeyboardButton('EN ➡️ RU', callback_data =
    'en_ru_direction')
    ru_en_btn = types.InlineKeyboardButton('RU ➡️ EN', callback_data =
    'ru_en_direction')
    return markup.add(en_ru_btn, ru_en_btn)


def get_select_dict_menu():
    markup = types.InlineKeyboardMarkup(row_width = 3)
    base_dict = types.InlineKeyboardButton('Все слова 📚',
                                           callback_data = 'all_words')
    user_dict = types.InlineKeyboardButton('Мои слова 📖',
                                           callback_data = 'my_words')
    backstate_btn = types.InlineKeyboardButton(Command.BACK,
                                         callback_data = 'go_back_direction')
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

def create_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton('Да', callback_data = 'confirm'),
              InlineKeyboardButton('Нет', callback_data = 'cancel')
    )
    return keyboard






@bot.message_handler(commands = ['start'])
def start_command(message):
    bot.send_message(message.chat.id, Labels.START_LABEL,
                     reply_markup = get_start_menu())
    dbm.create_user(message.from_user.id, session)

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
    if call.data == 'confirm':
        success, message_text = reset_users_progress(call.from_user.id,
                                                     session)
        bot.answer_callback_query(call.id, text = message_text)
        bot.edit_message_text(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            text = message_text
        )
        if success:
            bot.send_message(call.message.chat.id,
                        'Выберите следующее действие:',
                             reply_markup = get_translation_menu())
    elif call.data == 'cancel':
        bot.answer_callback_query(call.id,
                                  text = 'Сброс прогресса отменен!')
        bot.edit_message_text(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            text = 'Сброс прогресса отменен.'
        )
        bot.send_message(call.message.chat.id,
                         'Выберите следующее действие:',
                         reply_markup = get_translation_menu())



@bot.message_handler(func = lambda message: message.text == Command.ADD_WORD)
def handle_add_word(message):
    bot.send_message(message.chat.id, 'Введите русское слово:',
                     reply_markup = ReplyKeyboardRemove())
    bot.register_next_step_handler(message, handle_russian_word)

def handle_russian_word(message):
    russian_word = message.text.lower()
    bot.set_state(message.from_user.id,
                  AddWordStates.russian_added_word,
                  message.chat.id
                  )
    # logger.info(f'Received message: {message.text}')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['russian_word'] = russian_word
        # logger.info(f'Current state data: {data}')
    bot.send_message(message.chat.id, 'Теперь введите соответствующий '
                                      'русскому слову английский перевод:')
    bot.set_state(message.from_user.id, AddWordStates.english_added_word,
                  message.chat.id)
    bot.register_next_step_handler(message, handle_english_word)
    # logger.info(f'User {message.from_user.id} entered Russian word: '
    #             f'{russian_word}. Waiting for English translation.')

def handle_english_word(message):
    english_word = message.text.lower()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        russian_word = data['russian_word']
    # logger.info(f'User {message.from_user.id} entered English word: '
    #             f'{english_word}. Waiting for storing words in DB.')
    if dbm.create_user(message.from_user.id, session):
        try:
            ru_word = RussianWord(ru_word = russian_word)
            en_word = EnglishWord(en_word = english_word)
            session.add_all([ru_word, en_word])
            session.flush()
            word_association = RussianEnglishAssociation(
                russian_word_id = ru_word.id,
                english_word_id = en_word.id
            )
            # logger.info(f'Created association: {word_association}')
            user_id = session.query(User.id).filter(
                User.username == message.from_user.id).first()[0]
            user_association = RuWordUserAssociation(russian_word_id = ru_word.id,
                                                     user_id = user_id)
            # logger.info(f'Created association: {user_association}')
            session.add_all([word_association, user_association])
            session.commit()

            bot.send_message(message.chat.id,
                             f'Пара слов {russian_word} - {english_word} '
                             f'успешно добавлена в словарь.')
        except Exception as e:
            session.rollback()
            bot.send_message(message.chat.id,
                             f'Произошла ошибка при добавлении слова: {str(e)}')
        finally:
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.chat.id, 'Выберите следующее действие:',
                             reply_markup = get_translation_menu())
    else:
        bot.send_message(message.chat.id,
                         'Произошла ошибка при добавлении пользователя в '
                         'базу данных!',
                         reply_markup = get_translation_menu())


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def handle_delete_word(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите слово для удаления '
                              '(на русском или английском):',
                              reply_markup = ReplyKeyboardRemove())
    bot.register_next_step_handler(message, handle_word_to_delete)

def handle_word_to_delete(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    word_to_delete = message.text.lower()
    try:
        ru_word = session.query(RussianWord).filter(RussianWord.ru_word ==
                                                    word_to_delete).first()
        en_word = session.query(EnglishWord).filter(EnglishWord.en_word ==
                                                    word_to_delete).first()
        if ru_word:
            associations = session.query(RussianEnglishAssociation).filter_by(
                russian_word_id = ru_word.id).all()
            for items in associations:
                other_items = session.query(RussianEnglishAssociation).filter(
                    RussianEnglishAssociation.english_word_id == items.english_word_id,
                    RussianEnglishAssociation.russian_word_id != ru_word.id
                ).first()
                if not other_items:
                    en_word_to_delete = session.get(EnglishWord,
                                                    items.english_word_id)
                    if en_word_to_delete:
                        session.delete(en_word_to_delete)
                session.delete(items)
            session.delete(ru_word)
            session.commit()
            bot.send_message(chat_id,
                             f'Слово - {word_to_delete} - и его уникальные '
                             f'переводы удалены из словаря.')
        elif en_word:
            associations = session.query(RussianEnglishAssociation).filter_by(
                english_word_id=en_word.id).all()
            for items in associations:
                other_items = session.query(RussianEnglishAssociation).filter(
                    RussianEnglishAssociation.russian_word_id == items.russian_word_id,
                    RussianEnglishAssociation.english_word_id != en_word.id
                ).first()
                if not other_items:
                    ru_word_to_delete = session.get(RussianWord,
                                                    items.russian_word_id)
                    if ru_word_to_delete:
                        session.delete(ru_word_to_delete)
                session.delete(items)
            session.delete(en_word)
            session.commit()
            bot.send_message(chat_id,
                             f'Слово - {word_to_delete} - и его уникальные '
                             f'переводы удалены из словаря.')
        else:
            bot.send_message(chat_id, f'Слово - {word_to_delete} - '
                                      f'не найдено в словаре.')
    except Exception as e:
        session.rollback()
        bot.send_message(chat_id, f'Произошла ошибка при удалении слова: {str(e)}')
    finally:
        bot.send_message(chat_id, 'Выберите следующее действие:',
                         reply_markup = get_translation_menu())

@bot.message_handler(commands = ['reset_progress'])
def handle_reset_progress(message):
    user_name = message.from_user.id
    bot.send_message(message.chat.id,
                'Вы уверены, что хотите сбросить весь прогресс обучения? '
                     'Это действие нельзя отменить!',
                     reply_markup = create_confirmation_keyboard())


# @bot.callback_query_handler(func = lambda call: call.data in [
#                             'confirm', 'cancel'])

# def callback_reset_progress(call):
#     if call.data == 'confirm':
#         success, message_text = reset_users_progress(call.from_user.id,
#                                                      session)
#         bot.answer_callback_query(call.id, text = message_text)
#         bot.edit_message_text(
#             chat_id = call.message.chat.id,
#             message_id = call.message.message_id,
#             text = message_text
#         )
#         if success:
#             bot.send_message(call.message.chat.id,
#                         'Выберите следующее действие:',
#                              reply_markup = get_translation_menu())
#     else:
#         bot.answer_callback_query(call.id,
#                                   text = 'Сброс прогресса отменен!')
#         bot.edit_message_text(
#             chat_id = call.message.chat.id,
#             message_id = call.message.message_id,
#             text = 'Сброс прогресса отменен.'
#         )
#         bot.send_message(call.message.chat.id,
#                          'Выберите следующее действие:',
#                          reply_markup = get_translation_menu())

def reset_users_progress(user_id, session):
    try:
        user = session.query(User).filter(User.username == user_id).first()
        if not user:
            return False, 'Пользователь не найден!'
        deleted = session.query(LearnedWord).filter(
            LearnedWord.user_name == user.username).delete()
        session.commit()
        return True, f'Прогресс сброшен. Удалено {deleted} выученных слов(а)!'
    except Exception as e:
        session.rollback()
        return False, f'Произошла ошибка при сбросе прогресса: {str(e)}'













@bot.message_handler(func = lambda message: True, content_types = ['text'])
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    current_state = bot.get_state(user_id, chat_id)
    logger.info(f"Received message: '{message.text}', Current state: {current_state}")


if __name__ == '__main__':
    bot.polling(none_stop=True)