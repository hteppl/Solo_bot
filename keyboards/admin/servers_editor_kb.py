from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_editor_kb(servers) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for cluster_name, cluster_servers in servers.items():
        builder.row(
            InlineKeyboardButton(
                text=f"⚙️ {cluster_name}", callback_data=f"manage_cluster|{cluster_name}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить кластер", callback_data="add_cluster")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin"))
    return builder.as_markup()


def build_manage_cluster_kb(cluster_servers, cluster_name) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for server in cluster_servers:
        builder.row(
            InlineKeyboardButton(
                text=f"🌍 {server['server_name']}",
                callback_data=f"manage_server|{server['server_name']}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить сервер", callback_data=f"add_server|{cluster_name}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🌐 Доступность серверов",
            callback_data=f"server_availability|{cluster_name}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="💾 Создать бэкап кластера",
            callback_data=f"backup_cluster|{cluster_name}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад в управление кластерами", callback_data="servers_editor"
        )
    )
    return builder.as_markup()


def build_manage_server_kb(server_name: str, cluster_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить", callback_data=f"delete_server|{server_name}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=f"manage_cluster|{cluster_name}"
        )
    )
    return builder.as_markup()


def build_delete_server_kb(server_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да", callback_data=f"confirm_delete_server|{server_name}"
        ),
        InlineKeyboardButton(
            text="❌ Нет", callback_data=f"manage_server|{server_name}"
        ),
    )
    return builder.as_markup()


def build_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="servers_editor"
        )
    )
    return builder.as_markup()
