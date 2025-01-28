import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key = True)
    username = sq.Column(sq.Integer, unique = True, nullable = False)


class RussianWord(Base):
    __tablename__ = 'russian_word'
    id = sq.Column(sq.Integer, primary_key = True)
    ru_word = sq.Column(sq.String(100), unique = True, nullable = False)
    user_name = sq.Column(sq.Integer,
                        sq.ForeignKey('user.username',
                                              ondelete = 'SET DEFAULT'),
                        nullable = False,
                        server_default = '0'
    )

    def __str__(self):
        return f'{self.id}: {self.ru_word}'

class EnglishWord(Base):
    __tablename__ = 'english_word'
    id = sq.Column(sq.Integer, primary_key = True)
    en_word = sq.Column(sq.String(100), unique = True, nullable = False)

    def __str__(self):
        return f'{self.id}: {self.en_word}'

class RussianEnglishAssociation(Base):
    __tablename__ = 'russian_english_association'
    russian_word_id = sq.Column(sq.Integer,
                                sq.ForeignKey('russian_word.id',
                                               ondelete='CASCADE'),
                                primary_key = True)
    english_word_id = sq.Column(sq.Integer,
                                sq.ForeignKey('english_word.id',
                                               ondelete = 'CASCADE'),
                                primary_key = True)

class LearnedWord(Base):
    __tablename__ = 'learned_words'
    russian_word_id = sq.Column(sq.Integer, primary_key=True)
    english_word_id = sq.Column(sq.Integer, primary_key=True)
    user_name = sq.Column(sq.Integer,
                          sq.ForeignKey('user.username', ondelete='CASCADE'),
                          nullable=False,
                          primary_key=True)
    __table_args__ = (
                      sq.ForeignKeyConstraint(
                       ['russian_word_id', 'english_word_id'],
                     ['russian_english_association.russian_word_id',
                                'russian_english_association.english_word_id'],
                                ondelete='CASCADE'
                     ),
    )



def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)