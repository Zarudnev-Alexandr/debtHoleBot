from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class DebtorsCallbackFactory(CallbackData, prefix="debtor"):
    id: int
    name: str


def main_kb():
    kb = [
        [
            KeyboardButton(text="Должники📃"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard


def add_debtor_kb(debtors_list):
    if not debtors_list:
        builder = InlineKeyboardBuilder()
        builder.button(text="➕добавить➕", callback_data="debtor_add")
        return builder.as_markup()

    builder = InlineKeyboardBuilder()
    for item in debtors_list:
        builder.button(
            text=item["name"],
            callback_data=DebtorsCallbackFactory(id=item["id"], name=item["name"])
        )
    builder.button(text="➕добавить➕", callback_data="debtor_add")
    builder.adjust(3)
    return builder.as_markup()


def confirm_debtor_fullname_kb():
    kb = [
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="debtor_confirm"),
            InlineKeyboardButton(text="Заново", callback_data="debtor_rewrite")
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard


def debtor_kb(loans, debtor_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕Добавить долг➕", callback_data=f"debtorAddLoan_{debtor_id}")
    if loans is None:
        builder.button(text="🗑️Удалить должника🗑️", callback_data=f"debtorRemoveDebtor_{debtor_id}")
        builder.button(text="⬅Назад⬅", callback_data=f"debtorBackToMain")
        builder.adjust(2)
        return builder.as_markup()

    builder.button(text="➖Вычесть долг➖", callback_data=f"debtorRemoveLoan_{debtor_id}")
    builder.button(text="❤Простить долги❤", callback_data=f"debtorForgiveLoan_{debtor_id}")
    builder.button(text="🗑️Удалить должника🗑️", callback_data=f"debtorRemoveDebtor_{debtor_id}")
    builder.button(text="⬅Назад⬅", callback_data=f"debtorBackToMain")
    builder.adjust(2)
    return builder.as_markup()


def add_loan_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сохранить✅", callback_data="debtorAddLoanConfirm")
    builder.button(text="Заново🔄", callback_data="debtorAddLoanRewrite")
    builder.adjust(2)
    return builder.as_markup()


def remove_loan_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Вычесть✅", callback_data="debtorRemoveLoanConfirm")
    builder.button(text="Заново🔄", callback_data="debtorRemoveLoanRewrite")
    builder.adjust(2)
    return builder.as_markup()


def forgive_loan_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🙏Прощаю🙏", callback_data="debtorForgiveLoanConfirm")
    builder.button(text="💀Я жлоб💀", callback_data="debtorForgiveLoanNo")
    builder.adjust(2)
    return builder.as_markup()


def delete_debtor_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️Удаляем🗑️", callback_data="debtorDeleteConfirm")
    builder.button(text="🥱Пусть остается🥱", callback_data="debtorDeleteNo")
    builder.adjust(2)
    return builder.as_markup()

