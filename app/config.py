import os

# ==========================================
# Open Lifestyle UA — Configuration File
# Version: 1.1
# ==========================================

# Токен бота (берётся из переменных окружения Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Username обязательного канала (БЕЗ символа @)
REQUIRED_CHANNEL = "open_lifestyle_ua"

# ID обязательного канала
REQUIRED_CHANNEL_ID = -1003717958620

# Включена ли проверка обязательной подписки
SUBSCRIPTION_CHECK_ENABLED = True
