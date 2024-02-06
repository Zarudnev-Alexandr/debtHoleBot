from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, ForeignKey

# from bot.db.base import Base
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    telegram_id = Column(BigInteger, primary_key=True, unique=True)

    loans = relationship("Loan", back_populates="creditor", lazy="joined")
    debtors = relationship("Debtor", back_populates="creditor", lazy="joined")


class Debtor(Base):
    __tablename__ = "debtor"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    creditor_id = Column(BigInteger, ForeignKey("user.telegram_id"), nullable=False)

    loans = relationship("Loan", back_populates="debtor", lazy="joined")
    creditor = relationship("User", back_populates="debtors", lazy="joined")


class Loan(Base):
    __tablename__ = "loan"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    amount_of_debt = Column(Integer, nullable=False)
    subject_of_debt = Column(String, nullable=False)
    date_of_loan = Column(Date, nullable=False)
    end_date_of_loan = Column(Date, nullable=True)
    creditor_id = Column(BigInteger, ForeignKey("user.telegram_id"), nullable=False)
    debtor_id = Column(Integer, ForeignKey("debtor.id"), nullable=False)

    creditor = relationship("User", back_populates="loans", lazy="joined")
    debtor = relationship("Debtor", back_populates="loans", lazy="joined")

