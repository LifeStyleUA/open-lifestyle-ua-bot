import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.exceptions import ChatNotFound, UserNotParticipant

import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)


# =========================
# Перевірка підписки
# =========================
async def check_subscription(user_id: int) -> bool:
    if not config.SUBSCRIPTION_CHECK_ENABLED:
        return True

    try:
        chat_member = await bot.get_chat_member(
            chat_id=f"@{config.REQUIRED_CHANNEL}",
            user_id=user_id
        )

        if chat_member.status in ["member", "creator", "administrator"]:
            return True
        else:
            return False

    except (ChatNotFound, UserNotParticipant):
        return False


# =========================
# Клавіатура підписки
# =========================
def subscription_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="📢 Підписатися",
            url=f"https://t.me/{config.REQUIRED_CHANNEL}"
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Перевірити підписку",
            callback_data="check_sub"
        )
    )
    return keyboard


# =========================
# Команда /start
# =========================
@dp.message_handler(CommandStart())
async def start_handler(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)

    if not is_subscribed:
        await message.answer(
            "❗ Для використання бота необхідно підписатися на канал.",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer("Ласкаво просимо до Open Lifestyle UA 🚀")


# =========================
# Перевірка кнопки
# =========================
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def process_check_subscription(callback_query: types.CallbackQuery):
    is_subscribed = await check_subscription(callback_query.from_user.id)

    if is_subscribed:
        await callback_query.message.edit_text(
            "✅ Підписку підтверджено.\nЛаскаво просимо до Open Lifestyle UA 🚀"
        )
    else:
        await callback_query.answer("❌ Ви ще не підписані.", show_alert=True)


# =========================
# Запуск
# =========================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
  
