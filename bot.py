import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

BOT_TOKEN = "8220061421:AAHqOFSyXM029zUAr_3hd2tXaOX19cwfJ6U"
BOT_USERNAME = "playadoptroblox_bot"  # Юзернейм вашего бота
WEB_APP_URL = "https://domnageev-coder.github.io/casino-bot3/"

# Ваш Telegram ID для админки и получения заявок на вывод
ADMIN_ID = 8761610032  # 👈 УКАЖИТЕ ВАШ TELEGRAM ID

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
conn = sqlite3.connect("casino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    referrer_id INTEGER DEFAULT NULL
)
""")
conn.commit()

def db_add_user(user_id: int, username: str, referrer_id: int = None):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", 
                       (user_id, username, referrer_id))
        if referrer_id:
            cursor.execute("UPDATE users SET balance = balance + 250 WHERE user_id = ?", (referrer_id,))
        conn.commit()

def db_get_user(user_id: int):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def db_update_balance(user_id: int, amount: int):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def db_add_all_balance(amount: int):
    cursor.execute("UPDATE users SET balance = balance + ?", (amount,))
    conn.commit()

def db_sub_all_balance(amount: int):
    cursor.execute("UPDATE users SET balance = MAX(0, balance - ?)", (amount,))
    conn.commit()

def db_get_stats():
    cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
    return cursor.fetchone()

def db_get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# --- FSM СОСТОЯНИЯ ---
class AdminStates(StatesGroup):
    give_all = State()
    take_all = State()
    user_action_id = State()
    user_action_amount = State()
    broadcast_msg = State()

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())

# --- КЛАВИАТУРЫ ---
def main_keyboard(user_id: int):
    kb = [
        [
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
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_keyboard():
    kb = [
        [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎁 Выдать всем валюту", callback_data="admin_give_all"),
         InlineKeyboardButton(text="🔥 Забрать у всех валюту", callback_data="admin_take_all")],
        [InlineKeyboardButton(text="👤 Изменить баланс игрока", callback_data="admin_user_manage")],
        [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ КОМАНД И ССЫЛОК ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == message.from_user.id:
            referrer_id = None

    db_add_user(message.from_user.id, message.from_user.username or "Игрок", referrer_id)
    
    await message.answer(
        "👋 **Добро пожаловать в Казино!**\nНажмите кнопку ниже, чтобы открыть игровой виджет:",
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await message.answer(
        "🛠 **Панель Администратора**\nВыберите необходимое действие:",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )

# --- АДМИН-ПАНЕЛЬ И ПРОФИЛЬ ---
@dp.callback_query(F.data == "admin_panel")
async def process_admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    await callback.message.edit_text(
        "🛠 **Панель Администратора**\nВыберите необходимое действие:",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 **Добро пожаловать в Казино!**\nНажмите кнопку ниже, чтобы открыть игровой виджет:",
        reply_markup=main_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "profile")
async def process_profile(callback: types.CallbackQuery):
    user_data = db_get_user(callback.from_user.id)
    balance = user_data[0] if user_data else 0
    ref_link = f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"
    await callback.answer(
        f"👤 Ваш профиль\nID: {callback.from_user.id}\n💰 Баланс: {balance} монет\n\n🔗 Реф. ссылка: {ref_link}",
        show_alert=True
    )

# --- АДМИНСКИЕ ДЕЙСТВИЯ ---
@dp.callback_query(F.data == "admin_stats")
async def process_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    count, total_balance = db_get_stats()
    total_balance = total_balance or 0
    await callback.message.edit_text(
        f"📊 **Статистика бота**\n\n👥 Всего игроков: `{count}`\n💰 Монет в системе: `{total_balance}`",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "admin_give_all")
async def process_give_all_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.give_all)
    await callback.message.answer("✏️ Введите сумму, которую выдать **всем игрокам**:")

@dp.message(AdminStates.give_all)
async def process_give_all_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    amount = int(message.text)
    db_add_all_balance(amount)
    await state.clear()
    await message.answer(f"✅ Выдано по **{amount} монет** всем игрокам!")

@dp.callback_query(F.data == "admin_take_all")
async def process_take_all_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.take_all)
    await callback.message.answer("✏️ Введите сумму, которую списать у **всех игроков**:")

@dp.message(AdminStates.take_all)
async def process_take_all_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    amount = int(message.text)
    db_sub_all_balance(amount)
    await state.clear()
    await message.answer(f"🔥 Списано по **{amount} монет** у всех игроков!")

@dp.callback_query(F.data == "admin_user_manage")
async def process_user_manage_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.user_action_id)
    await callback.message.answer("✏️ Введите **Telegram ID** игрока:")

@dp.message(AdminStates.user_action_id)
async def process_user_manage_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Telegram ID должен состоять из цифр.")
        return
    await state.update_data(target_id=int(message.text))
    await state.set_state(AdminStates.user_action_amount)
    await message.answer("✏️ Введите сумму (`500` или `-200`):")

@dp.message(AdminStates.user_action_amount)
async def process_user_manage_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите корректное число.")
        return
    data = await state.get_data()
    db_update_balance(data["target_id"], amount)
    await state.clear()
    await message.answer(f"✅ Для ID `{data['target_id']}` успешно изменено на **{amount} монет**.")

@dp.callback_query(F.data == "admin_broadcast")
async def process_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.broadcast_msg)
    await callback.message.answer("📢 Введите текст анонса:")

@dp.message(AdminStates.broadcast_msg)
async def process_broadcast_finish(message: types.Message, state: FSMContext):
    users = db_get_all_users()
    await state.clear()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **АНОНС**\n\n{message.text}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"🚀 Доставлено **{sent}** из `{len(users)}` пользователей!")

# --- ПРИЕМ ДАННЫХ ИЗ MINI APP (ЗАЯВКА НА ВЫВОД ПРЕДМЕТА) ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = message.web_app_data.data
    # Отправка уведомления администратору о заявке на вывод
    await bot.send_message(
        ADMIN_ID,
        f"🚨 **ЗАЯВКА НА ВЫВОД ПРЕДМЕТА!**\n\n"
        f"👤 **Игрок:** @{message.from_user.username or 'без_юзернейма'}\n"
        f"🆔 **ID:** `{message.from_user.id}`\n"
        f"📦 **Запрошенный вывод:** {data}",
        parse_mode="Markdown"
    )
    await message.answer("✅ Заявка отправлена администратору! Ожидайте выдачи.")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
