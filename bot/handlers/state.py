from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.callbacks import DebtorAddState, DebtorAddLoanState
from bot.keyboards import confirm_debtor_fullname_kb
from bot.utils.db import add_debtor
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback, \
    get_user_locale

from bot.utils.utils import get_current_add_loan_state_data

router = Router(name="state-router")


@router.message(DebtorAddState.waiting_for_fullname, F.text)
async def debtor_add_state_wating_for_fullanme(message: Message, state: FSMContext, session: AsyncSession):
    full_name = message.text.strip()

    if not full_name:
        await message.answer("Пожалуйста, укажите корректное ФИО должника. Пустой ввод не допускается: ")
        return

    await state.update_data(fullname=message.text)
    await message.answer(text=f"Вы ввели: {full_name}. Все правильно?", reply_markup=confirm_debtor_fullname_kb())


@router.message(DebtorAddLoanState.enter_amount, F.text)
async def debtor_add_loan_enter_amount(message: Message, state: FSMContext):
    amount = message.text.strip()
    if not amount.isdigit():
        await message.answer("Указывать можно только целые числа.\n\n<b>Укажите размер долга:</b> ")
        return

    await state.update_data(amount=amount)
    state_data = await state.get_data()
    await message.answer(f"{get_current_add_loan_state_data(state_data)}\n\n<b>Введите причину долга:</b> ")
    await state.set_state(DebtorAddLoanState.enter_subject)


@router.message(DebtorAddLoanState.enter_subject, F.text)
async def debtor_add_loan_enter_amount(message: Message, state: FSMContext):
    subject = message.text.strip()
    if not subject:
        await message.answer("Укажите причину долга: ")
        return

    await state.update_data(subject=subject)
    state_data = await state.get_data()
    await message.answer(f"{get_current_add_loan_state_data(state_data)}\n\n<b>Введите дату заема: </b> ",
                         reply_markup=await SimpleCalendar(locale=await get_user_locale(message.from_user)).start_calendar())
    await state.set_state(DebtorAddLoanState.enter_date_of_loan)

