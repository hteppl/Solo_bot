from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminPanelCallback(CallbackData, prefix='admin_panel'):
    action: str


def build_start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📊 Статистика пользователей",
        callback_data=AdminPanelCallback(action="user_stats").pack()
    )
    builder.button(
        text="👥 Управление пользователями",
        callback_data=AdminPanelCallback(action="user_editor").pack()
    )
    builder.button(
        text="🖥️ Управление серверами",
        callback_data=AdminPanelCallback(action="servers_editor").pack()
    )
    builder.button(
        text="🎟️ Управление купонами",
        callback_data=AdminPanelCallback(action="coupons_editor").pack()
    )
    builder.button(
        text="📢 Массовая рассылка",
        callback_data=AdminPanelCallback(action="sender").pack()
    )
    builder.button(
        text="💾 Создать резервную копию",
        callback_data=AdminPanelCallback(action="backups").pack()
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
