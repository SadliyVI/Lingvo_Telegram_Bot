import configparser
import json
import sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
from models import (
                    User, RussianWord, EnglishWord, LearnedWord,
                    RussianEnglishAssociation
)
import random



def create_engine():
    """
    Create and return a SQLAlchemy engine instance for database connection.

    This function reads database configuration from a 'settings.ini' file
    and uses it to create a SQLAlchemy engine for a PostgreSQL database.
    The database connection string is constructed using the provided
    parameters.

    Returns:
        sqlalchemy.engine.base.Engine: A SQLAlchemy engine instance
        configured for the specified PostgreSQL database.

    Note:
        This function assumes the existence of a 'settings.ini' file
        with a [Tokens] section containing db_name, user, password,
        host, and port fields.
    """
    config = configparser.ConfigParser()
    config.read('settings.ini')
    db_name = config['Tokens']['db_name']
    user = config['Tokens']['user']
    password = config['Tokens']['password']
    host = config['Tokens']['host']
    port = config['Tokens']['port']
    DSN = f'postgresql://{user}:{password}@{host}:{port}/{db_name}'
    engine = sqlalchemy.create_engine(DSN)
    return engine

def create_session(engine):
    """
    Create and return a new SQLAlchemy session.

    This function creates a new SQLAlchemy session using the provided engine.
    The session is used for database operations and transaction management.

    Parameters:
    engine (sqlalchemy.engine.base.Engine): A SQLAlchemy engine instance
        connected to the database.

    Returns:
    sqlalchemy.orm.session.Session: A new SQLAlchemy session bound to the
        provided engine.
    """

    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def download_data_from_json(session, path):
    """
    Download and process data from a JSON file, adding it to the database.

    This function reads data from a JSON file, processes it, and adds the information
    to the database using the provided SQLAlchemy session. It handles two types of
    data: User and Word. For Word data, it creates RussianWord and EnglishWord entries,
    as well as associations between them.

    Used for loading the basic dictionary.

    Parameters:
    session (sqlalchemy.orm.session.Session): An active SQLAlchemy session for
        database operations.
    path (str): The file path to the JSON file containing the data to be processed.

    Returns:
    None

    Note:
    - The function assumes specific structures for User and Word data in the JSON file.
    - It prints debug information about existing Russian and English words.
    - If a word pair already exists in the database, it prints a message in Russian.
    """

    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for item in data:
        model = item['model']
        fields = item['fields']
        if model == 'User':
            create_user(username = fields['username'], session = session)
        elif model == 'Word':
            user_id = create_user(username = fields['user_id'],
                                  session = session)
            if user_id:
                print(f'Пользователь -{fields['user_id']}- успешно добавлен '
                      f'в базу данных!')
            else:
                print(f'При добавлении пользователя -{fields['user_id']}- '
                      f'в базу данных произошла ошибка!')
            russian_word_id = create_russian_word(ru_word = fields['ru_word'],
                                                  session = session)
            if russian_word_id:
                print(f'Русское слово -{fields['ru_word']}- успешно '
                      f'добавлено в словарь пользователя '
                      f'-{fields['user_id']}-!')
            else:
                print(f'При добавлении русского слова -{fields['ru_word']}- '
                      f'в базу данных произошла ошибка!')
            english_word_id = create_english_word(en_word = fields['en_word'],
                                                  session = session)
            if english_word_id:
                print(f'Английское слово -{fields['en_word']}- успешно '
                      f'добавлено в словарь пользователя '
                      f'-{fields['user_id']}-!')
            else:
                print(f'При добавлении английского слова '
                      f'-{fields['en_word']}- в базу данных произошла ошибка!')
            new_association = create_words_association(russian_word_id,
                                                       english_word_id,
                                                       user_id,
                                                       session)
            # if new_association:
            #     print('Связь между русским и английским словами '
            #               'успешно добавлена в базу данных!')
            if new_association == None:
                print('При добавлении связи между русским и английскими '
                      'словами в базу данных произошла ошибка!')
            elif new_association == False:
                print(f'Пара слов {fields['ru_word']} - {fields['en_word']} '
                      f'уже есть в словаре пользователя '
                      f'-{fields['user_id']}-!')

            # new_word_user_association = create_ru_word_user_association(
            #                                 russian_word_id, user_id, session)
            # # if new_word_user_association:
            # #     print('Связь между словами и пользователем успешно добавлена '
            # #           'в базу данных!')
            # if new_word_user_association == None:
            #     print('При добавлении связи между словами и пользователем в '
            #           'базу данных произошла ошибка!')
            # elif new_word_user_association == False:
            #     print(f'Связь, слово: {fields['ru_word']} - пользователь:'
            #           f' {fields['user_id']} уже есть в базе данных!')

