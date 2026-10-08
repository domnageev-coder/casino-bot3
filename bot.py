from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Укажите здесь ВАШУ ссылку, которую выдал GitHub Pages на Шаге 1
WEB_APP_URL = "https://github.com/domnageev-coder/casino-bot3/blob/main/index.html"

def main_keyboard():
    kb = [
        [
            # Кнопка для открытия виджета прямо в Telegram
            InlineKeyboardButton(
                text="🎮 Открыть Игровой Виджет", 
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="deposit_menu"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
