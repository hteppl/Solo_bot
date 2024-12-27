from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminPanelCallback(CallbackData, prefix='admin_panel'):
    action: str


def build_start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика пользователей", callback_data="user_stats"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 Управление пользователями", callback_data="user_editor"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🖥️ Управление серверами", callback_data="servers_editor"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎟️ Управление купонами", callback_data="coupons_editor"
        )
    )
    builder.row(
        InlineKeyboardButton(text="📢 Массовая рассылка", callback_data="send_to_alls")
    )
    builder.row(
        InlineKeyboardButton(text="💾 Создать резервную копию", callback_data="backups")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Перезагрузить бота", callback_data="restart_bot")
    )
    builder.row(InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile"))
    return builder.as_markup()


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


def build_user_editor_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔍 Поиск по названию ключа",
            callback_data="search_by_key_name",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🆔 Поиск по Telegram ID", callback_data="search_by_tg_id"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🌐 Поиск по Username", callback_data="search_by_username"
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="admin"))
    return builder.as_markup()


def build_restart_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, перезапустить", callback_data="confirm_restart"
        ),
        InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="admin"))
    return builder.as_markup()
