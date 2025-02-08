import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """
    Represents a user in the system.

    This class defines the structure for the 'user' table in the database.
    It includes basic user information and establishes a relationship
    with RussianEnglishAssociation.

    Attributes:
        id (int): The primary key for the user.
        username (int): A unique identifier for the user, cannot be null.
        associations (relationship): A relationship to RussianEnglishAssociation,
                                     representing the user's word associations.

    Table name: 'user'
    """
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key = True)
    username = sq.Column(sq.BigInteger, unique = True, nullable = False)

    associations = relationship('RussianEnglishAssociation',
                                 back_populates = 'user',
                                 cascade = 'all, delete-orphan')

class RussianWord(Base):
    """
    Represents a russian word in the system.

    This class defines the structure for the 'russian_word' table in the
    database. It includes the russian word and establishes a
    relationship with RussianEnglishAssociation.

    Attributes:
        id (int): The primary key for the Russian word.
        ru_word (str): The Russian word, must be unique and cannot be null.
        associations (relationship):
                   A relationship to RussianEnglishAssociation,
                   representing the word's associations with English words.

    Table name: 'russian_word'
    """
    __tablename__ = 'russian_word'
    id = sq.Column(sq.Integer, primary_key = True)
    ru_word = sq.Column(sq.String(100), unique = True, nullable = False)

    associations = relationship('RussianEnglishAssociation',
                                back_populates = 'russian_word',
                                cascade = 'all, delete-orphan')
    def __str__(self):
        """
        Returns a string representation of the RussianWord object.

        This method is used to provide a human-readable representation of the
        RussianWord instance, which includes the word's ID and the Russian
        word itself.

        Returns:
            str: A string in the format 'id: ru_word', where 'id' is the
            unique identifier of the word and 'ru_word' is the Russian word.
        """
        return f'{self.id}: {self.ru_word}'

class EnglishWord(Base):
    """
    Represents an english word in the system.

    This class defines the structure for the 'english_word' table in the
    database. It includes the english word and establishes a
    relationship with RussianEnglishAssociation.

    Attributes:
        id (int): The primary key for the English word.
        en_word (str): The English word, must be unique and cannot be null.
        associations (relationship):
                   A relationship to RussianEnglishAssociation,
                   representing the word's associations with Russian words.

    Table name: 'english_word'
    """
    __tablename__ = 'english_word'
    id = sq.Column(sq.Integer, primary_key = True)
    en_word = sq.Column(sq.String(100), unique = True, nullable = False)

    associations = relationship('RussianEnglishAssociation',
                                back_populates = 'english_word',
                                cascade = 'all, delete-orphan')
    def __str__(self):
        return f'{self.id}: {self.en_word}'

class RussianEnglishAssociation(Base):
    """
    Represents a link between a russian word and an english word,
    and a user who has associated these words.

    This class defines the structure for the 'russian_english_association'
    table in the database. It includes columns for the foreign keys
    for the russian and english words and the user.

    Attributes:
        russian_word_id (int): The foreign key for the russian word.
        english_word_id (int): The foreign key for the english word.
        user_id (int): The foreign key for the user.
        user (relationship): A relationship to User, representing the user who has
                             associated the words.
        russian_word (relationship): A relationship to RussianWord, representing
                             the russian word.
        english_word (relationship): A relationship to EnglishWord, representing
                             the english word.
        learned_words (relationship): A relationship to LearnedWord, representing
                             the words learned by the user.

        Table name: 'russian_english_association'
    """
    __tablename__ = 'russian_english_association'
    russian_word_id = sq.Column(sq.Integer,
                                sq.ForeignKey('russian_word.id',
                                               ondelete = 'CASCADE'),
                                primary_key = True)
    english_word_id = sq.Column(sq.Integer,
                                sq.ForeignKey('english_word.id',
                                               ondelete = 'CASCADE'),
                                primary_key = True)
    user_id = sq.Column(sq.Integer,
                        sq.ForeignKey('user.id', ondelete = 'CASCADE'),
                        primary_key = True)
    user = relationship('User', back_populates = 'associations')
    russian_word = relationship('RussianWord',
                                back_populates = 'associations')
    english_word = relationship('EnglishWord',
                                back_populates = 'associations')
    learned_words = relationship('LearnedWord',
                                 back_populates = 'association',
                                 cascade = 'all, delete-orphan')

    __table_args__ = (
        sq.UniqueConstraint('russian_word_id', 'english_word_id',
                            'user_id',
                            name = 'uq_russian_english_user'),
    )

class LearnedWord(Base):
    """
    Represents a link between a russian word, an english word,
    and a user who has learned these words.

    This class defines the structure for the 'learned_words'
    table in the database. It includes columns for the foreign keys
    for the russian and english words and the user.

    Attributes:
        russian_word_id (int): The foreign key for the russian word.
        english_word_id (int): The foreign key for the english word.
        user_id (int): The foreign key for the user.
        association (relationship): A relationship to RussianEnglishAssociation,
                             representing the association between the words.

    Table name: 'learned_words'
    """
    __tablename__ = 'learned_words'
    russian_word_id = sq.Column(sq.Integer, primary_key = True)
    english_word_id = sq.Column(sq.Integer, primary_key = True)
    user_id = sq.Column(sq.Integer, primary_key=True)

    association = relationship('RussianEnglishAssociation',
                                back_populates = 'learned_words')
    __table_args__ = (
        sq.ForeignKeyConstraint(
            ['russian_word_id', 'english_word_id', 'user_id'],
            ['russian_english_association.russian_word_id',
             'russian_english_association.english_word_id',
             'russian_english_association.user_id'],
             ondelete = 'CASCADE'
        ),
    )

def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)