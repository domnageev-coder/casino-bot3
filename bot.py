import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ⚠️ Вставьте сюда ваш токен бота от @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ⚠️ Вставьте сюда ваш личный Telegram ID (чтобы получать уведомления)
# Узнать свой ID можно у бота @userinfobot
ADMIN_ID = 123456789

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных в памяти
users_db = {}
withdraw_requests = {}  # Заявки на вывод

# База петов с шансами (%)
PETS_CASE = [
    {"icon": "🐹", "name": "Хомяк", "rarity": "Обычный", "price": 15.0, "chance": 50.0},
    {"icon": "🐱", "name": "Кот", "rarity": "Обычный", "price": 30.0, "chance": 30.0},
    {"icon": "🐶", "name": "Собака", "rarity": "Редкий", "price": 75.0, "chance": 14.0},
    {"icon": "🦊", "name": "Лис", "rarity": "Эпический", "price": 180.0, "chance": 5.0},
    {"icon": "🐉", "name": "Дракон", "rarity": "🔥 ЛЕГЕНДА", "price": 600.0, "chance": 1.0},
]


def get_user(user_id: int, username: str = "Игрок"):
    is_new = user_id not in users_db
    if is_new:
        users_db[user_id] = {
            "username": username,
            "balance": 500.0,
            "inventory": []
        }
    return users_db[user_id], is_new


