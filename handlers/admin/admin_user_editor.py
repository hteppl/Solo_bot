import asyncio
from datetime import datetime
from typing import Any

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TOTAL_GB
from database import delete_user_data, get_client_id_by_email, get_servers_from_db, restore_trial, update_key_expiry
from filters.admin import IsAdminFilter
from handlers.keys.key_utils import (
    delete_key_from_cluster,
    delete_key_from_db,
    renew_key_in_cluster,
)
from handlers.utils import sanitize_key_name
from keyboards.admin.panel_kb import build_user_editor_kb, AdminPanelCallback
from keyboards.admin.user_editor_kb import build_user_edit_kb, build_key_edit_kb, build_key_delete_kb, \
    build_user_delete_kb
from keyboards.common_kb import build_back_kb
from logger import logger

router = Router()


class UserEditorState(StatesGroup):
    waiting_for_tg_id = State()
    waiting_for_username = State()
    displaying_user_info = State()
    waiting_for_new_balance = State()
    waiting_for_key_name = State()
    waiting_for_expiry_time = State()


@router.callback_query(
    AdminPanelCallback.filter(F.action == "user_editor"),
    IsAdminFilter(),
)
async def user_editor_menu(callback_query: CallbackQuery):
    kb = build_user_editor_kb()
    await callback_query.message.answer(
        text="👇 Выберите способ поиска пользователя:",
        reply_markup=kb
    )


@router.callback_query(F.data == "search_by_tg_id", IsAdminFilter())
async def prompt_tg_id(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("user_editor")
    await callback_query.message.answer(
        text="🔍 Введите Telegram ID клиента:",
        reply_markup=kb
    )
    await state.set_state(UserEditorState.waiting_for_tg_id)


@router.callback_query(F.data == "search_by_username", IsAdminFilter())
async def prompt_username(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("user_editor")
    await callback_query.message.answer(
        text="🔍 Введите Username клиента:",
        reply_markup=kb
    )
    await state.set_state(UserEditorState.waiting_for_username)


@router.message(UserEditorState.waiting_for_username, IsAdminFilter())
async def handle_username_input(
        message: types.Message, state: FSMContext, session: Any
):
    # Extract the username from a message text by removing leading '@' and the Telegram URL prefix
    username = message.text.strip().lstrip('@').replace('https://t.me/', '')
    user_record = await session.fetchrow(
        "SELECT tg_id FROM users WHERE username = $1", username
    )

    kb = build_back_kb("user_editor")

    if not user_record:
        await message.answer(
            text="🔍 Пользователь с указанным username не найден. 🚫",
            reply_markup=kb,
        )
        await state.clear()
        return

    tg_id = user_record["tg_id"]
    username = await session.fetchval(
        "SELECT username FROM users WHERE tg_id = $1", tg_id
    )
    balance = await session.fetchval(
        "SELECT balance FROM connections WHERE tg_id = $1", tg_id
    )
    key_records = await session.fetch("SELECT email FROM keys WHERE tg_id = $1", tg_id)
    referral_count = await session.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_tg_id = $1", tg_id
    )

    if balance is None:
        await message.answer(
            "🚫 Пользователь с указанным tg_id не найден. 🔍",
            reply_markup=kb,
        )
        await state.clear()
        return

    kb = build_user_edit_kb(tg_id, key_records)

    user_info = (
        f"📊 Информация о пользователе:\n\n"
        f"🆔 ID пользователя: <b>{tg_id}</b>\n"
        f"👤 Логин пользователя: <b>@{username}</b>\n"
        f"💰 Баланс: <b>{balance}</b>\n"
        f"👥 Количество рефералов: <b>{referral_count}</b>\n"
        f"🔑 Ключи (для редактирования нажмите на ключ):"
    )

    await message.answer(
        text=user_info,
        reply_markup=kb
    )
    await state.set_state(UserEditorState.displaying_user_info)


@router.message(UserEditorState.waiting_for_tg_id, F.text.isdigit(), IsAdminFilter())
async def handle_tg_id_input(message: types.Message, state: FSMContext, session: Any):
    tg_id = int(message.text)
    username = await session.fetchval(
        "SELECT username FROM users WHERE tg_id = $1", tg_id
    )
    balance = await session.fetchval(
        "SELECT balance FROM connections WHERE tg_id = $1", tg_id
    )
    key_records = await session.fetch("SELECT email FROM keys WHERE tg_id = $1", tg_id)
    referral_count = await session.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_tg_id = $1", tg_id
    )

    if balance is None:
        kb = build_back_kb("user_editor")
        await message.answer(
            text="❌ Пользователь с указанным tg_id не найден. 🔍",
            reply_markup=kb,
        )
        await state.clear()
        return

    kb = build_user_edit_kb(tg_id, key_records)

    user_info = (
        f"📊 Информация о пользователе:\n\n"
        f"🆔 ID пользователя: <b>{tg_id}</b>\n"
        f"👤 Логин пользователя: <b>@{username}</b>\n"
        f"💰 Баланс: <b>{balance}</b>\n"
        f"👥 Количество рефералов: <b>{referral_count}</b>\n"
        f"🔑 Ключи (для редактирования нажмите на ключ):"
    )

    await message.answer(
        text=user_info,
        reply_markup=kb
    )
    await state.set_state(UserEditorState.displaying_user_info)


