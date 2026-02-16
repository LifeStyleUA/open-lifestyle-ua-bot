import asyncio
import logging
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

import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ==================================================
# Проверка подписки
# ==================================================
async def check_subscription(user_id: int) -> bool:
    if not config.SUBSCRIPTION_CHECK_ENABLED:
        return True

    try:
        member = await bot.get_chat_member(
            chat_id=f"@{config.REQUIRED_CHANNEL}",
            user_id=user_id
        )

        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }

    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False


def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Підписатися",
                    url=f"https://t.me/{config.REQUIRED_CHANNEL}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Перевірити підписку",
                    callback_data="check_sub"
                )
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
    age = State()
    user_type = State()
    goal = State()


# ==================================================
# START
# ==================================================
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    if not await check_subscription(message.from_user.id):
        await message.answer(
            "Щоб користуватися ботом, підпишіться на канал:",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer(
        "👋 Вітаємо в Open Lifestyle UA!\n\n"
        "Міні-анкета займе 30 секунд 😊"
    )

    await message.answer("1️⃣ Скільки вам років?")
    await state.set_state(Survey.age)


# ==================================================
# Проверка подписки
# ==================================================
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("🎉 Дякуємо за підписку! Починаємо.")
        await start_handler(callback.message, state)
    else:
        await callback.answer("Ви ще не підписані ❗", show_alert=True)


# ==================================================
# ВОЗРАСТ
# ==================================================
@dp.message(Survey.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть вік числом.")
        return

    age = int(message.text)

    if age < 18 or age > 100:
        await message.answer("Бот доступний лише для 18+ 😉")
        return

    await state.update_data(age=age)

    await message.answer(
        "2️⃣ Ви: Пара? Жінка? Чоловік?",
        reply_markup=user_type_keyboard()
    )

    await state.set_state(Survey.user_type)


# ==================================================
# ТИП КОРИСТУВАЧА
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

    await state.update_data(user_type=user_type)

    await callback.message.edit_text("3️⃣ Яка ваша головна ціль зараз?")
    await state.set_state(Survey.goal)


# ==================================================
# ЦІЛЬ
# ==================================================
@dp.message(Survey.goal)
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)

    data = await state.get_data()

    await message.answer(
        "✅ Дякуємо за відповіді!\n\n"
        f"📌 Вік: {data['age']}\n"
        f"📌 Ви: {data['user_type']}\n"
        f"📌 Ціль: {data['goal']}\n\n"
        "Ми раді, що ви з нами 💚"
    )

    await state.clear()


# ==================================================
# FALLBACK
# ==================================================
@dp.message()
async def fallback_handler(message: Message):
    await message.answer("Напишіть /start щоб почати 😊")


# ==================================================
# Запуск
# ==================================================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
