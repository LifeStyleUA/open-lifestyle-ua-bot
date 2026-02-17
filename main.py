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

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")  # Render автоматически даёт URL
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ==================================================
# Клавиатуры
# ==================================================
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
# Состояния
# ==================================================
class Survey(StatesGroup):
    age_confirm = State()
    user_type = State()


# ==================================================
# START
# ==================================================
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "👋 Вітаємо в Open Lifestyle UA!\n\n"
        "Перед початком невелике уточнення."
    )

    await message.answer(
        "🔞 Вам вже є 21?",
        reply_markup=age_keyboard()
    )

    await state.set_state(Survey.age_confirm)


# ==================================================
# Возраст
# ==================================================
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


# ==================================================
# Тип пользователя
# ==================================================
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
# WEBHOOK
# ==================================================
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, dp.webhook_handler())

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))


if __name__ == "__main__":
    main()
