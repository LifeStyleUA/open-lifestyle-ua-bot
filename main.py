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

    if not await check_subscription(message.from_user.id):
        await message.answer(
            "Щоб користуватися ботом, підпишіться на канал:",
            reply_markup=subscription_keyboard()
        )
        return

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
# ПОДТВЕРЖДЕНИЕ ВОЗРАСТА
# ==================================================
@dp.callback_query(Survey.age_confirm, F.data.startswith("age_"))
async def process_age(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "age_no":
        await callback.message.edit_text(
            "⛔ На жаль, бот доступний лише для користувачів 21+."
        )
        await state.clear()
        return

    # Если age_yes
    await callback.message.edit_text("2️⃣ Ви: Пара? Жінка? Чоловік?")
    await callback.message.answer(
        "Оберіть варіант нижче:",
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

    await callback.message.edit_text(
        f"✅ Дякуємо!\n\n"
        f"📌 Ви: {user_type}\n\n"
        "Раді, що ви з нами 💚"
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