def create_user(username, session):
    all_users = session.query(User.username).all()
    if all(username != user.username for user in all_users):
        new_user = User(username = username)
        session.add(new_user)
        try:
            session.commit()
            user_id = new_user.id
        except IntegrityError:
            session.rollback()
            return False
    else:
        user_id = session.query(User.id).filter(User.username ==
                                                username).first()[0]
    return user_id

def create_russian_word(ru_word, session):
    rus_dict = session.query(RussianWord).all()
    if not rus_dict or all(ru_word != r.ru_word for r in rus_dict):
        rus_word = RussianWord(ru_word = ru_word)
        session.add(rus_word)
        try:
            session.commit()
            ru_word_id = rus_word.id
        except IntegrityError:
            session.rollback()
            return False
    else:
        ru_word_id = session.query(RussianWord.id).filter(RussianWord.ru_word
                                                       == ru_word).first()[0]
    return ru_word_id

def create_english_word(en_word, session):
    eng_dict = session.query(EnglishWord).all()
    if not eng_dict or all(en_word != e.en_word for e in eng_dict):
        eng_word = EnglishWord(en_word = en_word)
        session.add(eng_word)
        try:
            session.commit()
            en_word_id = eng_word.id
        except IntegrityError:
            session.rollback()
            return False
    else:
        en_word_id = session.query(EnglishWord.id).filter(EnglishWord.en_word
                                                       == en_word).first()[0]
    return en_word_id

def create_words_association(russian_word_id, english_word_id, user_id,
                             session):
    words_associations =  session.query(RussianEnglishAssociation).all()
    existing_association = session.query(RussianEnglishAssociation).filter_by(
        russian_word_id = russian_word_id,
        english_word_id = english_word_id,
        user_id = user_id
    ).first()
    if existing_association and words_associations:
        return False
    else:
        new_association = RussianEnglishAssociation(
                                            russian_word_id = russian_word_id,
                                            english_word_id = english_word_id,
                                            user_id = user_id,

        )
        session.add(new_association)
        try:
            session.commit()
            return new_association
        except IntegrityError:
            session.rollback()
            return None

def mark_word_as_learned(russian_word_id, english_word_id, user_id, session):
    learned_word = session.query(LearnedWord).all()
    existing_combination = session.query(LearnedWord).filter_by(
        russian_word_id = russian_word_id,
        english_word_id = english_word_id,
        user_id = user_id
    ).first()
    if existing_combination and learned_word:
        return False
    else:
        new_learned_word = LearnedWord(
                                        russian_word_id = russian_word_id,
                                        english_word_id = english_word_id,
                                        user_id = user_id)
        session.add(learned_word)
        try:
            session.commit()
            return new_learned_word
        except IntegrityError as e:
            session.rollback()
            # print(e)
            return None


# Read (Select) functions

def get_user_by_username(username, session):
    return session.query(User).filter(User.username == username).first()

def get_russian_word(ru_word_id, session):
    return session.query(RussianWord).filter(
        RussianWord.id == ru_word_id).first()

def get_english_word(en_word_id, session):
    return session.query(EnglishWord).filter(
        EnglishWord.id == en_word_id).first()


def get_word_association(russian_word_id, english_word_id, session):
    return session.query(RussianEnglishAssociation).filter(
        RussianEnglishAssociation.russian_word_id == russian_word_id,
        RussianEnglishAssociation.english_word_id == english_word_id
    ).first()


def get_english_word_id(session, russian_word_id):
    association = session.query(RussianEnglishAssociation).filter(
        RussianEnglishAssociation.russian_word_id == russian_word_id
    ).first()
    if association:
        return association.english_word_id
    else:
        return None


def get_learned_words(username, session):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        return []
    return session.query(LearnedWord).filter(LearnedWord.user_id == user.id).all()








# Update functions

def update_russian_word(word_id, new_ru_word, session):
    word = session.query(RussianWord).filter(RussianWord.id == word_id).first()
    if word:
        word.ru_word = new_ru_word
        try:
            session.commit()
            return word
        except IntegrityError:
            session.rollback()
            return None
    return None


def update_english_word(word_id, new_en_word, session):
    word = session.query(EnglishWord).filter(EnglishWord.id == word_id).first()
    if word:
        word.en_word = new_en_word
        try:
            session.commit()
            return word
        except IntegrityError:
            session.rollback()
            return None
    return None


# Delete functions

def delete_user(username, session):
    user = session.query(User).filter(User.username == username).first()
    if user:
        session.delete(user)
        session.commit()
        return True
    return False


