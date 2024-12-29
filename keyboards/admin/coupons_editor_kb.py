from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_coupons_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Создать купон", callback_data="create_coupon")
    )
    builder.row(InlineKeyboardButton(text="Купоны", callback_data="coupons"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin"))
    return builder.as_markup()


def build_coupons_list_kb(coupons: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for coupon in coupons:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ Удалить {coupon['code']}",
                callback_data=f"delete_coupon_{coupon['code']}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="coupons_editor")
    )
    return builder.as_markup()
