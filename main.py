import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web

import config

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = config.BOT_TOKEN
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "supersecret"  # можно любой строкой
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ==================================================
# СОСТОЯНИЯ
# ==================================================
class Survey(StatesGroup):
    age_confirm = State()
    user_type = State()


# ==================================================
# ПРОВЕРКА ПОДПИСКИ
# ==================================================
async def check_subscription(user_id: int) -> bool:
    if not config.SUBSCRIPTION_CHECK_ENABLED:
        return True

    try:
        chat_member = await bot.get_chat_member(
            chat_id=f"@{config.REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return chat_member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
        }
    except Exception:
        return False


# ==================================================
# КЛАВИАТУРЫ
# ==================================================
def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться",
                    url=f"https://t.me/{config.REQUIRED_CHANNEL}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Проверить подписку",
                    callback_data="check_sub"
                )
            ]
        ]
    )


def age_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Так", callback_data="age_yes"),
                InlineKeyboardButton(text="❌ Ні", callback_data="age_no"),
            ]
        ]
    )


def user_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👩 Жінка", callback_data="type_woman"),
                InlineKeyboardButton(text="👨 Чоловік", callback_data="type_man"),
            ],
            [
                InlineKeyboardButton(text="💑 Пара", callback_data="type_couple"),
            ]
        ]
    )


# ==================================================
# START
# ==================================================
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    if await check_subscription(message.from_user.id):
        await message.answer(
            "👋 Вітаємо в Open Lifestyle UA!\n\n"
            "🔞 Вам вже є 21?",
            reply_markup=age_keyboard()
        )
        await state.set_state(Survey.age_confirm)
    else:
        await message.answer(
            "Щоб користуватися ботом, підпишіться на канал:",
            reply_markup=subscription_keyboard()
        )


@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Дякуємо за підписку!\n\n"
            "🔞 Вам вже є 21?",
            reply_markup=age_keyboard()
        )
    else:
        await callback.answer("❌ Ви ще не підписані!", show_alert=True)


@dp.callback_query(Survey.age_confirm, F.data.startswith("age_"))
async def process_age(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "age_no":
        await callback.message.edit_text(
            "⛔ Бот доступний лише для користувачів 21+."
        )
        await state.clear()
        return

    await callback.message.edit_text("2️⃣ Ви: Пара? Жінка? Чоловік?")
    await callback.message.answer(
        "Оберіть варіант нижче:",
        reply_markup=user_type_keyboard()
    )

    await state.set_state(Survey.user_type)


@dp.callback_query(Survey.user_type, F.data.startswith("type_"))
async def process_user_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    mapping = {
        "type_woman": "Жінка",
        "type_man": "Чоловік",
        "type_couple": "Пара"
    }

    user_type = mapping.get(callback.data)

    await callback.message.edit_text(
        f"✅ Дякуємо!\n\n"
        f"📌 Ви: {user_type}\n\n"
        "Раді, що ви з нами 💚"
    )

    await state.clear()


# ==================================================
# WEBHOOK (AIROGRAM 3 ПРАВИЛЬНО)
# ==================================================
async def on_startup(app):
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET
    )
    logging.info(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


async def handle_webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)

    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response()


def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))


if __name__ == "__main__":
    main()
