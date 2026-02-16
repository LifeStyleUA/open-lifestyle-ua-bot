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


# =========================
# Проверка подписки
# =========================
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


def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Підписатися",
                    url=f"https://t.me/{config.REQUIRED_CHANNEL}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Перевірити підписку",
                    callback_data="check_sub"
                )
            ]
        ]
    )


# =========================
# Состояния анкеты
# =========================
class Survey(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()


# =========================
# /start
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    if not await check_subscription(message.from_user.id):
        await message.answer(
            "Щоб користуватися ботом, підпишіться на канал:",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer(
        "👋 Вітаємо в Open Lifestyle UA!\n\n"
        "Давайте познайомимось. Міні-анкета займе 30 секунд 😊"
    )

    await message.answer("1️⃣ Скільки вам років?")
    await state.set_state(Survey.q1)


# =========================
# Проверка кнопки подписки
# =========================
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("Дякуємо за підписку! Напишіть /start ще раз 😊")
    else:
        await callback.answer("Ви ще не підписані!", show_alert=True)


# =========================
# Вопрос 1
# =========================
@dp.message(Survey.q1)
async def question_1(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("2️⃣ Ви чоловік чи жінка?")
    await state.set_state(Survey.q2)


# =========================
# Вопрос 2
# =========================
@dp.message(Survey.q2)
async def question_2(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("3️⃣ Яка ваша головна ціль зараз?")
    await state.set_state(Survey.q3)


# =========================
# Вопрос 3
# =========================
@dp.message(Survey.q3)
async def question_3(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)

    data = await state.get_data()

    await message.answer(
        "✅ Дякуємо за відповіді!\n\n"
        f"📌 Вік: {data['age']}\n"
        f"📌 Стать: {data['gender']}\n"
        f"📌 Ціль: {data['goal']}\n\n"
        "Скоро ви отримаєте персоналізований контент 💚"
    )

    await state.clear()


# =========================
# Запуск
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
