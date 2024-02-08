from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_calendar import get_user_locale, SimpleCalendarCallback, SimpleCalendar
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import main_kb, DebtorsCallbackFactory, debtor_kb, add_loan_confirm_kb, add_debtor_kb, \
    forgive_loan_confirm_kb, delete_debtor_confirm_kb
from bot.utils.db import add_debtor, get_loans, add_loan, get_debtor, subtract_from_debt, get_debtors, \
    get_user_all_loans, forgive_all_debts, delete_debtor
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


class DebtorRemoveLoanState(StatesGroup):
    enter_remove_amount = State()
    confirm_remove_amount = State()


class DebtorForgiveLoanState(StatesGroup):
    confirm_forgive_amount = State()


@router.callback_query(F.data.startswith("debtorBackToMain"))
async def back_to_main_callback_edit_text(callback: CallbackQuery, session: AsyncSession):
    total_debt = 0
    telegram_id = callback.from_user.id
    loans = await get_user_all_loans(telegram_id=telegram_id, session=session)
    debtors = await get_debtors(creditor_id=telegram_id, session=session)

    if isinstance(loans, list) and len(loans) > 0:
        total_debt = sum(loan.amount_of_debt for loan in loans)

    if debtors == 401:
        await callback.answer("Вы не зарегистрированы. Используйте команду /start, чтобы начать пользоваться ботом")
        return

    debtors_list = [{"name": d.full_name, "id": d.id} for d in debtors]
    if len(debtors) == 0:
        await callback.message.edit_text("Пока у вас нет должников. Хотите добавить первого?", reply_markup=add_debtor_kb(debtors_list))
        return
    elif len(debtors) != 0:
        await callback.message.edit_text(f"Общая сумма ваших денег у других людей: <b>{0 if total_debt is None else total_debt}</b>\n\n"
                                         f"Вот ваши должники:", reply_markup=add_debtor_kb(debtors_list))
        return
    else:
        await callback.answer("Ошибка")
        return


@router.callback_query(F.data.startswith("debtorBackToMainCallbackEditText"))
async def back_to_main_callback_answer(callback: CallbackQuery, session: AsyncSession):
    global total_debt
    telegram_id = callback.from_user.id
    loans = await get_user_all_loans(telegram_id=telegram_id, session=session)
    debtors = await get_debtors(creditor_id=telegram_id, session=session)

    if loans not in [None, 0, []]:
        total_debt = sum(loan.amount_of_debt for loan in loans)

    if debtors == 401:
        await callback.answer("Вы не зарегистрированы. Используйте команду /start, чтобы начать пользоваться ботом")
        return

    debtors_list = [{"name": d.full_name, "id": d.id} for d in debtors]
    if len(debtors) == 0:
        await callback.message.answer("Пока у вас нет должников. Хотите добавить первого?", reply_markup=add_debtor_kb(debtors_list))
        return
    elif len(debtors) != 0:
        await callback.message.answer(f"Общая сумма ваших денег у других людей: <b>{total_debt}</b>\n\n"
                                      f"Вот ваши должники:", reply_markup=add_debtor_kb(debtors_list))
        return
    else:
        await callback.answer("Ошибка")
        return


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
        await callback.message.delete()
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

    if loans is None or all(loan.amount_of_debt == 0 for loan in loans):
        await callback.message.edit_text(f"<b>{callback_data.name}</b>\n\n"
                                         f"Вам ничего не должен этот человек🎉",
                                         reply_markup=debtor_kb(None, callback_data.id))
        return

    # Фильтруем долги, оставляем только те, у которых amount_of_debt > 0
    filtered_loans = [loan for loan in loans if loan.amount_of_debt > 0]

    total_debt = sum(loan.amount_of_debt for loan in filtered_loans)
    loans_answer = "\n".join([f"Долг💸: <b>{loan.amount_of_debt}</b>\n"
                              f"Причина📋: <b>{loan.subject_of_debt}</b>\n"
                              f"Дата займа📅: <b>{convert_date(loan.date_of_loan)}</b>\n"
                              f"Дата возврата⏰: <b>{convert_date(loan.end_date_of_loan)}</b>\n"
                              for loan in filtered_loans])

    await callback.message.edit_text(f"<b>{callback_data.name}</b>\n"
                                     f"Общая сумма💰: <b>{total_debt}</b>\n\n"
                                     f"{loans_answer}",
                                     reply_markup=debtor_kb(filtered_loans, callback_data.id))


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
        calendar.set_dates_range(datetime(2010, 1, 1), datetime(2050, 12, 31))
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
            await callback.message.delete()
            await state.clear()
        else:
            await callback.message.answer("Ошибка", reply_markup=main_kb())


