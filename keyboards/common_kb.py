from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_back_kb(callback_data: str) -> InlineKeyboardMarkup:
    return build_singleton_kb("🔙 Назад", callback_data)


def build_singleton_kb(text: str, callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback_data)
    return builder.as_markup()
