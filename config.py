import os

# Токен бота (будет браться из переменных окружения Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID обязательного канала для подписки
# ВАЖНО: заменить на реальный username канала БЕЗ @
REQUIRED_CHANNEL = "your_channel_username"

# Если используется ID канала вместо username
# Пример: -1001234567890
REQUIRED_CHANNEL_ID = None

# Режим запуска (polling или webhook)
MODE = "polling"

# Проверка обязательной подписки включена
SUBSCRIPTION_CHECK_ENABLED = True