def delete_russian_word(word_id, session):
    word = session.query(RussianWord).filter(RussianWord.id == word_id).first()
    if word:
        session.delete(word)
        session.commit()
        return True
    return False


def delete_english_word(word_id, session):
    word = session.query(EnglishWord).filter(EnglishWord.id == word_id).first()
    if word:
        session.delete(word)
        session.commit()
        return True
    return False


def delete_word_association(russian_word_id, english_word_id, session):
    association = session.query(RussianEnglishAssociation).filter(
        RussianEnglishAssociation.russian_word_id == russian_word_id,
        RussianEnglishAssociation.english_word_id == english_word_id
    ).first()
    if association:
        session.delete(association)
        session.commit()
        return True
    return False


def unmark_learned_word(russian_word_id, english_word_id, user_name, session):
    learned_word = session.query(LearnedWord).filter(
        LearnedWord.russian_word_id == russian_word_id,
        LearnedWord.english_word_id == english_word_id,
        LearnedWord.user_name == user_name
    ).first()
    if learned_word:
        session.delete(learned_word)
        session.commit()
        return True
    return False


# def get_word_for_study(dictionary_type, translate_direction, user_name,
#                        session):
#     word_set = []
#     learned_words = get_learned_words(user_name, session)
#
#     if dictionary_type == 'all_words':
#         id_list = [id[0] for id in session.query(RussianWord.id).all()]
#     else:
#         id_list = [id[0] for id in session.query(RussianWord.id).filter(
#             RussianWord.username == user_name).all()]
#
#     if learned_words:
#         id_list = [id for id in id_list if
#                    id not in [word.russian_word_id for word in learned_words]]
#     if not id_list:
#         return word_set  # Возвращаем пустой список, если нет доступных слов
#
#     ru_word_id = random.choice(id_list)
#     en_word_id = get_english_word_id(session, ru_word_id)
#
#     if translate_direction == 'ru_en_direction':
#         word_set.append(get_russian_word(ru_word_id, session).ru_word)
#         word_set.append(get_english_word(en_word_id, session).en_word)
#
#         id_list.remove(ru_word_id)
#         other_words_ids = random.sample(id_list, k=min(3, len(id_list)))
#         for other_word_id in other_words_ids:
#             other_en_word_id = get_english_word_id(session, other_word_id)
#             word_set.append(
#                 get_english_word(other_en_word_id, session).en_word)
#
#     elif translate_direction == 'en_ru_direction':
#         word_set.append(get_english_word(en_word_id, session).en_word)
#         word_set.append(get_russian_word(ru_word_id, session).ru_word)
#
#         id_list.remove(ru_word_id)
#         other_words_ids = random.sample(id_list, k = min(3, len(id_list)))
#         for other_word_id in other_words_ids:
#             word_set.append(get_russian_word(other_word_id, session).ru_word)
#
#     return word_set


def get_word_for_study(dictionary_type, translate_direction, user_name,
                       session):
    word_set = []
    user = session.query(User).filter(User.username == user_name).first()
    if not user:
            return word_set
    learned_words = get_learned_words(user_name, session)
    learned_word_pairs = set((lw.russian_word_id, lw.english_word_id)
                              for lw in learned_words)

    if dictionary_type == 'all_words':
        available_words = session.query(RussianEnglishAssociation).all()
    else:
        available_words = session.query(RussianEnglishAssociation).filter(RussianEnglishAssociation.user_id == user.id).all()

    available_words = [w for w in available_words if (
    w.russian_word_id, w.english_word_id) not in learned_word_pairs]

    if not available_words:
        return word_set  # Return empty list if no available words

    chosen_pair = random.choice(available_words)
    russian_word = session.query(RussianWord).get(chosen_pair.russian_word_id)
    english_word = session.query(EnglishWord).get(chosen_pair.english_word_id)

    if translate_direction == 'ru_en_direction':
        word_set = [russian_word.ru_word, english_word.en_word]
        # Get 3 other random English words
        other_english_words = session.query(EnglishWord).filter(
            EnglishWord.id != english_word.id).order_by(
            func.random()).limit(3).all()
        word_set.extend([w.en_word for w in other_english_words])
    elif translate_direction == 'en_ru_direction':
        word_set = [english_word.en_word, russian_word.ru_word]
        # Get 3 other random Russian words
        other_russian_words = session.query(RussianWord).filter(
            RussianWord.id != russian_word.id).order_by(
            func.random()).limit(3).all()
        word_set.extend([w.ru_word for w in other_russian_words])

    # Shuffle the last 4 elements (correct answer + 3 random words)
    random.shuffle(word_set[1:])

    return word_set