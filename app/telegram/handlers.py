from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime, time

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.db.session import get_engine
from app.telegram.callbacks import TelegramCallbackRouter, build_root_menu_markup
from app.telegram.commands import TelegramCommandService

router = Router(name="telegram-runtime")
_callback_router: TelegramCallbackRouter | None = None

_USAGE = {
    "client_master": "Использование: /client_master <master_id>",
    "client_slots": "Использование: /client_slots <master_id> <YYYY-MM-DD>",
    "client_book": "Использование: /client_book <master_id> <service_type> <YYYY-MM-DDTHH:MM:SS+00:00>",
    "client_cancel": "Использование: /client_cancel <booking_id>",
    "master_cancel": "Использование: /master_cancel <booking_id> <reason>",
    "master_dayoff": "Использование: /master_dayoff <YYYY-MM-DDTHH:MM:SS+00:00> <YYYY-MM-DDTHH:MM:SS+00:00> [block_id]",
    "master_lunch": "Использование: /master_lunch <HH:MM:SS> <HH:MM:SS>",
    "master_manual": "Использование: /master_manual <service_type> <YYYY-MM-DDTHH:MM:SS+00:00> <client_name>",
}


def configure_dispatcher(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(router)


def _service() -> TelegramCommandService:
    return TelegramCommandService(get_engine())


def _callbacks() -> TelegramCallbackRouter:
    global _callback_router
    if _callback_router is None:
        _callback_router = TelegramCallbackRouter(get_engine())
    return _callback_router


@router.message(Command("start"))
async def show_start(message: Message) -> None:
    if message.from_user is None:
        return
    result = _callbacks().start_menu(telegram_user_id=message.from_user.id)
    await message.answer(result.text, reply_markup=result.reply_markup)


@router.message(Command("help"))
async def show_help(message: Message) -> None:
    if message.from_user is None:
        return
    result = _service().help(telegram_user_id=message.from_user.id)
    await message.answer(result.text, reply_markup=build_root_menu_markup())


@router.message(Command("client_start"))
async def client_start(message: Message) -> None:
    if message.from_user is None:
        return
    result = _service().client_start(telegram_user_id=message.from_user.id)
    _callbacks().seed_root_menu(message.from_user.id)
    await _reply_with_notifications(
        message=message,
        text=result.text,
        notifications=result.notifications,
        reply_markup=build_root_menu_markup(),
    )


@router.message(Command("client_master"))
async def client_master(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["client_master"])
        return
    try:
        master_id = int(command.args.strip())
    except ValueError:
        await message.answer(_USAGE["client_master"])
        return
    result = _service().client_select_master(
        telegram_user_id=message.from_user.id,
        master_id=master_id,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("client_slots"))
async def client_slots(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["client_slots"])
        return
    parts = command.args.split()
    if len(parts) != 2:
        await message.answer(_USAGE["client_slots"])
        return
    try:
        master_id = int(parts[0])
        on_date = date.fromisoformat(parts[1])
    except ValueError:
        await message.answer(_USAGE["client_slots"])
        return
    result = _service().client_slots(
        telegram_user_id=message.from_user.id,
        master_id=master_id,
        on_date=on_date,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("client_book"))
async def client_book(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["client_book"])
        return
    parts = command.args.split()
    if len(parts) != 3:
        await message.answer(_USAGE["client_book"])
        return
    try:
        master_id = int(parts[0])
        service_type = parts[1]
        slot_start = datetime.fromisoformat(parts[2])
    except ValueError:
        await message.answer(_USAGE["client_book"])
        return
    result = _service().client_confirm(
        telegram_user_id=message.from_user.id,
        master_id=master_id,
        service_type=service_type,
        slot_start=slot_start,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("client_cancel"))
async def client_cancel(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["client_cancel"])
        return
    try:
        booking_id = int(command.args.strip())
    except ValueError:
        await message.answer(_USAGE["client_cancel"])
        return
    result = _service().client_cancel(
        telegram_user_id=message.from_user.id,
        booking_id=booking_id,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("master_cancel"))
async def master_cancel(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["master_cancel"])
        return
    parts = command.args.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer(_USAGE["master_cancel"])
        return
    try:
        booking_id = int(parts[0])
    except ValueError:
        await message.answer(_USAGE["master_cancel"])
        return
    result = _service().master_cancel(
        telegram_user_id=message.from_user.id,
        booking_id=booking_id,
        reason=parts[1],
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("master_dayoff"))
async def master_dayoff(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["master_dayoff"])
        return
    parts = command.args.split()
    if len(parts) not in {2, 3}:
        await message.answer(_USAGE["master_dayoff"])
        return
    try:
        start_at = datetime.fromisoformat(parts[0])
        end_at = datetime.fromisoformat(parts[1])
        block_id = int(parts[2]) if len(parts) == 3 else None
    except ValueError:
        await message.answer(_USAGE["master_dayoff"])
        return
    result = _service().master_day_off(
        telegram_user_id=message.from_user.id,
        start_at=start_at,
        end_at=end_at,
        block_id=block_id,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("master_lunch"))
async def master_lunch(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["master_lunch"])
        return
    parts = command.args.split()
    if len(parts) != 2:
        await message.answer(_USAGE["master_lunch"])
        return
    try:
        lunch_start = time.fromisoformat(parts[0])
        lunch_end = time.fromisoformat(parts[1])
    except ValueError:
        await message.answer(_USAGE["master_lunch"])
        return
    result = _service().master_lunch(
        telegram_user_id=message.from_user.id,
        lunch_start=lunch_start,
        lunch_end=lunch_end,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


@router.message(Command("master_manual"))
async def master_manual(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    if not command.args:
        await message.answer(_USAGE["master_manual"])
        return
    parts = command.args.split(maxsplit=2)
    if len(parts) != 3:
        await message.answer(_USAGE["master_manual"])
        return
    try:
        service_type = parts[0]
        slot_start = datetime.fromisoformat(parts[1])
        client_name = parts[2]
    except ValueError:
        await message.answer(_USAGE["master_manual"])
        return
    result = _service().master_manual(
        telegram_user_id=message.from_user.id,
        service_type=service_type,
        slot_start=slot_start,
        client_name=client_name,
    )
    await _reply_with_notifications(message=message, text=result.text, notifications=result.notifications)


async def _reply_with_notifications(
    *,
    message: Message,
    text: str,
    notifications: list[dict[str, object]],
    reply_markup=None,
) -> None:
    await message.answer(text, reply_markup=reply_markup)
    if message.from_user is None:
        return
    await _send_notifications(
        bot=message.bot,
        notifications=notifications,
        sender_telegram_user_id=message.from_user.id,
    )


async def _send_notifications(
    *,
    bot: Bot,
    notifications: list[dict[str, object]],
    sender_telegram_user_id: int,
) -> None:
    for notification in notifications:
        recipient = notification.get("recipient_telegram_user_id")
        text = notification.get("message")
        if not isinstance(recipient, int) or not isinstance(text, str):
            continue
        if recipient == sender_telegram_user_id:
            continue
        with suppress(Exception):
            await bot.send_message(chat_id=recipient, text=text)


@router.callback_query()
async def callback_router(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        return
    result = _callbacks().handle(
        telegram_user_id=callback.from_user.id,
        data=callback.data,
    )
    with suppress(Exception):
        await callback.answer()
    if callback.message is None:
        return
    await callback.message.answer(result.text, reply_markup=result.reply_markup)
    await _send_notifications(
        bot=callback.bot,
        notifications=result.notifications,
        sender_telegram_user_id=callback.from_user.id,
    )
