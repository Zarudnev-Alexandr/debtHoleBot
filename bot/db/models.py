from sqlalchemy import Column, Integer, BigInteger, String, Float, Date

# from bot.db.base import Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    telegram_id = Column(BigInteger, primary_key=True, unique=True)


class Debtor(Base):
    __tablename__ = "debtor"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    full_name = Column(String, nullable=False)


class Loan(Base):
    __tablename__ = "loan"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    amount_of_debt = Column(Float, nullable=False)
    date_of_loan = Column(Date, nullable=False)
    end_date_of_loan = Column(Date, nullable=True)

