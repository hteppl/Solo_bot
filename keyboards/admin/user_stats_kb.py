from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_user_stats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="user_stats")
    )
    builder.row(
        InlineKeyboardButton(
            text="📥 Выгрузить пользователей в CSV",
            callback_data="export_users_csv",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📥 Выгрузить оплаты в CSV", callback_data="export_payments_csv"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="admin")
    )
    return builder.as_markup()