def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Игра «Шарики»", callback_data="balls_menu")],
        [InlineKeyboardButton(text="📦 Открыть кейс", callback_data="open_case")],
        [InlineKeyboardButton(text="💸 Вывести деньги", callback_data="withdraw_menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])


# ==========================================
# 1. СТАРТ И УВЕДОМЛЕНИЯ О НОВЫХ ЮЗЕРАХ
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Без имени"
    user, is_new = get_user(user_id, username)

    # Уведомление админа о новом пользователе
    if is_new and ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 **Новый пользователь в боте!**\n\n"
                f"👤 Имя: {username}\n"
                f"🆔 ID: `{user_id}`\n"
                f"🔗 Юзернейм: @{message.from_user.username or 'нет'}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

    await message.answer(
        f"👋 **Привет, {username}!**\n\n"
        f"Ваш баланс: `{user['balance']:.2f}` монет.",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    user, _ = get_user(call.from_user.id)
    await call.message.edit_text(
        f"🏠 **Главное меню**\nВаш баланс: `{user['balance']:.2f}` монет",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    user, _ = get_user(call.from_user.id)
    await call.message.edit_text(
        f"👤 **Ваш профиль**\n\n"
        f"💰 Баланс: `{user['balance']:.2f}` монет\n"
        f"🎒 Предметов в инвентаре: `{len(user['inventory'])}` шт.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]]),
        parse_mode="Markdown"
    )


# ==========================================
# 2. ИГРА «ШАРИКИ» (ВЫБОР КОЛИЧЕСТВА)
# ==========================================

@dp.callback_query(F.data == "balls_menu")
async def balls_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 🔮 (20 м.)", callback_data="play_balls_1"),
            InlineKeyboardButton(text="2 🔮 (40 м.)", callback_data="play_balls_2"),
            InlineKeyboardButton(text="3 🔮 (60 м.)", callback_data="play_balls_3")
        ],
        [
            InlineKeyboardButton(text="5 🔮 (100 м.)", callback_data="play_balls_5")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        "🔮 **ИГРА «ШАРИКИ»**\n\n"
        "Выберите, сколько шариков запустим одновременно:\n"
        "*(Цена за 1 шарик — 20 монет)*",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("play_balls_"))
async def play_balls_handler(call: types.CallbackQuery):
    count = int(call.data.split("_")[2])
    cost = count * 20.0
    user, _ = get_user(call.from_user.id)

    if user["balance"] < cost:
        await call.answer(f"❌ Недостаточно средств! Нужно {cost} монет.", show_alert=True)
        return

    user["balance"] -= cost
    total_win = 0.0
    results_log = []

    # Моделирование запуска каждого шарика
    for i in range(1, count + 1):
        is_win = random.random() < 0.70  # Шанс 70%
        if is_win:
            mult = random.choice([1.2, 1.5, 2.0, 3.0])
            win = 20.0 * mult
            total_win += win
            results_log.append(f"🔮 Шарик #{i}: **Победа!** (x{mult}) ➔ +{win:.1f} м.")
        else:
            results_log.append(f"🔮 Шарик #{i}: **Мимо!** ➔ 0 м.")

    user["balance"] += total_win
    log_str = "\n".join(results_log)

    result_text = (
        f"🎰 **РЕЗУЛЬТАТ БРОСКА ({count} шт.):**\n\n"
        f"{log_str}\n\n"
        f"📊 Всего получено: **+{total_win:.2f}** монет\n"
        f"💰 Ваш баланс: `{user['balance']:.2f}` монет"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Повторить бросок", callback_data=call.data)],
        [InlineKeyboardButton(text="⬅️ Меню шариков", callback_data="balls_menu")]
    ])
    await call.message.edit_text(result_text, reply_markup=kb, parse_mode="Markdown")


# ==========================================
# 3. КЕЙСЫ С ЯЧЕЙКАМИ И ПРОЦЕНТАМИ
# ==========================================

@dp.callback_query(F.data == "open_case")
async def open_case_handler(call: types.CallbackQuery):
    user, _ = get_user(call.from_user.id)
    cost = 100.0

    if user["balance"] < cost:
        await call.answer("❌ Недостаточно средств! Кейс стоит 100 монет.", show_alert=True)
        return

    user["balance"] -= cost

    # Выбор пета по весам шансов
    weights = [p["chance"] for p in PETS_CASE]
    won = random.choices(PETS_CASE, weights=weights, k=1)[0]
    user["balance"] += won["price"]

    # Формирование карточки-ячейки с шансами
    cell_ui = (
        f"📦 **ОТКРЫТИЕ КЕЙСВА** (100 монет)\n\n"
        f"┌────────────────────────────┐\n"
        f"│  ВЫПАЛ ПЕТ:               │\n"
        f"│  {won['icon']} **{won['name'].upper()}**\n"
        f"├────────────────────────────┤\n"
        f"│ 🔹 Редкость: {won['rarity']:<12} │\n"
        f"│ 📊 Шанс выпадения: {won['chance']}%  │\n"
        f"│ 💵 Продано за: +{won['price']:.1f} м.   │\n"
        f"└────────────────────────────┘\n\n"
        f"💰 Ваш баланс: `{user['balance']:.2f}` монет"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще раз (100 монет)", callback_data="open_case")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(cell_ui, reply_markup=kb, parse_mode="Markdown")


# ==========================================
# 4. СИСТЕМА ВЫВОДА СРЕСТВ И УВЕДОМЛЕНИЙ
# ==========================================

@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Вывод на Карту (от 300 м.)", callback_data="req_withdraw_card")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        "💸 **Заявка на вывод средств**\n\n"
        "Выберите способ для отправки запроса администратору:",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "req_withdraw_card")
async def process_withdraw_request(call: types.CallbackQuery):
    user_id = call.from_user.id
    user, _ = get_user(user_id)
    amount = 300.0  # Сумма вывода

    if user["balance"] < amount:
        await call.answer(f"❌ Минимальная сумма вывода — {amount} монет!", show_alert=True)
        return

    # Списываем баланс временно на период обработки заявки
    user["balance"] -= amount
    req_id = f"w_{user_id}_{int(asyncio.get_event_loop().time())}"

    withdraw_requests[req_id] = {
        "user_id": user_id,
        "amount": amount
    }

    # Уведомляем администратора в ТГ с кнопками
    if ADMIN_ID:
        try:
            admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_app_{req_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_rej_{req_id}")
                ]
            ])
            await bot.send_message(
                ADMIN_ID,
                f"🚨 **НОВАЯ ЗАЯВКА НА ВЫВОД!**\n\n"
                f"👤 Пользователь: {call.from_user.first_name} (`{user_id}`)\n"
                f"💰 Сумма: **{amount}** монет\n"
                f"🆔 ID заявки: `{req_id}`",
                reply_markup=admin_kb,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка уведомления админа: {e}")

    await call.message.edit_text(
        f"✅ **Заявка #{req_id} принята!**\n\n"
        f"Сумма **{amount}** монет отправлена на проверку администратору.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]]),
        parse_mode="Markdown"
    )


# Обработка действий администратора по выводу
@dp.callback_query(F.data.startswith("adm_"))
async def admin_withdraw_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Вы не администратор!", show_alert=True)
        return

    action, req_id = call.data.split("_")[1], call.data.replace(f"adm_{call.data.split('_')[1]}_", "")
    req_data = withdraw_requests.get(req_id)

    if not req_data:
        await call.answer("Заявка не найдена или уже обработана.", show_alert=True)
        return

    target_user = users_db.get(req_data["user_id"])

    if action == "app":
        # Подтверждение
        await call.message.edit_text(f"✅ Заявка `{req_id}` **ОДОБРЕНА**.", parse_mode="Markdown")
        try:
            await bot.send_message(req_data["user_id"], f"🎉 Ваши средства ({req_data['amount']} монет) успешно переведены!")
        except Exception:
            pass
    elif action == "rej":
        # Отклонение и возврат средств
        if target_user:
            target_user["balance"] += req_data["amount"]
        await call.message.edit_text(f"❌ Заявка `{req_id}` **ОТКЛОНЕНА**. Средства возвращены.", parse_mode="Markdown")
        try:
            await bot.send_message(req_data["user_id"], f"❌ Ваша заявка на вывод была отклонена. Средства вернулись на баланс.")
        except Exception:
            pass

    del withdraw_requests[req_id]


async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())