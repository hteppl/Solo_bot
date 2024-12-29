from typing import Any

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import create_coupon, delete_coupon_from_db, get_all_coupons
from filters.admin import IsAdminFilter
from keyboards.admin.coupons_editor_kb import build_coupons_kb, build_coupons_list_kb
from keyboards.admin.panel_kb import AdminPanelCallback
from keyboards.common_kb import build_back_kb
from logger import logger


class AdminCouponsState(StatesGroup):
    waiting_for_coupon_data = State()


router = Router()


@router.callback_query(
    AdminPanelCallback.filter(F.action == "coupons_editor"),
    IsAdminFilter(),
)
async def show_coupon_management_menu(
        callback_query: types.CallbackQuery, state: FSMContext
):
    await state.clear()

    kb = build_coupons_kb()

    await callback_query.message.answer(
        text="🛠 Меню управления купонами:",
        reply_markup=kb
    )


@router.callback_query(F.data == "coupons", IsAdminFilter())
async def show_coupon_list(callback_query: types.CallbackQuery, session: Any):
    try:
        coupons = await get_all_coupons(session)

        if not coupons:
            kb = build_back_kb("coupons_editor")
            await callback_query.message.answer(
                text="❌ На данный момент нет доступных купонов. 🚫\nВы можете вернуться в меню управления. 🔙",
                reply_markup=kb,
            )
            return

        kb = build_coupons_list_kb(coupons)
        coupon_list = "📜 Список всех купонов:\n\n"

        for coupon in coupons:
            coupon_list += (
                f"🏷️ <b>Код:</b> {coupon['code']}\n"
                f"💰 <b>Сумма:</b> {coupon['amount']} рублей\n"
                f"🔢 <b>Лимит использования:</b> {coupon['usage_limit']} раз\n"
                f"✅ <b>Использовано:</b> {coupon['usage_count']} раз\n\n"
            )

        await callback_query.message.answer(
            text=coupon_list,
            reply_markup=kb
        )

    except Exception as e:
        logger.error(f"Ошибка при получении списка купонов: {e}")


@router.callback_query(F.data.startswith("delete_coupon_"), IsAdminFilter())
async def handle_delete_coupon(callback_query: types.CallbackQuery, session: Any):
    coupon_code = callback_query.data[len("delete_coupon_"):]

    try:
        result = await delete_coupon_from_db(coupon_code, session)

        if result:
            await show_coupon_list(callback_query, session)
        else:
            await callback_query.message.answer(
                text=f"❌ Купон с кодом <b>{coupon_code}</b> не найден.",
            )
            await show_coupon_list(callback_query, session)

    except Exception as e:
        logger.error(f"Ошибка при удалении купона: {e}")


@router.callback_query(F.data == "create_coupon", IsAdminFilter())
async def handle_create_coupon(callback_query: types.CallbackQuery, state: FSMContext):
    kb = build_back_kb("coupons_editor")

    text = (
        "🎫 <b>Введите данные для создания купона в формате:</b>\n\n"
        "📝 <i>код</i> 💰 <i>сумма</i> 🔢 <i>лимит</i>\n\n"
        "Пример: <b>'COUPON1 50 5'</b> 👈\n\n"
    )

    await callback_query.message.answer(
        text=text,
        reply_markup=kb,
    )
    await state.set_state(AdminCouponsState.waiting_for_coupon_data)


@router.message(AdminCouponsState.waiting_for_coupon_data, IsAdminFilter())
async def process_coupon_data(message: types.Message, state: FSMContext, session: Any):
    text = message.text.strip()
    parts = text.split()

    kb = build_back_kb("coupons_editor")

    if len(parts) != 3:
        text = (
            "❌ <b>Некорректный формат!</b> 📝 Пожалуйста, введите данные в формате:\n"
            "🏷️ <b>код</b> 💰 <b>сумма</b> 🔢 <b>лимит</b>\n"
            "Пример: <b>'COUPON1 50 5'</b> 👈"
        )

        await message.answer(
            text=text,
            reply_markup=kb,
        )
        return

    try:
        coupon_code = parts[0]
        coupon_amount = float(parts[1])
        usage_limit = int(parts[2])
    except ValueError:
        text = (
            "⚠️ <b>Проверьте правильность введенных данных!</b>\n"
            "💱 Сумма должна быть числом, 🔢 а лимит — целым числом."
        )

        await message.answer(
            text=text,
            reply_markup=kb,
        )
        return

    try:
        await create_coupon(coupon_code, coupon_amount, usage_limit, session)

        result_message = (
            f"✅ Купон с кодом <b>{coupon_code}</b> успешно создан! 🎉\n"
            f"Сумма: <b>{coupon_amount} рублей</b> 💰\n"
            f"Лимит использования: <b>{usage_limit} раз</b> 🔢."
        )

        kb = build_back_kb("coupons_editor")

        await message.answer(
            text=result_message,
            reply_markup=kb
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании купона: {e}")
