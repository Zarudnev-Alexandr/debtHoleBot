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


async def get_debtor(id: int, session: AsyncSession):
    debtor = await session.get(Debtor, id)
    return debtor


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


async def delete_debtor(debtor_id: int, session: AsyncSession):
    status_code = 200

    try:
        # Получаем объект должника
        debtor = await session.get(Debtor, debtor_id)

        if not debtor:
            # Если должник не найден, возвращаем код ошибки 404
            return 404

        # Удаляем должника
        await session.delete(debtor)
        await session.commit()
    except Exception as e:
        # Если произошла ошибка при удалении, откатываем транзакцию и возвращаем код ошибки 500
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


async def get_user_all_loans(telegram_id: int, session: AsyncSession):
    user = await session.get(User, telegram_id)
    if not user:
        return 404

    if len(user.loans):
        return user.loans
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
    print(f"debtor: {debtor}")
    if not user:
        return 4041
    if not debtor:
        return 4042

    new_loan = Loan(amount_of_debt=amount_of_debt,
                    subject_of_debt=subject_of_debt,
                    date_of_loan=date_of_loan,
                    end_date_of_loan=end_date_of_loan,
                    is_debt_repaid=False,
                    debtor_id=debtor_id,
                    creditor_id=creditor_id)
    session.add(new_loan)

    await session.commit()

    return 201


async def forgive_all_debts(debtor_id: int, session: AsyncSession):
    # Получаем все долги данного должника
    debtor = await session.get(Debtor, debtor_id)
    loans = debtor.loans

    # Проходимся по каждому долгу и устанавливаем флаг is_debt_repaid в True
    for loan in loans:
        loan.is_debt_repaid = True
        loan.amount_of_debt = 0

    # Фиксируем изменения в базе данных
    await session.commit()

    return 200


async def subtract_from_debt(debtor_id: int, amount_to_subtract: int, session: AsyncSession):
    debtor = await session.get(Debtor, debtor_id)
    if not debtor:
        return 404

    loans = await session.execute(select(Loan).filter(Loan.debtor_id == debtor_id))
    loans = [loan for loan, in loans.unique().all()]
    print("loans: ", loans)

    # Вычисляем начальное значение total_debt как сумму всех долгов
    total_debt = sum(loan.amount_of_debt for loan in loans)

    loan_amounts = [(loan.id, loan.amount_of_debt) for loan in loans]
    # Сортируем долги по возрастанию суммы
    loan_amounts.sort(key=lambda x: x[1])

    # Вычитаем сумму из долгов, начиная с самого маленького
    for loan_id, loan_amount in loan_amounts:
        if amount_to_subtract <= 0:
            break  # Если сумма для вычитания уже ноль или отрицательна, выходим из цикла

        # Получаем информацию о текущем долге
        loan = await session.get(Loan, loan_id)

        # Если сумма вычитания больше суммы долга, закрываем долг полностью
        if amount_to_subtract >= loan_amount:
            loan.is_debt_repaid = True
            amount_to_subtract -= loan_amount
            loan.amount_of_debt = 0
        else:
            # Иначе вычитаем из долга необходимую сумму
            loan.amount_of_debt -= amount_to_subtract
            amount_to_subtract = 0

        # Обновляем значение total_debt после обработки каждого долга
        total_debt -= min(amount_to_subtract, loan_amount)

    # Выполняем обновление долгов и сохраняем изменения
    await session.commit()

    return 200  # Успешное выполнение операции




