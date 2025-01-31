
import db_manager as dbm
from models import (create_tables, User, RussianWord, EnglishWord,
                    RussianEnglishAssociation, LearnedWord)

if __name__ == "__main__":
    engine = dbm.create_engine()
    create_tables(engine)
    session = dbm.create_session(engine)

    # Загрузка базового словаря
    path = 'files/base_dict.json'
    dbm.download_data_from_json(session, path)

    # Проверка добавления пользователя в БД
    dbm.create_user(session = session, username = 340227777)

    # Проверка добавления новых слов и ассоциаций
    dbm.create_russian_word('пиво', session)
    dbm.create_english_word('beer', session)
    dbm.create_words_association(26, 26, 2, session)

    new_learned_word = [
                        LearnedWord(russian_word_id = 19 ,
                                    english_word_id = 20,
                                    user_id = 2),
                        LearnedWord(russian_word_id = 14 ,
                                    english_word_id = 15,
                                    user_id= 2),
                        LearnedWord(russian_word_id = 26,
                                    english_word_id = 26,
                                    user_id = 1)
    ]
    session.add_all(new_learned_word)



    session.commit()
    session.close()