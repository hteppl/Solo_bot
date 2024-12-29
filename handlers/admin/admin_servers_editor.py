import asyncpg
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from py3xui import AsyncApi

from backup import create_backup_and_send_to_admins
from config import ADMIN_PASSWORD, ADMIN_USERNAME, DATABASE_URL
from database import check_unique_server_name, get_servers_from_db
from filters.admin import IsAdminFilter
from keyboards.admin.panel_kb import AdminPanelCallback
from keyboards.admin.servers_editor_kb import build_editor_kb, build_cancel_kb, build_manage_server_kb, build_delete_server_kb, \
    build_manage_cluster_kb
from keyboards.common_kb import build_back_kb, build_singleton_kb

router = Router()


class UserEditorState(StatesGroup):
    waiting_for_cluster_name = State()
    waiting_for_api_url = State()
    waiting_for_inbound_id = State()
    waiting_for_server_name = State()
    waiting_for_subscription_url = State()


@router.callback_query(
    AdminPanelCallback.filter(F.action == "servers_editor"),
    IsAdminFilter(),
)
async def handle_servers_editor(callback_query: types.CallbackQuery):
    servers = await get_servers_from_db()
    kb = build_editor_kb(servers)

    text = (
        "<b>🔧 Управление кластерами</b>\n\n"
        "<i>📌 Здесь вы можете добавить новый кластер.</i>\n\n"
        "<i>🌐 <b>Кластеры</b> — это пространство серверов, в пределах которого создается подписка.</i>\n"
        "💡 Если вы хотите выдавать по 1 серверу, то добавьте всего 1 сервер в кластер.\n\n"
        "<i>⚠️ <b>Важно:</b> Кластеры удаляются автоматически, если удалить все серверы внутри них.</i>\n\n"
    )

    await callback_query.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )


@router.callback_query(F.data == "add_cluster", IsAdminFilter())
async def handle_add_cluster(callback_query: types.CallbackQuery, state: FSMContext):
    text = (
        "🔧 <b>Введите имя нового кластера:</b>\n\n"
        "<b>Имя кластера должно быть уникальным и на английском языке.</b>\n"
        "<i>Пример:</i> <code>cluster2</code> или <code>us_east_1</code>"
    )

    await callback_query.message.answer(
        text=text,
        parse_mode="HTML",
    )

    await state.set_state(UserEditorState.waiting_for_cluster_name)


@router.message(UserEditorState.waiting_for_cluster_name, IsAdminFilter())
async def handle_cluster_name_input(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            text="❌ Имя кластера не может быть пустым. Попробуйте снова."
        )
        return

    cluster_name = message.text.strip()
    await state.update_data(cluster_name=cluster_name)

    kb = build_back_kb("servers_editor")

    text = (
        f"<b>Введите имя сервера для кластера {cluster_name}:</b>\n\n"
        "Рекомендуется указать локацию сервера в имени.\n\n"
        "<i>Пример:</i> <code>server-asia</code>, <code>server-europe</code>"
    )

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await state.set_state(UserEditorState.waiting_for_server_name)


@router.message(UserEditorState.waiting_for_server_name, IsAdminFilter())
async def handle_server_name_input(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            text="❌ Имя сервера не может быть пустым. Попробуйте снова."
        )
        return

    server_name = message.text.strip()

    server_unique = await check_unique_server_name(server_name)
    if not server_unique:
        await message.answer(
            text="❌ Сервер с таким именем уже существует. Пожалуйста, выберите другое имя."
        )
        return

    user_data = await state.get_data()
    cluster_name = user_data.get("cluster_name")
    await state.update_data(server_name=server_name)

    kb = build_back_kb("servers_editor")

    text = (
        f"<b>Введите API URL для сервера {server_name} в кластере {cluster_name}:</b>\n\n"
        "API URL должен быть в следующем формате:\n\n"
        "<code>https://your_domain:port/panel_path</code>\n\n"
        "URL должен быть без слэша на конце!\n"
    )

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await state.set_state(UserEditorState.waiting_for_api_url)


