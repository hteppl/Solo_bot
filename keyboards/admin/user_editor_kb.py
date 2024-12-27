from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_user_edit_kb(tg_id: int, key_records: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for (email,) in key_records:
        builder.row(
            InlineKeyboardButton(text=f"🔑 {email}", callback_data=f"edit_key_{email}")
        )

    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить баланс",
            callback_data=f"change_balance_{tg_id}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Восстановить пробник",
            callback_data=f"restore_trial_{tg_id}",
        )
    )
    builder.row(InlineKeyboardButton(text="❌ Удалить клиента", callback_data=f"confirm_delete_user_{tg_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="user_editor"))
    return builder.as_markup()


def build_user_delete_kb(tg_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Удалить клиента", callback_data=f"confirm_delete_user_{tg_id}")
    builder.button(text="🔙 Назад", callback_data="user_editor")
    return builder.as_markup()


def build_key_edit_kb(key_details: dict, email: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Получить информацию о юзере",
            callback_data=f"user_info|{key_details['tg_id']}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏳ Изменить время истечения",
            callback_data=f"change_expiry|{email}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Удалить ключ",
            callback_data=f"delete_key_admin|{email}",
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="user_editor"))
    return builder.as_markup()


def build_key_delete_kb(client_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete_admin|{client_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(text="❌ Нет, отменить", callback_data="user_editor")
    )
    return builder.as_markup()
