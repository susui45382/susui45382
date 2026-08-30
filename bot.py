import telebot
from telebot import types
import requests
import re
import os
import sqlite3
import sys

# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631269601:AAH5keWN0qXjK60H8GTN5G-MLpqQTapxCuM"

# STOCK GROUPS/CHANNELS
GMAIL_GROUP_ID = -1004388026969
NUMBER_GROUP_ID = -1004418431812
FB_GROUP_ID = -1003966946655
TWITTER_GROUP_ID = -1003851497827
INSTA_GROUP_ID = -1003988074533

# ALERT / LOG / BROADCAST CHANNEL
RAW_CHANNEL_ID = "4418224009"

if not str(RAW_CHANNEL_ID).startswith("-100"):
    LOG_CHANNEL_ID = int(f"-100{RAW_CHANNEL_ID.replace('-', '')}")
else:
    LOG_CHANNEL_ID = int(RAW_CHANNEL_ID)

ADMIN_USER_ID = 6403557650
OCR_API_KEY = "K83665952588957"
ADMIN_USERNAME = "BhaiCharaYT"

DB_FILE = "bot_database.db"
USERS_FILE = "registered_users.txt"

# =========================================================
# PAYMENT CONFIG
# =========================================================

EXPECTED_AMOUNT = "30"
UPI_ID = "paytm.s26tbd7@pty"
UPI_NAME = "Mr Subham"
QR_PINNED_MESSAGE_ID = 39

EXPECTED_NAME_KEYWORDS = ["DICTATOR", "MERCHANT", "SHOP", "SUBHAM"]

