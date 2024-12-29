from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.admin.panel_kb import AdminPanelCallback


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
