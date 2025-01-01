from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminPanelCallback(CallbackData, prefix='admin_panel'):
    action: str


def build_start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔍 Поиск пользователя",
        callback_data=AdminPanelCallback(action="users_search").pack()
    )
    builder.button(
        text="🔑 Поиск по названию ключа",
        callback_data=AdminPanelCallback(action="users_search_key").pack()
    )
    builder.row(
        InlineKeyboardButton(
            text="🖥️ Серверы",
            callback_data=AdminPanelCallback(action="servers_editor").pack()
        ),
        InlineKeyboardButton(
            text="🎟️ Купоны",
            callback_data=AdminPanelCallback(action="coupons_editor").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📢 Рассылка",
            callback_data=AdminPanelCallback(action="sender").pack()
        ),
        InlineKeyboardButton(
            text="💾 Бекап",
            callback_data=AdminPanelCallback(action="backups").pack()
        )
    )
    builder.button(
        text="📊 Статистика",
        callback_data=AdminPanelCallback(action="user_stats").pack()
    )
    builder.button(
        text="🔄 Перезагрузить бота",
        callback_data=AdminPanelCallback(action="restart").pack()
    )
    builder.button(
        text="👤 Личный кабинет",
        callback_data="profile"
    )
    return builder.as_markup()


def build_restart_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, перезапустить",
        callback_data=AdminPanelCallback(action="restart_confirm").pack()
    )
    builder.button(
        text="🔙 Назад",
        callback_data="admin"
    )
    return builder.as_markup()
