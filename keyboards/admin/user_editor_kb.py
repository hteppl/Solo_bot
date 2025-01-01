from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.admin.panel_kb import AdminPanelCallback


class AdminUserEditorCallback(CallbackData, prefix='admin_users_editor'):
    action: str
    data: str


def build_user_edit_kb(tg_id: int, key_records: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for email in key_records:
        builder.button(
            text=f"🔑 {email}",
            callback_data=AdminUserEditorCallback(
                action="users_key_edit",
                data=email
            ).pack()
        )

    builder.button(
        text="📝 Изменить баланс",
        callback_data=AdminUserEditorCallback(
            action="users_balance_change",
            data=tg_id
        ).pack()
    )
    builder.button(
        text="🔄 Восстановить пробник",
        callback_data=AdminUserEditorCallback(
            action="users_trial_restore",
            data=tg_id
        ).pack()
    )
    builder.button(
        text="❌ Удалить клиента",
        callback_data=AdminUserEditorCallback(
            action="users_delete",
            data=tg_id
        ).pack()
    )
    builder.button(
        text="🔙 Назад",
        callback_data=AdminPanelCallback(action="user_editor").pack()
    )
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
            callback_data=AdminUserEditorCallback(
                action="users_info",
                data=key_details["tg_id"]
            ).pack()
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