@router.callback_query(F.data.startswith("restore_trial_"), IsAdminFilter())
async def handle_restore_trial(callback_query: types.CallbackQuery, session: Any):
    tg_id = int(callback_query.data.split("_")[2])

    await restore_trial(tg_id, session)

    kb = build_back_kb("admin")

    await callback_query.message.answer(
        text="✅ Триал успешно восстановлен.",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("change_balance_"), IsAdminFilter())
async def process_balance_change(callback_query: CallbackQuery, state: FSMContext):
    tg_id = int(callback_query.data.split("_")[2])
    await state.update_data(tg_id=tg_id)

    kb = build_back_kb("user_editor")

    await callback_query.message.answer(
        text="💸 Введите новую сумму баланса:",
        reply_markup=kb
    )
    await state.set_state(UserEditorState.waiting_for_new_balance)


@router.message(UserEditorState.waiting_for_new_balance, IsAdminFilter())
async def handle_new_balance_input(
        message: types.Message, state: FSMContext, session: Any
):
    if not message.text.isdigit() or int(message.text) < 0:
        kb = build_back_kb("user_editor")
        await message.answer(
            text="❌ Пожалуйста, введите корректную сумму для изменения баланса.",
            reply_markup=kb,
        )
        return

    new_balance = int(message.text)
    user_data = await state.get_data()
    tg_id = user_data.get("tg_id")

    await session.execute(
        "UPDATE connections SET balance = $1 WHERE tg_id = $2",
        new_balance,
        tg_id,
    )

    kb = build_back_kb("admin")

    await message.answer(
        text=f"✅ Баланс успешно изменен на <b>{new_balance}</b>.",
        reply_markup=kb
    )
    await state.clear()


@router.callback_query(F.data.startswith("edit_key_"), IsAdminFilter())
async def process_key_edit(callback_query: CallbackQuery, session: Any):
    email = callback_query.data.split("_", 2)[2]
    key_details = await get_key_details(email, session)

    if not key_details:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="user_editor"))
        await callback_query.message.answer(
            text="🔍 <b>Информация о ключе не найдена.</b> 🚫",
            reply_markup=builder.as_markup(),
        )
        return

    response_message = (
        f"🔑 Ключ: <code>{key_details['key']}</code>\n"
        f"⏰ Дата истечения: <b>{key_details['expiry_date']}</b>\n"
        f"💰 Баланс пользователя: <b>{key_details['balance']}</b>\n"
        f"🌐 Кластер: <b>{key_details['server_name']}</b>"
    )

    kb = build_key_edit_kb(key_details, email)

    await callback_query.message.answer(
        text=response_message,
        reply_markup=kb
    )


@router.callback_query(F.data == "search_by_key_name", IsAdminFilter())
async def prompt_key_name(callback_query: CallbackQuery, state: FSMContext):
    kb = build_back_kb("user_editor")
    await callback_query.message.answer(
        text="🔑 Введите имя ключа:",
        reply_markup=kb
    )
    await state.set_state(UserEditorState.waiting_for_key_name)


@router.message(UserEditorState.waiting_for_key_name, IsAdminFilter())
async def handle_key_name_input(
        message: types.Message, state: FSMContext, session: Any
):
    key_name = sanitize_key_name(message.text)
    key_details = await get_key_details(key_name, session)

    if not key_details:
        kb = build_back_kb("user_editor")
        await message.answer(
            text="🚫 Пользователь с указанным именем ключа не найден.",
            reply_markup=kb
        )
        await state.clear()
        return

    response_message = (
        f"🔑 Ключ: <code>{key_details['key']}</code>\n"
        f"⏰ Дата истечения: <b>{key_details['expiry_date']}</b>\n"
        f"💰 Баланс пользователя: <b>{key_details['balance']}</b>\n"
        f"🌐 Сервер: <b>{key_details['server_name']}</b>"
    )

    kb = build_key_edit_kb(key_details, key_name)

    await message.answer(
        text=response_message,
        reply_markup=kb
    )
    await state.clear()


