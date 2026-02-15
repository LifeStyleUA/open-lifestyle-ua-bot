import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


# Проверка подписки
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


# Клавиатура подписки
def subscription_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подписаться",
                    url=f"https://t.me/{config.REQUIRED_CHANNEL}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Проверить подписку",
                    callback_data="check_sub"
                )
            ]
        ]
    )
    return keyboard


@dp.message(CommandStart())
async def start_handler(message: Message):
    if await check_subscription(message.from_user.id):
        await message.answer("Добро пожаловать!")
    else:
        await message.answer(
            "Чтобы пользоваться ботом, подпишитесь на канал:",
            reply_markup=subscription_keyboard()
        )


@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("Спасибо за подписку! Теперь доступ открыт.")
    else:
        await callback.answer("Вы ещё не подписаны!", show_alert=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