# =========================================================
# DATABASE SETUP (PERMANENT STORAGE)
# =========================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    # Used UTRs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS used_utrs (utr TEXT PRIMARY KEY)''')
    # Stock table
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT,
                        msg_id INTEGER,
                        text_data TEXT
                    )''')
    # User Purchases table
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        utr TEXT,
                        data TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()

# Temporary in-memory states (not critical across restarts)
user_states = {}
temp_number_requests = {}

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# DATABASE HELPER FUNCTIONS
# =========================================================

def save_user_id(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()
    
    # Text file backup
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = set(line.strip() for line in f.readlines())
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{str(chat_id)}\n")

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [str(row[0]) for row in rows]

def add_utr(utr):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO used_utrs (utr) VALUES (?)", (utr,))
    conn.commit()
    conn.close()

def is_utr_used(utr):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT utr FROM used_utrs WHERE utr = ?", (utr,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def add_stock(category, msg_id, text_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stock (category, msg_id, text_data) VALUES (?, ?, ?)", (category, msg_id, text_data))
    conn.commit()
    conn.close()

def pop_stock(category):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, msg_id, text_data FROM stock WHERE category = ? ORDER BY id ASC LIMIT 1", (category,))
    row = cursor.fetchone()
    if row:
        stock_id, msg_id, text_data = row
        cursor.execute("DELETE FROM stock WHERE id = ?", (stock_id,))
        conn.commit()
        conn.close()
        return {"msg_id": msg_id, "text": text_data}
    conn.close()
    return None

def get_stock_count(category):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock WHERE category = ?", (category,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_purchase(user_id, utr, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (user_id, utr, data) VALUES (?, ?, ?)", (user_id, utr, data))
    conn.commit()
    conn.close()

def get_user_purchases(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT utr, data FROM purchases WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"utr": r[0], "data": r[1]} for r in rows]

def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"[LOG ERROR] {e}")

# =========================================================
# AUTO BROADCAST ON BOT RESTART
# =========================================================

def notify_restart():
    if "--restarted" in sys.argv:
        users = get_all_users()
        msg = "⚡ **Bot is Online & Active!**\n\nAap ab service use kar sakte hain."
        for uid in users:
            try:
                bot.send_message(int(uid), msg, parse_mode="Markdown")
            except Exception:
                pass
        send_log("🔄 **Bot Restart Notification Sent To All Users!**")

# =========================================================
# HANDLERS & COMMANDS
# =========================================================

@bot.channel_post_handler(func=lambda message: message.chat.id == LOG_CHANNEL_ID)
def handle_channel_commands(message):
    text = message.text.strip() if message.text else ""

    if text.lower() == "/user":
        users = get_all_users()
        if not users:
            bot.send_message(LOG_CHANNEL_ID, "📊 **Registered Users List:**\n\nKoi user registered nahi hai.", parse_mode="Markdown")
            return

        user_list_text = f"📊 **REGISTERED USERS LIST (Total: {len(users)})**\n\n"
        for idx, uid in enumerate(users, start=1):
            try:
                chat = bot.get_chat(int(uid))
                username = f"@{chat.username}" if chat.username else "No Username"
                first_name = chat.first_name if chat.first_name else "User"
                user_list_text += f"{idx}. {first_name} | {username} | `{uid}`\n"
            except Exception:
                user_list_text += f"{idx}. Unknown User | `{uid}`\n"

        bot.send_message(LOG_CHANNEL_ID, user_list_text, parse_mode="Markdown")
        return

    if text.lower().startswith("/broadcast"):
        broadcast_msg = text[10:].strip()
        if not broadcast_msg:
            bot.send_message(LOG_CHANNEL_ID, "⚠️ **Format:** `/broadcast Aapka Message Yaha`", parse_mode="Markdown")
            return

        users = get_all_users()
        if not users:
            bot.send_message(LOG_CHANNEL_ID, "❌ Broadcast karne ke liye koi user nahi mila.", parse_mode="Markdown")
            return

        success_count = 0
        failed_count = 0

        for uid in users:
            try:
                bot.send_message(int(uid), broadcast_msg, parse_mode="Markdown")
                success_count += 1
            except Exception:
                failed_count += 1

        bot.send_message(
            LOG_CHANNEL_ID, 
            f"✅ **Broadcast Completed!**\n\n📤 **Sent:** `{success_count}` Users\n❌ **Failed:** `{failed_count}` Users", 
            parse_mode="Markdown"
        )
        return

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        "📧 Sell Gmail",
        "🛒 Buy Gmail",
        "👤 Profile",
        "📞 Buy Number",
        "🆘 Support",
        "📑 My Submitted",
        "👥 Buy Facebook",
        "🐦 Buy Twitter",
        "📸 Buy Instagram"
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.chat.id] = None
    save_user_id(message.chat.id)

    welcome_text = (
        f"👋 Welcome **{message.from_user.first_name}**!\n\n"
        "📧 **Gmail Store & OTP Number Bot** me aapka swagat hai."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    
    send_log(
        f"🚀 **Bot Started**\n\n"
        f"👤 **Name:** {message.from_user.first_name}\n"
        f"🌐 **Username:** @{message.from_user.username if message.from_user.username else 'None'}\n"
        f"🆔 **User ID:** `{message.chat.id}`"
    )

@bot.message_handler(commands=['botstatus'])
def check_bot_status(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    users = get_all_users()
    bot.send_message(message.chat.id, f"📊 **BOT STATUS**\n\n👥 **Total Users:** `{len(users)}`", parse_mode="Markdown")

# Stock Capture
@bot.message_handler(func=lambda message: message.chat.id == GMAIL_GROUP_ID, content_types=['text'])
def capture_gmail_stock(message):
    add_stock("gmail", message.message_id, message.text.strip())
    send_log(f"📦 **Stock Added (Gmail)** | Total: {get_stock_count('gmail')}")

@bot.message_handler(func=lambda message: message.chat.id == NUMBER_GROUP_ID, content_types=['text'])
def capture_number_stock(message):
    add_stock("number", message.message_id, message.text.strip())
    send_log(f"📦 **Stock Added (Number)** | Total: {get_stock_count('number')}")

@bot.message_handler(func=lambda message: message.chat.id == FB_GROUP_ID, content_types=['text'])
def capture_fb_stock(message):
    add_stock("facebook", message.message_id, message.text.strip())
    send_log(f"📦 **Stock Added (Facebook)** | Total: {get_stock_count('facebook')}")

@bot.message_handler(func=lambda message: message.chat.id == TWITTER_GROUP_ID, content_types=['text'])
def capture_twitter_stock(message):
    add_stock("twitter", message.message_id, message.text.strip())
    send_log(f"📦 **Stock Added (Twitter)** | Total: {get_stock_count('twitter')}")

@bot.message_handler(func=lambda message: message.chat.id == INSTA_GROUP_ID, content_types=['text'])
def capture_insta_stock(message):
    add_stock("instagram", message.message_id, message.text.strip())
    send_log(f"📦 **Stock Added (Instagram)** | Total: {get_stock_count('instagram')}")

@bot.message_handler(commands=['sendotp'])
def admin_send_otp(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Format: `/sendotp username 574375`", parse_mode="Markdown")
        return
    
    target_username = parts[1].replace("@", "").strip().lower()
    otp_code = parts[2].strip()
    
    users = get_all_users()
    found_chat_id = None
    for uid in users:
        try:
            chat_member = bot.get_chat(int(uid))
            if chat_member.username and chat_member.username.lower() == target_username:
                found_chat_id = int(uid)
                break
        except Exception:
            continue
            
    if found_chat_id:
        try:
            bot.send_message(found_chat_id, f"🚨 **YOUR OTP CODE RECEIVED!**\n\n🔑 **OTP:** `{otp_code}`", parse_mode="Markdown")
            bot.send_message(message.chat.id, f"✅ OTP `@{target_username}` ko bhej diya hai!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
    else:
        bot.send_message(message.chat.id, f"❌ Username (`@{target_username}`) nahi mila.")

# =========================================================
# MENU HANDLERS
# =========================================================

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_menu(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    save_user_id(user_id)

    if message.text == "📧 Sell Gmail":
        user_states[user_id] = "AWAITING_SELL_GMAIL"
        bot.send_message(user_id, "📧 **SELL GMAIL**\n\nGmail ID aur Password bhejein:\n`example@gmail.com : password123`", parse_mode="Markdown")

    elif message.text == "📞 Buy Number":
        cnt = get_stock_count("number")
        if cnt == 0:
            bot.send_message(user_id, "❌ **Number Out of Stock!**", parse_mode="Markdown")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💬 WhatsApp (₹30)", callback_data="pay_num_whatsapp"),
            types.InlineKeyboardButton("📱 Telegram (₹30)", callback_data="pay_num_telegram"),
            types.InlineKeyboardButton("👥 Facebook (₹30)", callback_data="pay_num_facebook"),
            types.InlineKeyboardButton("📸 Instagram (₹30)", callback_data="pay_num_instagram")
        )
        bot.send_message(user_id, f"📞 **BUY NUMBER**\n\n💵 Price: ₹{EXPECTED_AMOUNT}\n📦 Stock: {cnt}", reply_markup=markup, parse_mode="Markdown")

    elif message.text in ["🛒 Buy Gmail", "👥 Buy Facebook", "🐦 Buy Twitter", "📸 Buy Instagram"]:
        cat_map = {
            "🛒 Buy Gmail": ("gmail", "show_qr_gmail", "Gmail"),
            "👥 Buy Facebook": ("facebook", "show_qr_fb", "Facebook"),
            "🐦 Buy Twitter": ("twitter", "show_qr_twitter", "Twitter"),
            "📸 Buy Instagram": ("instagram", "show_qr_insta", "Instagram")
        }
        cat, cb_data, label = cat_map[message.text]
        cnt = get_stock_count(cat)
        if cnt == 0:
            bot.send_message(user_id, f"❌ **{label} Out of Stock!**", parse_mode="Markdown")
            return
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(types.InlineKeyboardButton("💳 Pay & Auto-Verify", callback_data=cb_data))
        bot.send_message(user_id, f"🛒 **Buy {label}**\n\n💵 Price: ₹{EXPECTED_AMOUNT}\n📦 Stock: {cnt}", reply_markup=inline_kb, parse_mode="Markdown")

    elif message.text == "👤 Profile":
        purchases = get_user_purchases(user_id)
        profile_text = (
            "👤 **YOUR PROFILE DETAILS**\n\n"
            f"📛 **Name:** {name}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🌐 **Username:** {username}\n"
            f"🛍️ **Total Bought:** `{len(purchases)}`\n"
            f"⚡ **Account Status:** Active ✅"
        )
        bot.send_message(user_id, profile_text, parse_mode="Markdown")

    elif message.text == "🆘 Support":
        support_kb = types.InlineKeyboardMarkup()
        support_kb.add(types.InlineKeyboardButton("💬 Contact Support Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}") )
        bot.send_message(user_id, "🆘 **CUSTOMER SUPPORT HUB**", parse_mode="Markdown", reply_markup=support_kb)

    elif message.text == "📑 My Submitted":
        purchases = get_user_purchases(user_id)
        if not purchases:
            bot.send_message(user_id, "📑 **MY PURCHASE HISTORY**\n\n❌ Koi item buy nahi kiya hai.", parse_mode="Markdown")
            return
        history_text = "📑 **YOUR PURCHASE HISTORY:**\n\n"
        for idx, item in enumerate(purchases, start=1):
            history_text += f"{idx}. **UTR:** `{item['utr']}`\n   **Data:** `{item['data']}`\n\n"
        bot.send_message(user_id, history_text, parse_mode="Markdown")

    else:
        if user_states.get(user_id) == "AWAITING_SELL_GMAIL":
            user_states[user_id] = None
            admin_msg = f"📩 **NEW GMAIL SUBMITTED**\n\n👤 **User:** [{name}](tg://user?id={user_id})\n🆔 `{user_id}`\n\n📝 **Data:**\n`{message.text}`"
            try:
                bot.send_message(ADMIN_USER_ID, admin_msg, parse_mode="Markdown")
            except Exception:
                pass
            bot.send_message(user_id, "✅ **Details Admin ko bhej di gayi hain!**", parse_mode="Markdown")

# Callback Handlers
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.message.chat.id
    save_user_id(user_id)

    states_map = {
        "pay_num_": ("AWAITING_NUMBER_PAYMENT_PROOF", "number"),
        "show_qr_gmail": ("AWAITING_PAYMENT_PROOF", "gmail"),
        "show_qr_fb": ("AWAITING_FB_PAYMENT_PROOF", "facebook"),
        "show_qr_twitter": ("AWAITING_TWITTER_PAYMENT_PROOF", "twitter"),
        "show_qr_insta": ("AWAITING_INSTA_PAYMENT_PROOF", "instagram")
    }

    state_to_set = None
    category = None

    for prefix, (st, cat) in states_map.items():
        if call.data.startswith(prefix):
            state_to_set = st
            category = cat
            if prefix == "pay_num_":
                service = call.data.split("_")[2]
                temp_number_requests[user_id] = {"service": service}
            break

    if category and get_stock_count(category) == 0:
        bot.answer_callback_query(call.id, "❌ Stock Out!", show_alert=True)
        return

    try:
        user_states[user_id] = state_to_set
        bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)
        payment_text = (
            f"💳 **Payment Request**\n\n💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
            f"👤 **UPI Name:** `{UPI_NAME}`\n📌 **UPI ID:** `{UPI_ID}`\n\n"
            "📲 Payment karke screenshot yahin bhejein."
        )
        bot.send_message(user_id, payment_text, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "✅ QR Sent!")
    except Exception:
        user_states[user_id] = None
        bot.answer_callback_query(call.id, "❌ Error sending QR!", show_alert=True)

# OCR Processing
def ocr_space_file(filename, api_key):
    url = "https://api.ocr.space/parse/image"
    with open(filename, "rb") as f:
        response = requests.post(url, files={"file": f}, data={"apikey": api_key, "language": "eng", "OCREngine": "2"}, timeout=60)
    result = response.json()
    if not result.get("IsErroredOnProcessing"):
        parsed_results = result.get("ParsedResults")
        if parsed_results:
            return parsed_results[0].get("ParsedText", "")
    return ""

@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.chat.id
    current_state = user_states.get(user_id)
    save_user_id(user_id)

    state_category_map = {
        "AWAITING_PAYMENT_PROOF": "gmail",
        "AWAITING_NUMBER_PAYMENT_PROOF": "number",
        "AWAITING_FB_PAYMENT_PROOF": "facebook",
        "AWAITING_TWITTER_PAYMENT_PROOF": "twitter",
        "AWAITING_INSTA_PAYMENT_PROOF": "instagram"
    }

    if current_state not in state_category_map:
        return

    bot.send_message(user_id, "🔍 **Analyzing Screenshot...**", parse_mode="Markdown")
    image_path = f"screenshot_{user_id}.jpg"

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(image_path, "wb") as new_file:
            new_file.write(downloaded_file)

        extracted_text = ocr_space_file(image_path, OCR_API_KEY)
        clean_text = extracted_text.upper()

        if os.path.exists(image_path):
            os.remove(image_path)

        utr_match = re.search(r"\b\d{12}\b", clean_text)
        utr_found = utr_match.group(0) if utr_match else None

        amount_verified = (EXPECTED_AMOUNT in clean_text or f"₹{EXPECTED_AMOUNT}" in clean_text)
        name_verified = any(keyword in clean_text for keyword in EXPECTED_NAME_KEYWORDS)

        if not utr_found or not amount_verified or not name_verified:
            user_states[user_id] = None
            bot.send_message(user_id, "❌ **Verification Failed!** Sahi screenshot bhejein.", parse_mode="Markdown")
            return

        if is_utr_used(utr_found):
            user_states[user_id] = None
            bot.send_message(user_id, f"❌ **Duplicate UTR!** UTR `{utr_found}` pehle use ho chuka hai.", parse_mode="Markdown")
            return

        category = state_category_map[current_state]
        stock_item = pop_stock(category)

        if not stock_item:
            bot.send_message(user_id, "❌ **Stock Out!** Admin se contact karein.")
            return

        add_utr(utr_found)
        user_states[user_id] = None

        data_content = stock_item["text"]
        if category == "number":
            service = temp_number_requests.get(user_id, {}).get("service", "NUMBER")
            data_content = f"[{service.upper()}] {data_content}"

        add_purchase(user_id, utr_found, data_content)

        try:
            group_map = {
                "gmail": GMAIL_GROUP_ID, "number": NUMBER_GROUP_ID, 
                "facebook": FB_GROUP_ID, "twitter": TWITTER_GROUP_ID, "instagram": INSTA_GROUP_ID
            }
            bot.delete_message(group_map[category], stock_item["msg_id"])
        except Exception:
            pass

        bot.send_message(user_id, f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n📦 **Data:**\n`{data_content}`", parse_mode="Markdown")
        send_log(f"🎉 **PURCHASE SUCCESS ({category.upper()})**\n🆔 User: `{user_id}`\n🆔 UTR: `{utr_found}`")

    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        bot.send_message(user_id, "⚠️ Error processing image!")

if __name__ == "__main__":
    notify_restart()
    print("Bot is Running with Permanent SQLite Database...")
    bot.infinity_polling()