@router.callback_query(F.data.startswith("change_expiry|"), IsAdminFilter())
async def prompt_expiry_change(callback_query: CallbackQuery, state: FSMContext):
    email = callback_query.data.split("|")[1]
    await callback_query.message.answer(
        text=f"⏳ Введите новое время истечения для ключа <b>{email}</b> в формате <code>YYYY-MM-DD HH:MM:SS</code>:"
    )
    await state.update_data(email=email)
    await state.set_state(UserEditorState.waiting_for_expiry_time)


@router.message(UserEditorState.waiting_for_expiry_time, IsAdminFilter())
async def handle_expiry_time_input(
        message: types.Message, state: FSMContext, session: Any
):
    user_data = await state.get_data()
    email = user_data.get("email")

    if not email:
        kb = build_back_kb("user_editor")
        await message.answer(
            text="📧 Email не найден в состоянии. 🚫",
            reply_markup=kb
        )
        await state.clear()
        return

    try:
        expiry_time_str = message.text
        expiry_time = int(
            datetime.strptime(expiry_time_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
        )

        client_id = await get_client_id_by_email(email)
        if client_id is None:
            kb = build_back_kb("user_editor")
            await message.answer(
                text=f"🚫 Клиент с email {email} не найден. 🔍",
                reply_markup=kb,
            )
            await state.clear()
            return

        record = await session.fetchrow(
            "SELECT server_id FROM keys WHERE client_id = $1", client_id
        )
        if not record:
            kb = build_back_kb("user_editor")
            await message.answer(
                text="🚫 Клиент не найден в базе данных. 🔍",
                reply_markup=kb.as_markup(),
            )
            await state.clear()
            return

        clusters = await get_servers_from_db()

        async def update_key_on_all_servers():
            tasks = []
            for cluster_name, cluster_servers in clusters.items():
                for server in cluster_servers:
                    tasks.append(
                        asyncio.create_task(
                            renew_key_in_cluster(
                                cluster_name,
                                email,
                                client_id,
                                expiry_time,
                                total_gb=TOTAL_GB,
                            )
                        )
                    )
            await asyncio.gather(*tasks)

        await update_key_on_all_servers()

        await update_key_expiry(client_id, expiry_time)

        response_message = f"✅ Время истечения ключа для клиента {client_id} ({email}) успешно обновлено на всех серверах."

        kb = build_back_kb("admin")
        await message.answer(
            text=response_message,
            reply_markup=kb
        )
    except ValueError:
        kb = build_back_kb("user_editor")
        await message.answer(
            text="❌ Пожалуйста, используйте формат: YYYY-MM-DD HH:MM:SS.",
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(e)
    await state.clear()


@router.callback_query(F.data.startswith("delete_key_admin|"), IsAdminFilter())
async def process_callback_delete_key(
        callback_query: types.CallbackQuery, session: Any
):
    email = callback_query.data.split("|")[1]
    client_id = await session.fetchval(
        "SELECT client_id FROM keys WHERE email = $1", email
    )

    if client_id is None:
        kb = build_back_kb("user_editor")
        await callback_query.message.answer(
            text="🔍 Ключ не найден. 🚫",
            reply_markup=kb
        )
        return

    kb = build_key_delete_kb(client_id)

    await callback_query.message.answer(
        text="<b>❓ Вы уверены, что хотите удалить ключ?</b>",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("confirm_delete_admin|"), IsAdminFilter())
async def process_callback_confirm_delete(
        callback_query: types.CallbackQuery, session: Any
):
    client_id = callback_query.data.split("|")[1]
    record = await session.fetchrow(
        "SELECT email FROM keys WHERE client_id = $1", client_id
    )

    kb = build_back_kb("view_keys")

    if record:
        clusters = await get_servers_from_db()

        async def delete_key_from_servers(email, client_id):
            tasks = []
            for cluster_name, cluster_servers in clusters.items():
                for server in cluster_servers:
                    tasks.append(
                        delete_key_from_cluster(cluster_name, email, client_id)
                    )
            await asyncio.gather(*tasks)

        await delete_key_from_servers(record["email"], client_id)
        await delete_key_from_db(client_id, session)

        await callback_query.message.answer(
            text="✅ Ключ успешно удален.",
            reply_markup=kb
        )
    else:
        await callback_query.message.answer(
            text="🚫 Ключ не найден или уже удален.",
            reply_markup=kb
        )


@router.callback_query(F.data.startswith("user_info|"), IsAdminFilter())
async def handle_user_info(
        callback_query: types.CallbackQuery, state: FSMContext, session: Any
):
    tg_id = int(callback_query.data.split("|")[1])
    username = await session.fetchval(
        "SELECT username FROM users WHERE tg_id = $1", tg_id
    )
    balance = await session.fetchval(
        "SELECT balance FROM connections WHERE tg_id = $1", tg_id
    )
    key_records = await session.fetch("SELECT email FROM keys WHERE tg_id = $1", tg_id)
    referral_count = await session.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_tg_id = $1", tg_id
    )

    kb = build_user_edit_kb(tg_id, key_records)

    user_info = (
        f"📊 Информация о пользователе:\n\n"
        f"🆔 ID пользователя: <b>{tg_id}</b>\n"
        f"👤 Логин пользователя: <b>@{username}</b>\n"
        f"💰 Баланс: <b>{balance}</b>\n"
        f"👥 Количество рефералов: <b>{referral_count}</b>\n"
        f"🔑 Ключи (для редактирования нажмите на ключ):"
    )

    await callback_query.message.answer(
        text=user_info,
        reply_markup=kb
    )
    await state.set_state(UserEditorState.displaying_user_info)


@router.callback_query(F.data.startswith("confirm_delete_user_"), IsAdminFilter())
async def confirm_delete_user(callback_query: types.CallbackQuery, state: FSMContext, session: Any):
    tg_id = int(callback_query.data.split("_")[3])

    kb = build_user_delete_kb(tg_id)

    await callback_query.message.answer(
        text=f"Вы уверены, что хотите удалить пользователя с ID {tg_id}?",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("delete_user_"), IsAdminFilter())
async def delete_user(callback_query: types.CallbackQuery, session: Any):
    tg_id = int(callback_query.data.split("_")[2])

    key_records = await session.fetch("SELECT email, client_id FROM keys WHERE tg_id = $1", tg_id)

    async def delete_keys_from_servers():
        try:
            tasks = []
            for email, client_id in key_records:
                servers = await get_servers_from_db()
                for cluster_id, cluster in servers.items():
                    tasks.append(delete_key_from_cluster(cluster_id, email, client_id))
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Ошибка при удалении ключей с серверов для пользователя {tg_id}: {e}")

    await delete_keys_from_servers()

    try:
        await delete_user_data(session, tg_id)

        kb = build_back_kb("user_editor")

        await callback_query.message.answer(
            text=f"🗑️ Пользователь с ID {tg_id} был удален.",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении данных из базы данных для пользователя {tg_id}: {e}")
        await callback_query.message.answer(
            text=f"❌ Произошла ошибка при удалении пользователя с ID {tg_id}. Попробуйте снова."
        )


async def get_key_details(email, session):
    record = await session.fetchrow(
        """
        SELECT k.key, k.expiry_time, k.server_id, c.tg_id, c.balance
        FROM keys k
        JOIN connections c ON k.tg_id = c.tg_id
        WHERE k.email = $1
        """,
        email,
    )

    if not record:
        return None

    servers = await get_servers_from_db()

    cluster_name = "Неизвестный кластер"
    for cluster_name, cluster_servers in servers.items():
        if any(
                server["inbound_id"] == record["server_id"] for server in cluster_servers
        ):
            cluster_name = cluster_name
            break

    expiry_date = datetime.utcfromtimestamp(record["expiry_time"] / 1000)
    current_date = datetime.utcnow()
    time_left = expiry_date - current_date

    if time_left.total_seconds() <= 0:
        days_left_message = "<b>Ключ истек.</b>"
    elif time_left.days > 0:
        days_left_message = f"Осталось дней: <b>{time_left.days}</b>"
    else:
        hours_left = time_left.seconds // 3600
        days_left_message = f"Осталось часов: <b>{hours_left}</b>"

    return {
        "key": record["key"],
        "expiry_date": expiry_date.strftime("%d %B %Y года"),
        "days_left_message": days_left_message,
        "server_name": cluster_name,
        "balance": record["balance"],
        "tg_id": record["tg_id"],
    }
