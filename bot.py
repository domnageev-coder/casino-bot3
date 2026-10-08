import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

BOT_TOKEN = "8220061421:AAHqOFSyXM029zUAr_3hd2tXaOX19cwfJ6U"

# ⚠️ Вкажіть ПРАВИЛЬНОЕ URL від GitHub Pages (не github.com/...)
WEB_APP_URL = "https://domnageev-coder.github.io/casino-bot3/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_keyboard():
    kb = [
        [
            # Кнопка открытия виджета прямо в Telegram
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать!**\nНажмите кнопку ниже, чтобы открыть игровой виджет:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# --- ЗАПУСК БОТА ---
async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