@router.message(UserEditorState.waiting_for_api_url, IsAdminFilter())
async def handle_api_url_input(message: types.Message, state: FSMContext):
    api_url = message.text.strip()

    if api_url == "❌ Отменить":
        await state.clear()

        kb = build_singleton_kb("🔧 Управление кластерами", "servers_editor")

        await message.answer(
            text="Процесс создания кластера был отменен. Вы вернулись в меню управления серверами.",
            reply_markup=kb,
        )
        return

    if not api_url.startswith("https://"):
        await message.answer(
            text="❌ API URL должен начинаться с <code>https://</code>. Попробуйте снова.",
            parse_mode="HTML",
        )
        return

    api_url = api_url.rstrip("/")

    user_data = await state.get_data()
    cluster_name = user_data.get("cluster_name")
    server_name = user_data.get("server_name")
    await state.update_data(api_url=api_url)

    kb = build_cancel_kb()

    text = (
        f"<b>Введите subscription_url для сервера {server_name} в кластере {cluster_name}:</b>\n\n"
        "Subscription URL должен быть в следующем формате:\n\n"
        "<code>https://your_domain:port_sub/sub_path</code>\n\n"
        "URL должен быть без слэша и имени клиента на конце!\n"
        "Его можно увидеть в панели 3x-ui в информации о клиенте."
    )

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await state.set_state(UserEditorState.waiting_for_subscription_url)


@router.message(UserEditorState.waiting_for_subscription_url, IsAdminFilter())
async def handle_subscription_url_input(message: types.Message, state: FSMContext):
    subscription_url = message.text.strip()

    if subscription_url == "❌ Отменить":
        await state.clear()

        kb = build_singleton_kb("🔧 Управление кластерами", "servers_editor")

        await message.answer(
            text="Процесс создания кластера был отменен. Вы вернулись в меню управления серверами.",
            reply_markup=kb,
        )
        return

    if not subscription_url.startswith("https://"):
        await message.answer(
            text="❌ subscription_url должен начинаться с <code>https://</code>. Попробуйте снова.",
            parse_mode="HTML",
        )
        return

    subscription_url = subscription_url.rstrip("/")

    user_data = await state.get_data()
    cluster_name = user_data.get("cluster_name")
    server_name = user_data.get("server_name")
    await state.update_data(subscription_url=subscription_url)

    kb = build_back_kb("servers_editor")

    text = (
        f"<b>Введите inbound_id для сервера {server_name} в кластере {cluster_name}:</b>\n\n"
        "Это номер подключения vless в вашей панели 3x-ui. Обычно это <b>1</b> при чистой настройке по гайду.\n\n"
    )

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await state.set_state(UserEditorState.waiting_for_inbound_id)


@router.message(UserEditorState.waiting_for_inbound_id, IsAdminFilter())
async def handle_inbound_id_input(message: types.Message, state: FSMContext):
    inbound_id = message.text.strip()

    if not inbound_id.isdigit():
        await message.answer(
            text="❌ inbound_id должен быть числовым значением. Попробуйте снова."
        )
        return

    user_data = await state.get_data()
    cluster_name = user_data.get("cluster_name")
    server_name = user_data.get("server_name")
    api_url = user_data.get("api_url")
    subscription_url = user_data.get("subscription_url")

    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        """
        INSERT INTO servers (cluster_name, server_name, api_url, subscription_url, inbound_id) 
        VALUES ($1, $2, $3, $4, $5)
        """,
        cluster_name,
        server_name,
        api_url,
        subscription_url,
        inbound_id,
    )
    await conn.close()

    kb = build_back_kb("servers_editor")

    await message.answer(
        text=f"✅ Кластер {cluster_name} и сервер {server_name} успешно добавлены!",
        reply_markup=kb,
    )

    await state.clear()


