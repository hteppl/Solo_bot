import subprocess
from datetime import datetime
from io import BytesIO
from typing import Any

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery

from backup import backup_database
from bot import bot
from filters.admin import IsAdminFilter
from keyboards.admin.panel_kb import build_start_kb, build_user_stats_kb, build_restart_kb, build_user_editor_kb
from keyboards.common_kb import build_back_kb
from logger import logger

router = Router()


class UserEditorState(StatesGroup):
    waiting_for_tg_id = State()
    displaying_user_info = State()
    waiting_for_restart_confirmation = State()
    waiting_for_message = State()


@router.callback_query(F.data == "admin", IsAdminFilter())
async def handle_admin_callback_query(callback_query: CallbackQuery, state: FSMContext):
    await handle_admin_message(callback_query.message, state)


@router.message(Command("admin"), IsAdminFilter())
async def handle_admin_message(message: types.Message, state: FSMContext):
    await state.clear()
    kb = build_start_kb()

    await message.answer(
        text="🤖 Панель администратора",
        reply_markup=kb
    )


@router.callback_query(F.data == "user_stats", IsAdminFilter())
async def user_stats_menu(callback_query: CallbackQuery, session: Any):
    try:
        total_users = await session.fetchval("SELECT COUNT(*) FROM connections")
        total_keys = await session.fetchval("SELECT COUNT(*) FROM keys")
        total_referrals = await session.fetchval("SELECT COUNT(*) FROM referrals")

        total_payments_today = await session.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE created_at >= CURRENT_DATE"
        )
        total_payments_week = await session.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE created_at >= date_trunc('week', CURRENT_DATE)"
        )
        total_payments_month = await session.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE created_at >= date_trunc('month', CURRENT_DATE)"
        )
        total_payments_all_time = await session.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments"
        )

        active_keys = await session.fetchval(
            "SELECT COUNT(*) FROM keys WHERE expiry_time > $1",
            int(datetime.utcnow().timestamp() * 1000),
        )
        expired_keys = total_keys - active_keys

        stats_message = (
            f"📊 <b>Подробная статистика проекта:</b>\n\n"
            f"👥 Пользователи:\n"
            f"   🌐 Зарегистрировано: <b>{total_users}</b>\n"
            f"   🤝 Привлеченных рефералов: <b>{total_referrals}</b>\n\n"
            f"🔑 Ключи:\n"
            f"   🌈 Всего сгенерировано: <b>{total_keys}</b>\n"
            f"   ✅ Действующих: <b>{active_keys}</b>\n"
            f"   ❌ Просроченных: <b>{expired_keys}</b>\n\n"
            f"💰 Финансовая статистика:\n"
            f"   📅 За день: <b>{total_payments_today} ₽</b>\n"
            f"   📆 За неделю: <b>{total_payments_week} ₽</b>\n"
            f"   📆 За месяц: <b>{total_payments_month} ₽</b>\n"
            f"   🏦 За все время: <b>{total_payments_all_time} ₽</b>\n"
        )

        kb = build_user_stats_kb()

        await callback_query.message.answer(
            text=stats_message,
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Error in user_stats_menu: {e}")


@router.callback_query(F.data == "export_users_csv", IsAdminFilter())
async def export_users_csv(callback_query: CallbackQuery, session: Any):
    kb = build_back_kb("user_stats")

    try:
        users = await session.fetch(
            """
            SELECT 
                u.tg_id, 
                u.username, 
                u.first_name, 
                u.last_name, 
                u.language_code, 
                u.is_bot, 
                c.balance, 
                c.trial 
            FROM users u
            LEFT JOIN connections c ON u.tg_id = c.tg_id
        """
        )

        if not users:
            await callback_query.message.answer(
                text="📭 Нет пользователей для экспорта.",
                reply_markup=kb
            )
            return

        csv_data = "tg_id,username,first_name,last_name,language_code,is_bot,balance,trial\n"
        for user in users:
            csv_data += f"{user['tg_id']},{user['username']},{user['first_name']},{user['last_name']},{user['language_code']},{user['is_bot']},{user['balance']},{user['trial']}\n"

        file_name = BytesIO(csv_data.encode("utf-8-sig"))
        file_name.seek(0)

        file = BufferedInputFile(file_name.getvalue(), filename="users_export.csv")

        await callback_query.message.answer_document(
            file,
            caption="📥 Экспорт пользователей в CSV",
            reply_markup=kb
        )
        file_name.close()

    except Exception as e:
        logger.error(f"Ошибка при экспорте пользователей в CSV: {e}")
        await callback_query.message.answer(
            text="❗ Произошла ошибка при экспорте пользователей.",
            reply_markup=kb
        )


@router.callback_query(F.data == "export_payments_csv", IsAdminFilter())
async def export_payments_csv(callback_query: CallbackQuery, session: Any):
    kb = build_back_kb("user_stats")

    try:
        payments = await session.fetch(
            """
            SELECT 
                u.tg_id, 
                u.username, 
                u.first_name, 
                u.last_name, 
                p.amount, 
                p.payment_system,
                p.status,
                p.created_at 
            FROM users u
            JOIN payments p ON u.tg_id = p.tg_id
        """
        )

        if not payments:
            await callback_query.message.answer(
                text="📭 Нет платежей для экспорта.",
                reply_markup=kb
            )
            return

        csv_data = "tg_id,username,first_name,last_name,amount,payment_system,status,created_at\n"  # Заголовки CSV
        for payment in payments:
            csv_data += f"{payment['tg_id']},{payment['username']},{payment['first_name']},{payment['last_name']},{payment['amount']},{payment['payment_system']},{payment['status']},{payment['created_at']}\n"

        file_name = BytesIO(csv_data.encode("utf-8-sig"))
        file_name.seek(0)

        file = BufferedInputFile(file_name.getvalue(), filename="payments_export.csv")

        await callback_query.message.answer_document(
            document=file,
            caption="📥 Экспорт платежей в CSV",
            reply_markup=kb
        )
        file_name.close()

    except Exception as e:
        logger.error(f"Ошибка при экспорте платежей в CSV: {e}")
        await callback_query.message.answer(
            text="❗ Произошла ошибка при экспорте платежей.",
            reply_markup=kb
        )


@router.callback_query(F.data == "send_to_alls", IsAdminFilter())
async def handle_send_to_all(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("admin")
    await callback_query.message.answer(
        text="✍️ Введите текст сообщения, который вы хотите отправить всем клиентам 📢🌐:",
        reply_markup=kb,
    )
    await state.set_state(UserEditorState.waiting_for_message)


@router.message(UserEditorState.waiting_for_message, IsAdminFilter())
async def process_message_to_all(
        message: types.Message, state: FSMContext, session: Any
):
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

        await message.answer(
            text=text
        )
    except Exception as e:
        logger.error(f"❗ Ошибка при подключении к базе данных: {e}")

    await state.clear()


@router.callback_query(F.data == "backups", IsAdminFilter())
async def handle_backup(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        text="💾 Инициализация резервного копирования базы данных..."
    )
    await backup_database()
    await callback_query.message.answer(
        text="✅ Резервная копия успешно создана и отправлена администратору."
    )


@router.callback_query(F.data == "restart_bot", IsAdminFilter())
async def handle_restart(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserEditorState.waiting_for_restart_confirmation)
    kb = build_restart_kb()
    await callback_query.message.answer(
        text="🤔 Вы уверены, что хотите перезапустить бота?",
        reply_markup=kb,
    )


@router.callback_query(
    F.data == "confirm_restart",
    UserEditorState.waiting_for_restart_confirmation,
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


@router.callback_query(F.data == "user_editor", IsAdminFilter())
async def user_editor_menu(callback_query: CallbackQuery):
    kb = build_user_editor_kb()
    await callback_query.message.answer(
        text="👇 Выберите способ поиска пользователя:",
        reply_markup=kb
    )
