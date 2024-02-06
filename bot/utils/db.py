from bot.db.models import User, Debtor, Loan
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from sqlalchemy.exc import IntegrityError
from tabulate import tabulate


async def get_user(telegram_id: int, session: AsyncSession):
    user = await session.get(User, telegram_id)
    return user


async def register_user(telegram_id: int, session: AsyncSession):
    status_code = 201

    try:
        session.add(User(telegram_id=telegram_id))
        await session.commit()
    except IntegrityError as e:
        # Обработка ошибки уникального ограничения telegram_id
        await session.rollback()
        status_code = 400
    except Exception as e:
        print(e)
        # Обработка других ошибок
        await session.rollback()
        status_code = 500  # Internal Server Error

    return status_code


async def get_debtors(creditor_id: int, session: AsyncSession):
    creditor = await session.get(User, creditor_id)
    if not creditor:
        return 401

    return creditor.debtors


async def add_debtor(telegram_id: int, full_name: str, session: AsyncSession):
    status_code = 201

    if await get_user(telegram_id=telegram_id, session=session) is None:
        status_code = 401
        return status_code

    try:
        session.add(Debtor(creditor_id=telegram_id, full_name=full_name))
        await session.commit()
    except IntegrityError:
        await session.rollback()
        status_code = 400
    except Exception:
        await session.rollback()
        status_code = 500

    return status_code


async def get_loans(debtor_id: int, session: AsyncSession):
    debtor = await session.get(Debtor, debtor_id)
    if not debtor:
        return 404

    if len(debtor.loans):
        return debtor.loans
    return None


async def add_loan(creditor_id: int,
                   debtor_id: int,
                   amount_of_debt: int,
                   subject_of_debt: str,
                   date_of_loan: date,
                   end_date_of_loan: date,
                   session: AsyncSession):
    user = await session.get(User, creditor_id)
    debtor = await session.get(Debtor, debtor_id)
    if not user:
        return 4041
    if not debtor:
        return 4042

    new_loan = Loan(amount_of_debt=amount_of_debt,
                    subject_of_debt=subject_of_debt,
                    date_of_loan=date_of_loan,
                    end_date_of_loan=end_date_of_loan,
                    debtor_id=debtor_id,
                    creditor_id=creditor_id)
    session.add(new_loan)
    await session.commit()

    return 201