@router.callback_query(F.data.startswith("manage_cluster|"), IsAdminFilter())
async def handle_manage_cluster(callback_query: types.CallbackQuery, state: FSMContext):
    cluster_name = callback_query.data.split("|")[1]

    servers = await get_servers_from_db()
    cluster_servers = servers.get(cluster_name, [])

    kb = build_manage_cluster_kb(cluster_servers, cluster_name)

    await callback_query.message.answer(
        text=f"🔧 Управление серверами для кластера {cluster_name}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("server_availability|"), IsAdminFilter())
async def handle_check_server_availability(callback_query: types.CallbackQuery):
    cluster_name = callback_query.data.split("|")[1]

    servers = await get_servers_from_db()
    cluster_servers = servers.get(cluster_name, [])

    if not cluster_servers:
        await callback_query.answer(
            text=f"Кластер '{cluster_name}' не содержит серверов."
        )
        return

    text = (
        f"🖥️ Проверка доступности серверов для кластера {cluster_name}.\n\n"
        "Это может занять до 1 минуты, пожалуйста, подождите..."
    )

    in_progress_message = await callback_query.message.answer(text=text)

    availability_message = (
        f"🖥️ Проверка доступности серверов для кластера {cluster_name} завершена:\n\n"
    )

    for server in cluster_servers:
        xui = AsyncApi(
            server["api_url"], username=ADMIN_USERNAME, password=ADMIN_PASSWORD
        )

        try:
            await xui.login()

            online_users = len(await xui.client.online())
            availability_message += (
                f"🌍 {server['server_name']}: {online_users} активных пользователей.\n"
            )

        except Exception as e:
            availability_message += f"❌ {server['server_name']}: Не удалось получить информацию. Ошибка: {e}\n"

    kb = build_back_kb("servers_editor")

    await in_progress_message.edit_text(
        text=availability_message,
        reply_markup=kb
    )

    await callback_query.answer()


@router.callback_query(F.data.startswith("manage_server|"), IsAdminFilter())
async def handle_manage_server(callback_query: types.CallbackQuery, state: FSMContext):
    server_name = callback_query.data.split("|")[1]

    servers = await get_servers_from_db()

    server = None
    cluster_name = None
    for cluster, cluster_servers in servers.items():
        server = next(
            (s for s in cluster_servers if s["server_name"] == server_name), None
        )
        if server:
            cluster_name = cluster
            break

    if server:
        api_url = server["api_url"]
        subscription_url = server["subscription_url"]
        inbound_id = server["inbound_id"]

        kb = build_manage_server_kb(server_name, cluster_name)

        text = (
            f"<b>🔧 Информация о сервере {server_name}:</b>\n\n"
            f"<b>📡 API URL:</b> {api_url}\n"
            f"<b>🌐 Subscription URL:</b> {subscription_url}\n"
            f"<b>🔑 Inbound ID:</b> {inbound_id}"
        )

        await callback_query.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await callback_query.message.answer("❌ Сервер не найден.")


@router.callback_query(F.data.startswith("delete_server|"), IsAdminFilter())
async def handle_delete_server(callback_query: types.CallbackQuery, state: FSMContext):
    server_name = callback_query.data.split("|")[1]

    kb = build_delete_server_kb(server_name)

    await callback_query.message.answer(
        text=f"🗑️ Вы уверены, что хотите удалить сервер {server_name}?",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("confirm_delete_server|"), IsAdminFilter())
async def handle_confirm_delete_server(
        callback_query: types.CallbackQuery, state: FSMContext
):
    server_name = callback_query.data.split("|")[1]

    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        """
        DELETE FROM servers WHERE server_name = $1
        """,
        server_name,
    )
    await conn.close()

    kb = build_back_kb("servers_editor")

    await callback_query.message.answer(
        text=f"🗑️ Сервер {server_name} успешно удален.",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("add_server|"), IsAdminFilter())
async def handle_add_server(callback_query: types.CallbackQuery, state: FSMContext):
    cluster_name = callback_query.data.split("|")[1]

    await state.update_data(cluster_name=cluster_name)

    kb = build_back_kb("servers_editor")

    text = (
        f"<b>Введите имя сервера для кластера {cluster_name}:</b>\n\n"
        "Рекомендуется указать локацию сервера в имени.\n\n"
        "<i>Пример:</i> <code>server-asia</code>, <code>server-europe</code>"
    )

    await callback_query.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )

    await state.set_state(UserEditorState.waiting_for_server_name)


@router.callback_query(F.data.startswith("backup_cluster|"), IsAdminFilter())
async def handle_backup_cluster(callback_query: types.CallbackQuery):
    cluster_name = callback_query.data.split("|")[1]

    servers = await get_servers_from_db()
    cluster_servers = servers.get(cluster_name, [])

    for server in cluster_servers:
        xui = AsyncApi(
            server["api_url"],
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
        )
        await create_backup_and_send_to_admins(xui)

    kb = build_back_kb("servers_editor")

    text = (
        f"<b>Бэкап для кластера {cluster_name} был успешно создан и отправлен администраторам!</b>\n\n"
        f"🔔 <i>Бэкапы отправлены в боты панелей.</i>"
    )

    await callback_query.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await callback_query.answer()