@router.callback_query(F.data.startswith("debtorAddLoanRewrite"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Давайте перепишем. Введите размер долга: ")
    await state.set_state(DebtorAddLoanState.enter_amount)
    await callback.message.delete()


@router.callback_query(F.data.startswith("debtorRemoveLoan_"))
async def callback_add_loan(callback: CallbackQuery, state: FSMContext):
    await state.update_data(debtor_id=callback.data.split('_')[1])
    await callback.message.edit_text(text="Введите, сколько вычесть из общего долга: ")
    await state.set_state(DebtorRemoveLoanState.enter_remove_amount)


@router.callback_query(F.data.startswith("debtorRemoveLoanConfirm"))
async def callback_remove_loan(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    state_data = await state.get_data()
    if current_state == DebtorRemoveLoanState.confirm_remove_amount:
        subtract = await subtract_from_debt(debtor_id=int(state_data["debtor_id"]),
                                            amount_to_subtract=int(state_data["amount_to_subtract"]),
                                            session=session)
        if subtract == 200:
            await callback.message.answer(f"<b>{state_data['amount_to_subtract']} успешно вычтено из долга👌</b>",
                                          reply_markup=main_kb())
            await callback.message.delete()
            await state.clear()
            return
        else:
            await callback.message.answer("Ошибка", reply_markup=main_kb())
            await state.clear()
            return
    else:
        await callback.message.answer("В начале введите вычитаемую из долга сумму: ")
        await state.set_state(DebtorRemoveLoanState.enter_remove_amount)
        return


@router.callback_query(F.data.startswith("debtorRemoveLoanRewrite"))
async def callback_remove_loan(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Давайте перепишем. Введите вычитаемую сумму: ")
    await state.set_state(DebtorRemoveLoanState.enter_remove_amount)
    await callback.message.delete()


@router.callback_query(F.data.startswith("debtorForgiveLoan_"))
async def callback_add_loan(callback: CallbackQuery, state: FSMContext):
    await state.update_data(debtor_id=callback.data.split('_')[1])
    await callback.message.edit_text(text="Вы уверены, что хотите простить этому человеку все долги?😐",
                                     reply_markup=forgive_loan_confirm_kb())
    await state.set_state(DebtorForgiveLoanState.confirm_forgive_amount)


@router.callback_query(F.data.startswith("debtorForgiveLoanConfirm"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    state_data = await state.get_data()

    forgive_debts = await forgive_all_debts(int(state_data["debtor_id"]), session)
    if forgive_debts == 200:
        await callback.message.answer("Долги списаны🔥", reply_markup=main_kb())
        await callback.message.delete()
    await state.clear()


@router.callback_query(F.data.startswith("debtorForgiveLoanNo"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("Не смогли простить, да?😔", reply_markup=main_kb())
    await callback.message.delete()
    await state.clear()


@router.callback_query(F.data.startswith("debtorRemoveDebtor_"))
async def callback_add_loan(callback: CallbackQuery, state: FSMContext):
    await state.update_data(debtor_id=callback.data.split('_')[1])
    await callback.message.edit_text(text="Вы уверены, что хотите удалить этого должника?🙄 \nВдруг еще пригодится?",
                                     reply_markup=delete_debtor_confirm_kb())
    await state.set_state(DebtorForgiveLoanState.confirm_forgive_amount)


@router.callback_query(F.data.startswith("debtorDeleteConfirm"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    state_data = await state.get_data()

    deleted_debtor = await delete_debtor(int(state_data["debtor_id"]), session)
    if deleted_debtor == 200:
        await callback.message.answer("Должник удален❌", reply_markup=main_kb())
        await callback.message.delete()
    await state.clear()


@router.callback_query(F.data.startswith("debtorDeleteNo"))
async def callback_add_loan_confirm(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("Ладно, оставим его пока😎", reply_markup=main_kb())
    await callback.message.delete()
    await state.clear()

