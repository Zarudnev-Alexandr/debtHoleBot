from datetime import datetime


def get_current_add_loan_state_data(state_data):
    return f"Сумма долга: {state_data['amount'] if 'amount' in state_data else '❌'}\n" \
           f"Причина долга: {state_data['subject'] if 'subject' in state_data else '❌'}\n" \
           f"Дата заема: {state_data['date_of_loan'] if 'date_of_loan' in state_data else '❌'}\n" \
           f"Дата возврата долга: {state_data['end_date_of_loan'] if 'end_date_of_loan' in state_data else '❌'}"


def convert_date(date_str):
    try:
        date_object = datetime.strptime(str(date_str), '%Y-%m-%d')
        formatted_date = date_object.strftime('%d.%m.%Y')
        return formatted_date
    except ValueError:
        return "Неверный формат даты"

