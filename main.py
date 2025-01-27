
import db_manager as dbm
from models import (create_tables, User, RussianWord, EnglishWord,
                    RussianEnglishAssociation, LearnedWord)

if __name__ == "__main__":
    engine = dbm.create_engine()
    create_tables(engine)
    session = dbm.create_session(engine)

    path = 'files/base_dict.json'
    dbm.download_data_from_json(session, path)

    dbm.create_user(session = session, username = 444)

    dbm.create_russian_word('пиво', 444, session)
    dbm.create_english_word('beer', session)
    dbm.create_word_association(26, 26, session)

    rus_dict = session.query(RussianWord.ru_word).all()
    eng_dict = session.query(EnglishWord.en_word).all()
    new_ru_word_1 = RussianWord(ru_word = 'слово')
    new_eng_word_1 = EnglishWord(en_word = 'word')
    session.add_all([new_ru_word_1, new_eng_word_1])
    session.commit()
    new_russian_word_id = session.query(RussianWord).filter(
        RussianWord.ru_word == new_ru_word_1.ru_word).first()
    new_english_word_id = session.query(EnglishWord).filter(
        EnglishWord.en_word == new_eng_word_1.en_word).first()
    dbm.create_word_association(russian_word_id =
                                new_russian_word_id.id,
                                english_word_id =
                                new_english_word_id.id,
                                session = session)


    # session.add(rus_eng_assoc)
    # session.commit()
    new_learned_word = LearnedWord(russian_word_id = 19 , english_word_id = 20,
                                   user_name = 333)
    session.add(new_learned_word)

    dbm.get_learned_words()
    session.commit()





    session.close()