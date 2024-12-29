from typing import Any

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from bot import bot
from filters.admin import IsAdminFilter
from keyboards.admin.panel_kb import AdminPanelCallback
from keyboards.common_kb import build_back_kb
from logger import logger

router = Router()


class AdminSendToAll(StatesGroup):
    waiting_for_message = State()


@router.callback_query(
    AdminPanelCallback.filter(F.action == "sender"),
    IsAdminFilter(),
)
async def handle_send_to_all(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("admin")
    await callback_query.message.edit_text(
        text="✍️ Введите текст сообщения, который вы хотите отправить всем клиентам:",
        reply_markup=kb,
    )
    await state.set_state(AdminSendToAll.waiting_for_message)


@router.message(
    AdminSendToAll.waiting_for_message,
    IsAdminFilter(),
)
async def process_message_to_all(message: types.Message, state: FSMContext, session: Any):
    text_message = message.text

    try:
        tg_ids = await session.fetch("SELECT tg_id FROM connections")

        total_users = len(tg_ids)
        success_count = 0
        error_count = 0

        for record in tg_ids:
            tg_id = record["tg_id"]
            try:
                await bot.send_message(chat_id=tg_id, text=text_message)
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    f"❌ Ошибка при отправке сообщения пользователю {tg_id}: {e}"
                )

        text = (
            f"📤 Рассылка завершена:\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"✅ Успешно отправлено: {success_count}\n"
            f"❌ Не доставлено: {error_count}"
        )

        await message.edit_text(
            text=text
        )
    except Exception as e:
        logger.error(f"❗ Ошибка при подключении к базе данных: {e}")

    await state.clear()
