from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Debtor, Loan
from bot.keyboards import main_kb, add_debtor_kb
from bot.utils.db import get_user, register_user, get_debtors, get_user_all_loans
from aiogram import F

router = Router(name="commands-router")


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()
    await message.answer(
        text="Ввод отменен",
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    new_user = await register_user(telegram_id, session)

    if new_user == 201:
        await message.answer(text=f"Добро пожаловать, {message.from_user.full_name}, никогда не пользовались "
                                  f"нашим ботом? Рады видеть новых пользователй.", reply_markup=main_kb())
        return

    elif new_user == 400:
        await message.answer(text=f"{message.from_user.full_name}, вы уже заргистрированы", reply_markup=main_kb())
        return

    elif new_user == 500:
        await message.answer(text=f"Ошибка сервера")
        return

    else:
        await message.answer(text="Другая ошибка")
        return


@router.message(F.text.lower() == "должники📃")
async def add_debt(message: Message, session: AsyncSession, state: FSMContext):
    total_debt = None
    await state.clear()
    telegram_id = message.from_user.id
    loans = await get_user_all_loans(telegram_id=telegram_id, session=session)
    debtors = await get_debtors(creditor_id=telegram_id, session=session)

    if isinstance(loans, list) and len(loans) > 0:
        total_debt = sum(loan.amount_of_debt for loan in loans)

    if debtors == 401:
        await message.answer("Вы не зарегистрированы. Используйте команду /start, чтобы начать пользоваться ботом")
        return

    debtors_list = [{"name": d.full_name, "id": d.id} for d in debtors]
    if len(debtors) == 0:
        await message.answer("Пока у вас нет должников. Хотите добавить первого?", reply_markup=add_debtor_kb(debtors_list))
        return
    elif len(debtors) != 0:
        await message.answer(f"Общая сумма ваших денег у других людей: <b>{0 if total_debt is None else total_debt}</b>\n\n"
                             f"Вот ваши должники:", reply_markup=add_debtor_kb(debtors_list))
        return
    else:
        await message.answer("Ошибка")
        return



