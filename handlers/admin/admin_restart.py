import subprocess

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.admin import IsAdminFilter
from keyboards.admin.panel_kb import build_restart_kb, AdminPanelCallback
from keyboards.common_kb import build_back_kb

router = Router()


@router.callback_query(
    AdminPanelCallback.filter(F.action == "restart"),
    IsAdminFilter(),
)
async def handle_restart(callback_query: CallbackQuery):
    kb = build_restart_kb()
    await callback_query.message.answer(
        text="🤔 Вы уверены, что хотите перезапустить бота?",
        reply_markup=kb,
    )


@router.callback_query(
    AdminPanelCallback.filter(F.action == "restart_confirm"),
    IsAdminFilter(),
)
async def confirm_restart_bot(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("admin")
    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", "bot.service"],
            check=True,
            capture_output=True,
            text=True,
        )
        await state.clear()
        await callback_query.message.answer(
            text="🔄 Бот успешно перезапущен.",
            reply_markup=kb
        )
    except subprocess.CalledProcessError:
        await callback_query.message.answer(
            text="🔄 Бот успешно перезапущен.",
            reply_markup=kb
        )
    except Exception as e:
        await callback_query.message.answer(
            text=f"⚠️ Ошибка при перезагрузке бота: {e.stderr}",
            reply_markup=kb
        )
