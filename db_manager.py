import configparser
import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
from models import (
                    User, RussianWord, EnglishWord, LearnedWord,
                    RussianEnglishAssociation
)

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

    with open(path, encoding ='utf-8') as f:
        data = json.load(f)
    for item in data:
        model = item['model']
        fields = item['fields']
        if model == 'User':
            user = User(username = fields['username'])
            session.add(user)
            session.commit()
        elif model == 'Word':
            rus_dict = session.query(RussianWord).all()
            for c in rus_dict:
                print(c)
            eng_dict = session.query(EnglishWord).all()
            for a in eng_dict:
                print(a)
            if not rus_dict or all(fields['ru_word'] != r.ru_word for r in
                                   rus_dict):
                rus_word = RussianWord(ru_word = fields['ru_word'],
                                       user_name = fields['user_id'])

                if all(fields['en_word'] != e.en_word for e in eng_dict):
                    eng_word = EnglishWord(en_word = fields['en_word'])
                    session.add_all([rus_word, eng_word])
                    session.commit()
                    word_association = RussianEnglishAssociation(
                        russian_word_id = rus_word.id,
                        english_word_id = eng_word.id)
                    session.add(word_association)
                    session.commit()
                else:
                    session.add(rus_word)
                    session.commit()
                    word_association = RussianEnglishAssociation(
                        russian_word_id = rus_word.id,
                        english_word_id = eng_word.id)
                    session.add(word_association)
                    session.commit()
            else:
                word_association_pair = session.query(
                    RussianEnglishAssociation).all()
                for item in word_association_pair:
                    if (item.russian_word_id == rus_word.id and
                        all(fields['en_word'] != e.en_word for e in eng_dict)):
                        eng_word = EnglishWord(en_word = fields['en_word'])
                        session.add(eng_word)
                        session.commit()
                        word_association = RussianEnglishAssociation(
                            russian_word_id = rus_word.id,
                            english_word_id = eng_word.id)
                        session.add(word_association)
                        session.commit()
                    else:
                        print(f'Пара слов {fields['ru_word']} - '
                              f'{fields['en_word']} уже есть в '
                              f'словаре')


def create_user(username, session):
    """
    Create a new user in the database.

    This function attempts to create a new user with the given username
    and add it to the database. If successful, it returns the newly created
    user object. If a user with the same username already exists, it returns None.

    Parameters:
    username (str): The username for the new user.
    session (sqlalchemy.orm.session.Session): An active SQLAlchemy session
        for database operations.

    Returns:
    User or None: The newly created User object if successful, None if a user
        with the same username already exists in the database.
    """

    new_user = User(username = username)
    session.add(new_user)
    try:
        session.commit()
        return new_user
    except IntegrityError:
        session.rollback()
        return None


def create_russian_word(ru_word, user_name, session):
    new_word = RussianWord(ru_word = ru_word, user_name = user_name)
    session.add(new_word)
    try:
        session.commit()
        return new_word
    except IntegrityError:
        session.rollback()
        return None

def create_english_word(en_word, session):
    new_word = EnglishWord(en_word = en_word)
    session.add(new_word)
    try:
        session.commit()
        return new_word
    except IntegrityError:
        session.rollback()
        return None

def create_word_association(russian_word_id, english_word_id, session):
    new_association = RussianEnglishAssociation(
        russian_word_id = russian_word_id,
        english_word_id = english_word_id)
    session.add(new_association)
    try:
        session.commit()
        return new_association
    except IntegrityError:
        session.rollback()
        return None



def mark_word_as_learned(russian_word_id, english_word_id, user_name, session):
    learned_word = LearnedWord(
        russian_word_id = russian_word_id,
        english_word_id = english_word_id,
        user_name = user_name)
    session.add(learned_word)
    try:
        session.commit()
        return learned_word
    except IntegrityError:
        session.rollback()
        return None

# Read (Select) functions

def get_user_by_username(username, session):
    return session.query(User).filter(User.username == username).first()

def get_russian_word(ru_word, session):
    return session.query(RussianWord).filter(RussianWord.ru_word == ru_word).first()

def get_english_word(en_word, session):
    return session.query(EnglishWord).filter(EnglishWord.en_word == en_word).first()

def get_word_association(russian_word_id, english_word_id, session):
    return session.query(RussianEnglishAssociation).filter(
        RussianEnglishAssociation.russian_word_id == russian_word_id,
        RussianEnglishAssociation.english_word_id == english_word_id
    ).first()

def get_learned_words(user_name, session):
    return session.query(LearnedWord).filter(LearnedWord.user_name == user_name).all()

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

def get_word_for_study(dictionary_type, translate_direction):
    if dictionary_type == 'all_words':
        if translate_direction == 'ru_en_direction':
            pass
        elif translate_direction == 'en_ru_direction':
            pass
    else:
        if translate_direction == 'ru_en_direction':
            pass
        elif translate_direction == 'en_ru_direction':
            pass

