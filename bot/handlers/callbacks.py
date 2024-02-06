from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_calendar import get_user_locale, SimpleCalendarCallback, SimpleCalendar
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import main_kb, DebtorsCallbackFactory, debtor_kb, add_loan_confirm_kb
from bot.utils.db import add_debtor, get_loans, add_loan
from bot.utils.utils import get_current_add_loan_state_data, convert_date
from tabulate import tabulate

router = Router(name="callbacks-router")


class DebtorAddState(StatesGroup):
    waiting_for_fullname = State()
    waiting_for_confirm_fullname = State()


class DebtorAddLoanState(StatesGroup):
    enter_amount = State()
    enter_subject = State()
    enter_date_of_loan = State()
    enter_end_date_of_loan = State()
    loan_submit = State()


@router.callback_query(StateFilter(None), F.data.startswith("debtor_add"))
async def callback_debtor_add(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    await callback.message.answer("Укажите ФИО должника или еще как-нибудь его назовите: ")
    await state.set_state(DebtorAddState.waiting_for_fullname)


@router.callback_query(F.data.startswith("debtor_confirm"))
async def callback_debtor_add(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    telegram_id = callback.from_user.id
    state_data = await state.get_data()
    fullname = state_data['fullname']
    new_debtor = await add_debtor(telegram_id=telegram_id, full_name=fullname, session=session)

    if new_debtor == 201:
        await callback.message.answer("Должник записан😈", reply_markup=main_kb())
        await state.clear()
    else:
        await callback.message.answer("Ошибка", reply_markup=main_kb())


@router.callback_query(F.data.startswith("debtor_rewrite"))
async def callback_debtor_rewrite(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Давайте перепишем. Введите должника: ")
    await state.set_state(DebtorAddState.waiting_for_fullname)


@router.callback_query(DebtorsCallbackFactory.filter())
async def callbacks_debtor_change(callback: CallbackQuery, callback_data: DebtorsCallbackFactory, session: AsyncSession):
    loans = await get_loans(debtor_id=callback_data.id, session=session)

    if loans is None:
        loans_answer = "Вам ничего не должен этот человек🎉"
        total_debt = 0
    else:
        total_debt = sum(loan.amount_of_debt for loan in loans)
        loans_answer = "\n".join([f"Долг💸: <b>{loan.amount_of_debt}</b>\n"
                                  f"Причина📋: <b>{loan.subject_of_debt}</b>\n"
                                  f"Дата займа📅: <b>{convert_date(loan.date_of_loan)}</b>\n"
                                  f"Дата возврата⏰: <b>{convert_date(loan.end_date_of_loan)}</b>\n"
                                  for loan in loans])

    await callback.message.edit_text(f"<b>{callback_data.name}</b>\n"
                                     f"Общая сумма💰: <b>{total_debt}</b>\n\n"
                                     f"{loans_answer}",
                                     reply_markup=debtor_kb(loans, callback_data.id))


@router.callback_query(F.data.startswith("debtorAddLoan_"))
async def callback_add_loan(callback: CallbackQuery, state: FSMContext):
    await state.update_data(debtor_id=callback.data.split('_')[1])
    await callback.message.edit_text(text="Введите размер нового долга: ")
    await state.set_state(DebtorAddLoanState.enter_amount)


@router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    current_state = await state.get_state()

    if current_state == DebtorAddLoanState.enter_date_of_loan:
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback_query.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        selected, date = await calendar.process_selection(callback_query, callback_data)
        if selected:
            await state.update_data(date_of_loan=date.strftime("%d/%m/%Y"))
            await state.set_state(DebtorAddLoanState.enter_end_date_of_loan)
            state_data = await state.get_data()
            await callback_query.message.answer(f"{get_current_add_loan_state_data(state_data)}\n\n"
                                                f"<b>Введите дату возврата долга:</b> ",
                                                reply_markup=await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).start_calendar())
            await callback_query.message.delete()

    elif current_state == DebtorAddLoanState.enter_end_date_of_loan:
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback_query.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        selected, date = await calendar.process_selection(callback_query, callback_data)
        if selected:
            await state.update_data(end_date_of_loan=date.strftime("%d/%m/%Y"))
            await state.set_state(DebtorAddLoanState.loan_submit)
            state_data = await state.get_data()
            await callback_query.message.answer(f"{get_current_add_loan_state_data(state_data)}\n\n"
                                                f"<b>Вы полностью ввели новый долг</b>",
                                                reply_markup=add_loan_confirm_kb())
            await callback_query.message.delete()

    else:
        await callback_query.answer("Сначала укажите причину долга.")


@router.callback_query(F.data.startswith("debtorAddLoanConfirm"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()

    if current_state == DebtorAddLoanState.loan_submit:
        telegram_id = callback.from_user.id
        state_data = await state.get_data()
        print(state_data)
        new_loan = await add_loan(creditor_id=telegram_id,
                                  debtor_id=int(state_data['debtor_id']),
                                  amount_of_debt=int(state_data['amount']),
                                  subject_of_debt=state_data['subject'],
                                  date_of_loan=datetime.strptime(state_data['date_of_loan'], '%d/%m/%Y').date(),
                                  end_date_of_loan=datetime.strptime(state_data['end_date_of_loan'], '%d/%m/%Y').date(),
                                  session=session)

        if new_loan == 201:
            await callback.message.answer("Новый долг записан✍", reply_markup=main_kb())
            await state.clear()
        else:
            await callback.message.answer("Ошибка", reply_markup=main_kb())


@router.callback_query(F.data.startswith("debtorAddLoanRewrite"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Давайте перепишем. Введите размер долга: ")
    await state.set_state(DebtorAddLoanState.enter_amount)
    await callback.message.delete()




