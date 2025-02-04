import db_manager as dbm
from bot_manager import bot
from models import (create_tables, User, RussianWord, EnglishWord,
                    RussianEnglishAssociation, LearnedWord)

if __name__ == "__main__":
    engine = dbm.create_engine()
    create_tables(engine)
    session = dbm.create_session(engine)
    bot.polling(none_stop=True)
    session.commit()
    session.close()