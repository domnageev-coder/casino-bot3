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

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА_ЗДЕСЬ"  # Замените на токен вашего бота от @BotFather
ADMIN_ID = 7548882572                # Ваш Telegram ID для уведомлений и управления
WEBAPP_URL = "https://domnageev-coder.github.io/casino-bot3/" # Ссылка на ваш WebApp (GitHub Pages)
# ===================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Главная клавиатура с вашими кнопками
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

# Команда /start
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в PixelDrop Hub!**\n\n"
        "Открывайте кейсы, получайте редкие предметы и выводите их прямо в Roblox!\n\n"
        "Нажмите кнопку **«🎮 Открыть PixelDrop»** ниже, чтобы начать игру.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# Кнопка "📢 Канал"
@dp.message(F.text == "📢 Канал")
async def channel_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в канал 📢", url="https://t.me/fortunascase")]
    ])
    await message.answer("Подписывайтесь на наш официальный канал:", reply_markup=kb)

# Кнопка "💬 Чат"
@dp.message(F.text == "💬 Чат")
async def chat_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в чат 💬", url="https://t.me/fortunaschats")]
    ])
    await message.answer("Присоединяйтесь к нашему общему чату:", reply_markup=kb)

# Кнопка "💬 Обратная связь"
@dp.message(F.text == "💬 Обратная связь")
async def feedback_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать администратору 👤", url="https://t.me/hoikafun")]
    ])
    await message.answer("По всем вопросам и проблемам пишите в поддержку:", reply_markup=kb)

# ================= ОБРАБОТКА ДАННЫХ ИЗ WEBAPP =================
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")

        user_info = (
            f"👤 **Пользователь:** @{message.from_user.username or 'без_юзернейма'}\n"
            f"🆔 **ID:** `{message.from_user.id}`"
        )

        # 1. Заявка на вывод предмета в Roblox
        if action == "withdraw":
            roblox_user = data.get("roblox_user")
            item_name = data.get("item_name")
            item_val = data.get("item_value")

            admin_msg = (
                f"🚀 **НОВАЯ ЗАЯВКА НА ВЫВОД!**\n\n"
                f"{user_info}\n"
                f"🎮 **Ник в Roblox:** `{roblox_user}`\n"
                f"📦 **Предмет:** {item_name} (Стоимость: {item_val} R$)\n\n"
                f"⚠️ *Добавьте игрока в друзья (Gol5621) и передайте предмет!*"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            await message.answer("✅ **Заявка на вывод отправлена!** Администратор свяжется с вами и передаст предмет.")

        # 2. Запрос на пополнение картой / СБП
        elif action == "card_deposit_request":
            rub = data.get("rub_amount")
            coins = data.get("coins")

            admin_msg = (
                f"💳 **ЗАПРОС НА ПОПОЛНЕНИЕ КАРТОЙ!**\n\n"
                f"{user_info}\n"
                f"💵 **Сумма:** {rub} руб.\n"
                f"🪙 **Монет к начислению:** {coins} Coins\n\n"
                f"⚠️ *Проверьте поступление средств на карту перед выдачей баланса через админку!*"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            await message.answer("✅ **Заявка на пополнение отправлена!** Администратор проверит платёж и начислит монеты.")

        # 3. Выставление счёта в Telegram Stars (XTR)
        elif action == "stars_buy_request":
            stars = data.get("stars")
            coins = data.get("coins")

            prices = [LabeledPrice(label=f"{coins} Coins", amount=stars)]
            await bot.send_invoice(
                chat_id=message.chat.id,
                title=f"Пополнение {coins} Coins",
                description=f"Покупка {coins} Coins за {stars} Telegram Stars ⭐",
                payload=f"stars_deposit_{coins}_{stars}",
                provider_token="",  # Для Telegram Stars поле оставляем пустым
                currency="XTR",
                prices=prices
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке WebApp Data: {e}")

# Проверка оплаты Telegram Stars перед списыванием
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Успешная оплата Telegram Stars
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("stars_deposit_"):
        parts = payload.split("_")
        coins = parts[2]
        stars = parts[3]

        await message.answer(f"🎉 **Оплата успешна!** Вам начислено +{coins} Coins!")

        # Уведомление админу в ЛС
        admin_msg = (
            f"⭐ **ПОЛУЧЕНЫ TELEGRAM STARS!**\n\n"
            f"👤 **От:** @{message.from_user.username or 'без_юзернейма'} (ID: `{message.from_user.id}`)\n"
            f"⭐ **Получено:** {stars} Stars\n"
            f"🪙 **Выдано Coins:** {coins} Coins"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
