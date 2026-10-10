import logging
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    LabeledPrice,
    PreCheckoutQuery
)

# Токен вашего бота
BOT_TOKEN = "8220061421:AAHqOFSyXM029zUAr_3hd2tXaOX19cwfJ6U"
# Ваш Telegram ID
ADMIN_ID = 7548882572
# Ссылка на ваш WebApp
WEBAPP_URL = "https://domnageev-coder.github.io/casino-bot3/"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🎮 Открыть PixelDrop",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                KeyboardButton(text="📢 Канал"),
                KeyboardButton(text="💬 Чат")
            ],
            [
                KeyboardButton(text="💬 Обратная связь")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в PixelDrop!**\n\nНажмите кнопку ниже, чтобы открыть игровой виджет:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📢 Канал")
async def channel_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в канал 📢", url="https://t.me/fortunascase")]
    ])
    await message.answer("Подписывайтесь на наш официальный канал:", reply_markup=kb)

@dp.message(F.text == "💬 Чат")
async def chat_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в чат 💬", url="https://t.me/fortunaschats")]
    ])
    await message.answer("Общайтесь в нашем комьюнити-чате:", reply_markup=kb)

@dp.message(F.text == "💬 Обратная связь")
async def feedback_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать администратору 👤", url="https://t.me/hoikafun")]
    ])
    await message.answer("По всем вопросам и проблемам обращайтесь к нам:", reply_markup=kb)

# Обработка заявок и запросов из WebApp
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")

        user_info = f"👤 **Пользователь:** @{message.from_user.username or 'без_юзернейма'} (ID: `{message.from_user.id}`)"

        if action == "withdraw":
            roblox_user = data.get("roblox_user")
            item_name = data.get("item_name")
            item_val = data.get("item_value")

            admin_msg = (
                f"🚀 **ЗАЯВКА НА ВЫВОД ПРЕДМЕТА!**\n\n"
                f"{user_info}\n"
                f"🎮 **Roblox Ник:** `{roblox_user}`\n"
                f"📦 **Предмет:** {item_name} (Val: {item_val})\n\n"
                f"Добавьте пользователя в друзья и передайте предмет!"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            await message.answer("✅ Заявка отправлена администратору!")

        elif action == "card_deposit_request":
            rub = data.get("rub_amount")
            coins = data.get("coins")

            admin_msg = (
                f"💳 **ЗАПРОС НА ПОПОЛНЕНИЕ КАРТОЙ!**\n\n"
                f"{user_info}\n"
                f"💰 **Сумма:** {rub} Руб.\n"
                f"🪙 **Монет к начислению:** {coins} Coins"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            await message.answer("✅ Заявка отправлена администратору на проверку!")

        elif action == "stars_buy_request":
            stars = int(data.get("stars"))
            coins = data.get("coins")

            prices = [LabeledPrice(label=f"{coins} Coins", amount=stars)]
            
            # Генерируем специальную ссылку на оплату для WebApp
            invoice_link = await bot.create_invoice_link(
                title=f"Пополнение {coins} Coins",
                description=f"Покупка {coins} Coins за {stars} Telegram Stars",
                payload=f"stars_deposit_{coins}_{stars}",
                provider_token="", 
                currency="XTR",
                prices=prices
            )

            # Отправляем ссылку обратно в WebApp, чтобы сайт открыл нативное окно оплаты
            await message.answer(f"__INVOICE_LINK__{invoice_link}")

    except Exception as e:
        logging.error(f"Ошибка при обработке WebApp Data: {e}")

# Пре-чек платежа Telegram Stars
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Успешная оплата Telegram Stars (Автоматическое начисление)
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("stars_deposit_"):
        parts = payload.split("_")
        coins = parts[2]
        stars = parts[3]
        user_id = message.from_user.id

        # Успешное сообщение пользователю
        await message.answer(f"🎉 **Оплата успешна!** Вам зачислено +{coins} Coins 🪙")
        
        # Уведомление администратору
        admin_msg = (
            f"⭐ **ПОЛУЧЕНЫ TELEGRAM STARS!**\n\n"
            f"👤 **От:** @{message.from_user.username or 'без_юзернейма'} (ID: `{user_id}`)\n"
            f"⭐ **Получено звёзд:** {stars} Stars\n"
            f"🪙 **Выдано Coins:** {coins} Coins"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
