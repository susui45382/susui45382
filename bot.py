import telebot
from telebot import types
import requests
import re
import os
import json
from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631269601:AAH5keWN0qXjK60H8GTN5G-MLpqQTapxCuM"

# STOCK GROUPS / CHANNELS
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

DB_FILE = "user.json"

# PAYMENT CONFIG
EXPECTED_AMOUNT = "30"
UPI_ID = "paytm.s26tbd7@pty"
UPI_NAME = "Mr Subham"
QR_PINNED_MESSAGE_ID = 39
EXPECTED_NAME_KEYWORDS = ["DICTATOR", "MERCHANT", "SHOP", "SUBHAM"]

# =========================================================
# DATABASE LOAD & AUTO-SAVE BACKUP
# =========================================================

def load_database():
    """Bot start hone par user.json se backup restore karega"""
    default_db = {
        "used_utrs": [],
        "gmail_stock": [],
        "number_stock": [],
        "fb_stock": [],
        "twitter_stock": [],
        "insta_stock": [],
        "users": {},
        "user_purchases": {}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default_db:
                    if key not in data:
                        data[key] = default_db[key]
                return data
        except Exception as e:
            print(f"[DB LOAD ERROR]: {e}")
            return default_db
    return default_db

def save_database():
    """user.json file me background backup write/save karne ke liye"""
    db["used_utrs"] = list(used_utrs)
    db["gmail_stock"] = gmail_stock_list
    db["number_stock"] = number_stock_list
    db["fb_stock"] = fb_stock_list
    db["twitter_stock"] = twitter_stock_list
    db["insta_stock"] = insta_stock_list
    db["users"] = registered_users
    db["user_purchases"] = {str(k): v for k, v in user_purchases.items()}
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def save_user_info(user_obj):
    """User profile and real-time activity sync with user.json"""
    if not user_obj:
        return
        
    uid_str = str(user_obj.id)
    username = f"@{user_obj.username}" if user_obj.username else "No Username"
    first_name = user_obj.first_name if user_obj.first_name else "User"

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    if uid_str not in registered_users:
        registered_users[uid_str] = {
            "name": first_name,
            "username": username,
            "joined_date": current_date,
            "joined_time": current_time,
            "last_active_date": current_date,
            "last_active_time": current_time
        }
    else:
        registered_users[uid_str]["name"] = first_name
        registered_users[uid_str]["username"] = username
        registered_users[uid_str]["last_active_date"] = current_date
        registered_users[uid_str]["last_active_time"] = current_time

    # Automatic background backup write
    save_database()

# Database setup
db = load_database()
used_utrs = set(db.get("used_utrs", []))
gmail_stock_list = db.get("gmail_stock", [])
number_stock_list = db.get("number_stock", [])
fb_stock_list = db.get("fb_stock", [])
twitter_stock_list = db.get("twitter_stock", [])
insta_stock_list = db.get("insta_stock", [])
registered_users = db.get("users", {})
user_purchases = {int(k): v for k, v in db.get("user_purchases", {}).items()}

user_states = {}
temp_number_requests = {}

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# HELPER & LIVE LOG FUNCTIONS
# =========================================================

def record_purchase(user_id, utr, data_str):
    """Successful purchase record backup file me save karne ke liye"""
    if user_id not in user_purchases:
        user_purchases[user_id] = []
        
    now = datetime.now()
    user_purchases[user_id].append({
        "utr": utr,
        "data": data_str,
        "purchased_date": now.strftime("%Y-%m-%d"),
        "purchased_time": now.strftime("%H:%M:%S")
    })
    save_database()

def send_log(text):
    """ALERT CHANNEL PAR LIVE MSG BHEJNE KE LIYE"""
    try:
        bot.send_message(LOG_CHANNEL_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"[LOG ERROR]: {e}")

# =========================================================
# REAL-TIME ACTIVITY TRACKER (MIDDLEWARE)
# =========================================================

@bot.middleware_handler(update_types=['message', 'callback_query'])
def track_all_user_activities(bot_instance, update):
    """User ki har activity se user.json auto-backup rahega"""
    if update.message:
        save_user_info(update.message.from_user)
    elif update.callback_query:
        save_user_info(update.callback_query.from_user)

# =========================================================
# CHANNEL COMMANDS (/user & /broadcast)
# =========================================================

@bot.channel_post_handler(func=lambda message: message.chat.id == LOG_CHANNEL_ID)
def handle_channel_commands(message):
    text = message.text.strip() if message.text else ""

    if text.lower() == "/user":
        if not registered_users:
            bot.send_message(LOG_CHANNEL_ID, "📊 **Registered Users List:**\n\nKoi user registered nahi hai.", parse_mode="Markdown")
            return

        user_list_text = f"📊 **REGISTERED USERS LIST (Total: {len(registered_users)})**\n\n"
        for idx, (uid, uinfo) in enumerate(registered_users.items(), start=1):
            name = uinfo.get("name", "User")
            username = uinfo.get("username", "No Username")
            user_list_text += f"{idx}. {name} | {username} | `{uid}`\n"

        if len(user_list_text) > 4000:
            for x in range(0, len(user_list_text), 4000):
                bot.send_message(LOG_CHANNEL_ID, user_list_text[x:x+4000], parse_mode="Markdown")
        else:
            bot.send_message(LOG_CHANNEL_ID, user_list_text, parse_mode="Markdown")
        return

    if text.lower().startswith("/broadcast"):
        broadcast_msg = text[10:].strip()
        if not broadcast_msg:
            bot.send_message(LOG_CHANNEL_ID, "⚠️ **Format:** `/broadcast Aapka Message Yaha`", parse_mode="Markdown")
            return

        if not registered_users:
            bot.send_message(LOG_CHANNEL_ID, "❌ Broadcast karne ke liye koi registered user nahi mila.", parse_mode="Markdown")
            return

        success_count = 0
        failed_count = 0

        for uid in registered_users.keys():
            try:
                bot.send_message(int(uid), broadcast_msg, parse_mode="Markdown")
                success_count += 1
            except Exception:
                failed_count += 1

        bot.send_message(
            LOG_CHANNEL_ID, 
            f"✅ **Broadcast Completed!**\n\n📤 **Sent:** `{success_count}` Users\n❌ **Failed/Blocked:** `{failed_count}` Users", 
            parse_mode="Markdown"
        )
        return

# =========================================================
# MAIN MENU
# =========================================================

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

# =========================================================
# START COMMAND
# =========================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.chat.id] = None
    save_user_info(message.from_user)

    welcome_text = (
        f"👋 Welcome **{message.from_user.first_name}**!\n\n"
        "📧 **Gmail Store & OTP Number Bot** me aapka swagat hai."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    
    # LIVE ALERT TO CHANNEL
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    user_id = message.chat.id
    
    send_log(
        f"🚀 **Bot Started**\n\n"
        f"👤 **Name:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`"
    )

# =========================================================
# ADMIN STATUS COMMAND
# =========================================================

@bot.message_handler(commands=['botstatus'])
def check_bot_status(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    
    bot.send_message(
        message.chat.id, 
        f"📊 **BOT STATUS**\n\n👥 **Total Users:** `{len(registered_users)}`", 
        parse_mode="Markdown"
    )

# =========================================================
# STOCK CAPTURE HANDLERS (LOG + JSON BACKUP)
# =========================================================

@bot.message_handler(func=lambda message: message.chat.id == GMAIL_GROUP_ID, content_types=['text'])
def capture_gmail_stock(message):
    text_content = message.text.strip()
    gmail_stock_list.append({"msg_id": message.message_id, "text": text_content})
    save_database()
    
    send_log(
        f"📦 **New Stock Added (📧 Gmail Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Gmail Stock Available:** {len(gmail_stock_list)}"
    )

@bot.message_handler(func=lambda message: message.chat.id == NUMBER_GROUP_ID, content_types=['text'])
def capture_number_stock(message):
    text_content = message.text.strip()
    number_stock_list.append({"msg_id": message.message_id, "text": text_content})
    save_database()
    
    send_log(
        f"📦 **New Stock Added (📞 Number Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Number Stock Available:** {len(number_stock_list)}"
    )

@bot.message_handler(func=lambda message: message.chat.id == FB_GROUP_ID, content_types=['text'])
def capture_fb_stock(message):
    text_content = message.text.strip()
    fb_stock_list.append({"msg_id": message.message_id, "text": text_content})
    save_database()
    
    send_log(
        f"📦 **New Stock Added (👥 Facebook Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Facebook Stock Available:** {len(fb_stock_list)}"
    )

@bot.message_handler(func=lambda message: message.chat.id == TWITTER_GROUP_ID, content_types=['text'])
def capture_twitter_stock(message):
    text_content = message.text.strip()
    twitter_stock_list.append({"msg_id": message.message_id, "text": text_content})
    save_database()
    
    send_log(
        f"📦 **New Stock Added (🐦 Twitter Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Twitter Stock Available:** {len(twitter_stock_list)}"
    )

@bot.message_handler(func=lambda message: message.chat.id == INSTA_GROUP_ID, content_types=['text'])
def capture_insta_stock(message):
    text_content = message.text.strip()
    insta_stock_list.append({"msg_id": message.message_id, "text": text_content})
    save_database()
    
    send_log(
        f"📦 **New Stock Added (📸 Instagram Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Instagram Stock Available:** {len(insta_stock_list)}"
    )

# =========================================================
# ADMIN COMMAND: /sendotp username OTP
# =========================================================

@bot.message_handler(commands=['sendotp'])
def admin_send_otp(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Format galat hai!\nSahi tarika: `/sendotp username 574375`", parse_mode="Markdown")
        return
    
    target_username = parts[1].replace("@", "").strip().lower()
    otp_code = parts[2].strip()
    
    found_chat_id = None
    for uid_str, uinfo in registered_users.items():
        if uinfo.get("username", "").replace("@", "").lower() == target_username:
            found_chat_id = int(uid_str)
            break
            
    if found_chat_id:
        try:
            bot.send_message(
                found_chat_id,
                f"🚨 **YOUR OTP CODE RECEIVED!**\n\n🔑 **OTP:** `{otp_code}`\n\n*Apke number par OTP aa chuka hai, usey use karein.*",
                parse_mode="Markdown"
            )
            bot.send_message(message.chat.id, f"✅ OTP successfully `@{target_username}` ke paas bhej diya gaya hai!")
            send_log(f"📤 **OTP Sent by Admin**\n\n👤 **To Username:** `@{target_username}`\n🔑 **OTP:** `{otp_code}`")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ User ko message bhejne me error aayi: {e}")
    else:
        bot.send_message(message.chat.id, f"❌ Is username (`@{target_username}`) ka koi active user bot database me nahi mila.")

# =========================================================
# MAIN MENU TEXT HANDLER
# =========================================================

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_menu(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

    save_user_info(message.from_user)

    if message.text == "📧 Sell Gmail":
        user_states[user_id] = "AWAITING_SELL_GMAIL"
        sell_text = (
            "📧 **SELL YOUR GMAIL ACCOUNT**\n\n"
            "Kripya apna Gmail ID aur Password is format me bhejein:\n"
            "`example@gmail.com : password123`\n\n"
            "📌 *Note: Aapka message direct admin ke DM me chala jayega.*"
        )
        bot.send_message(user_id, sell_text, parse_mode="Markdown")

    elif message.text == "📞 Buy Number":
        if len(number_stock_list) == 0:
            bot.send_message(user_id, "❌ **Number Out of Stock!**\n\nFilhal koi number available nahi hai.", parse_mode="Markdown")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_wa = types.InlineKeyboardButton("💬 WhatsApp (₹30)", callback_data="pay_num_whatsapp")
        btn_tg = types.InlineKeyboardButton("📱 Telegram (₹30)", callback_data="pay_num_telegram")
        btn_fb = types.InlineKeyboardButton("👥 Facebook (₹30)", callback_data="pay_num_facebook")
        btn_ig = types.InlineKeyboardButton("📸 Instagram (₹30)", callback_data="pay_num_instagram")
        markup.add(btn_wa, btn_tg, btn_fb, btn_ig)

        bot.send_message(
            user_id,
            "📞 **SELECT SERVICE FOR OTP NUMBER**\n\n"
            f"💵 **Price:** ₹{EXPECTED_AMOUNT} per Number\n"
            f"📦 **Available Number Stock:** {len(number_stock_list)}\n\n"
            "Kripya niche diye gaye buttons me se select karein ki aapko kis app ke liye number chahiye:",
            reply_markup=markup
        )

    elif message.text == "🛒 Buy Gmail":
        if len(gmail_stock_list) == 0:
            bot.send_message(user_id, "❌ **Gmail Out of Stock!**\n\nFilhal koi Gmail available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Auto-Verify", callback_data="show_qr_gmail")
        inline_kb.add(btn_pay)

        buy_text = (
            "🛒 **Buy Fresh Gmail Account**\n\n"
            f"💵 **Price:** ₹{EXPECTED_AMOUNT} per Gmail\n"
            f"📦 **Available Stock:** {len(gmail_stock_list)}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "👥 Buy Facebook":
        if len(fb_stock_list) == 0:
            bot.send_message(user_id, "❌ **Facebook Out of Stock!**\n\nFilhal koi Facebook Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Auto-Verify", callback_data="show_qr_fb")
        inline_kb.add(btn_pay)

        buy_text = (
            "👥 **Buy Facebook Account**\n\n"
            f"💵 **Price:** ₹{EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {len(fb_stock_list)}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "🐦 Buy Twitter":
        if len(twitter_stock_list) == 0:
            bot.send_message(user_id, "❌ **Twitter Out of Stock!**\n\nFilhal koi Twitter Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Auto-Verify", callback_data="show_qr_twitter")
        inline_kb.add(btn_pay)

        buy_text = (
            "🐦 **Buy Twitter Account**\n\n"
            f"💵 **Price:** ₹{EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {len(twitter_stock_list)}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "📸 Buy Instagram":
        if len(insta_stock_list) == 0:
            bot.send_message(user_id, "❌ **Instagram Out of Stock!**\n\nFilhal koi Instagram Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Auto-Verify", callback_data="show_qr_insta")
        inline_kb.add(btn_pay)

        buy_text = (
            "📸 **Buy Instagram Account**\n\n"
            f"💵 **Price:** ₹{EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {len(insta_stock_list)}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "👤 Profile":
        total_bought = len(user_purchases.get(user_id, []))
        profile_text = (
            "👤 **YOUR PROFILE DETAILS**\n\n"
            f"📛 **Name:** {name}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🌐 **Username:** {username}\n"
            f"🛍️ **Total Bought:** `{total_bought}`\n"
            f"⚡ **Account Status:** Active ✅"
        )
        bot.send_message(user_id, profile_text, parse_mode="Markdown")

    elif message.text == "🆘 Support":
        support_kb = types.InlineKeyboardMarkup()
        btn_admin = types.InlineKeyboardButton("💬 Contact Support Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")
        support_kb.add(btn_admin)
        support_text = (
            "🆘 **CUSTOMER SUPPORT HUB**\n\n"
            "Kya aapko koi dikkat ya issue aa raha hai?\n"
            "Aap humare support team se direct baat kar sakte hain."
        )
        bot.send_message(user_id, support_text, parse_mode="Markdown", reply_markup=support_kb)

    elif message.text == "📑 My Submitted":
        purchases = user_purchases.get(user_id, [])
        if not purchases:
            bot.send_message(user_id, "📑 **MY PURCHASED HISTORY**\n\n❌ Aapne abhi tak koi item buy nahi kiya hai.", parse_mode="Markdown")
            return

        history_text = "📑 **YOUR PURCHASE HISTORY:**\n\n"
        for idx, item in enumerate(purchases, start=1):
            history_text += f"{idx}. **UTR:** `{item['utr']}`\n   **Data:** `{item['data']}`\n\n"
        bot.send_message(user_id, history_text, parse_mode="Markdown")

    else:
        if user_states.get(user_id) == "AWAITING_SELL_GMAIL":
            user_states[user_id] = None
            user_link = f"tg://user?id={user_id}"
            admin_msg = (
                "📩 **NEW GMAIL SUBMITTED TO SELL!**\n\n"
                f"👤 **Seller Name:** [{name}]({user_link})\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`\n\n"
                f"📝 **Gmail Details:**\n`{message.text}`"
            )
            try:
                bot.send_message(ADMIN_USER_ID, admin_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"[ADMIN DM ERROR]: {e}")

            bot.send_message(user_id, "✅ **Aapki Details Admin ko Bhej Di Gayi Hain!**", parse_mode="Markdown")

# =========================================================
# INLINE BUTTON HANDLERS (LOG + JSON BACKUP)
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.message.chat.id
    name = call.from_user.first_name
    username = f"@{call.from_user.username}" if call.from_user.username else "No Username"

    save_user_info(call.from_user)

    if call.data.startswith("pay_num_"):
        if len(number_stock_list) == 0:
            bot.answer_callback_query(call.id, "❌ Number Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal numbers available nahi hain.", parse_mode="Markdown")
            return

        service = call.data.split("_")[2]
        temp_number_requests[user_id] = {"service": service} 
        
        try:
            user_states[user_id] = "AWAITING_NUMBER_PAYMENT_PROOF"
            bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)

            payment_text = (
                f"💳 **Payment for {service.upper()} Number**\n\n"
                f"💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
                f"👤 **UPI Name:** `{UPI_NAME}`\n"
                f"📌 **UPI ID:** `{UPI_ID}`\n\n"
                f"📲 Upar diye gaye QR Code ko scan karke ₹{EXPECTED_AMOUNT} payment karein aur **payment screenshot yahin bhejein.**"
            )
            bot.send_message(user_id, payment_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id, f"✅ Selected: {service.upper()} Number")

            # LIVE CHANNEL ALERT
            send_log(
                f"📲 **QR Sent For Number ({service.upper()})**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"💵 **Expected Amount:** ₹{EXPECTED_AMOUNT}"
            )
        except Exception as e:
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "❌ QR send nahi ho paya!", show_alert=True)

    elif call.data == "show_qr_gmail":
        if len(gmail_stock_list) == 0:
            bot.answer_callback_query(call.id, "❌ Gmail Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Gmail available nahi hai.", parse_mode="Markdown")
            return

        try:
            user_states[user_id] = "AWAITING_PAYMENT_PROOF"
            bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)

            payment_text = (
                f"💳 **Payment for Gmail**\n\n"
                f"💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
                f"👤 **UPI Name:** `{UPI_NAME}`\n"
                f"📌 **UPI ID:** `{UPI_ID}`\n\n"
                f"📲 Upar diye gaye QR Code ko scan karke ₹{EXPECTED_AMOUNT} payment karein aur screenshot yahan bhejein."
            )
            bot.send_message(user_id, payment_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ QR Code sent!")

            # LIVE CHANNEL ALERT
            send_log(
                f"📲 **QR Sent To User (Gmail)**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`"
            )
        except Exception as e:
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "❌ QR send nahi ho paya!", show_alert=True)

    elif call.data == "show_qr_fb":
        if len(fb_stock_list) == 0:
            bot.answer_callback_query(call.id, "❌ Facebook Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Facebook available nahi hai.", parse_mode="Markdown")
            return

        try:
            user_states[user_id] = "AWAITING_FB_PAYMENT_PROOF"
            bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)

            payment_text = (
                f"💳 **Payment for Facebook Account**\n\n"
                f"💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
                f"👤 **UPI Name:** `{UPI_NAME}`\n"
                f"📌 **UPI ID:** `{UPI_ID}`\n\n"
                f"📲 Upar diye gaye QR Code ko scan karke ₹{EXPECTED_AMOUNT} payment karein aur screenshot yahan bhejein."
            )
            bot.send_message(user_id, payment_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ QR Code sent!")

            # LIVE CHANNEL ALERT
            send_log(
                f"📲 **QR Sent To User (Facebook)**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`"
            )
        except Exception as e:
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "❌ QR send nahi ho paya!", show_alert=True)

    elif call.data == "show_qr_twitter":
        if len(twitter_stock_list) == 0:
            bot.answer_callback_query(call.id, "❌ Twitter Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Twitter available nahi hai.", parse_mode="Markdown")
            return

        try:
            user_states[user_id] = "AWAITING_TWITTER_PAYMENT_PROOF"
            bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)

            payment_text = (
                f"💳 **Payment for Twitter Account**\n\n"
                f"💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
                f"👤 **UPI Name:** `{UPI_NAME}`\n"
                f"📌 **UPI ID:** `{UPI_ID}`\n\n"
                f"📲 Upar diye gaye QR Code ko scan karke ₹{EXPECTED_AMOUNT} payment karein aur screenshot yahan bhejein."
            )
            bot.send_message(user_id, payment_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ QR Code sent!")

            # LIVE CHANNEL ALERT
            send_log(
                f"📲 **QR Sent To User (Twitter)**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`"
            )
        except Exception as e:
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "❌ QR send nahi ho paya!", show_alert=True)

    elif call.data == "show_qr_insta":
        if len(insta_stock_list) == 0:
            bot.answer_callback_query(call.id, "❌ Instagram Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Instagram available nahi hai.", parse_mode="Markdown")
            return

        try:
            user_states[user_id] = "AWAITING_INSTA_PAYMENT_PROOF"
            bot.copy_message(chat_id=user_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)

            payment_text = (
                f"💳 **Payment for Instagram Account**\n\n"
                f"💰 **Amount:** ₹{EXPECTED_AMOUNT}\n"
                f"👤 **UPI Name:** `{UPI_NAME}`\n"
                f"📌 **UPI ID:** `{UPI_ID}`\n\n"
                f"📲 Upar diye gaye QR Code ko scan karke ₹{EXPECTED_AMOUNT} payment karein aur screenshot yahan bhejein."
            )
            bot.send_message(user_id, payment_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ QR Code sent!")

            # LIVE CHANNEL ALERT
            send_log(
                f"📲 **QR Sent To User (Instagram)**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`"
            )
        except Exception as e:
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "❌ QR send nahi ho paya!", show_alert=True)

# =========================================================
# CLOUD OCR ENGINE
# =========================================================

def ocr_space_file(filename, api_key):
    url = "https://api.ocr.space/parse/image"
    with open(filename, "rb") as f:
        response = requests.post(
            url,
            files={"file": f},
            data={"apikey": api_key, "language": "eng", "OCREngine": "2"},
            timeout=60
        )
    result = response.json()
    if result.get("IsErroredOnProcessing") == False:
        parsed_results = result.get("ParsedResults")
        if parsed_results:
            return parsed_results[0].get("ParsedText", "")
    return ""

# =========================================================
# PAYMENT SCREENSHOT HANDLER (CHANNEL LOG + BACKUP)
# =========================================================

@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    current_state = user_states.get(user_id)

    save_user_info(message.from_user)

    valid_states = [
        "AWAITING_PAYMENT_PROOF", 
        "AWAITING_NUMBER_PAYMENT_PROOF", 
        "AWAITING_FB_PAYMENT_PROOF", 
        "AWAITING_TWITTER_PAYMENT_PROOF",
        "AWAITING_INSTA_PAYMENT_PROOF"
    ]
    if current_state not in valid_states:
        return

    # LIVE CHANNEL ALERT
    send_log(f"📸 **Screenshot Received**\n\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`")
    bot.send_message(user_id, "🔍 **Analyzing Screenshot via Cloud OCR...**\n\nKripya wait karein.", parse_mode="Markdown")

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

        if not utr_found:
            user_states[user_id] = None
            bot.send_message(user_id, "❌ **Verification Failed!**\n\nScreenshot me UTR Number nahi mila.", parse_mode="Markdown")
            send_log(f"⚠️ **OCR Failed:** UTR Not Found\n\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`")
            return

        if utr_found in used_utrs:
            user_states[user_id] = None
            bot.send_message(user_id, f"❌ **Duplicate UTR!**\n\nUTR `{utr_found}` pehle use ho chuka hai.", parse_mode="Markdown")
            send_log(f"🚨 **Duplicate UTR Attempt!**\n\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\n🆔 **UTR:** `{utr_found}`")
            return

        if not amount_verified or not name_verified:
            user_states[user_id] = None
            bot.send_message(user_id, "❌ **Amount ya UPI Name Mismatch!**\n\nSahi payment screenshot bhejein.", parse_mode="Markdown")
            send_log(f"❌ **Payment Mismatch!**\n\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\nAmount Verified: {amount_verified}\nName Verified: {name_verified}\nUTR Found: `{utr_found}`")
            return

        used_utrs.add(utr_found)
        user_states[user_id] = None

        if current_state == "AWAITING_PAYMENT_PROOF":
            if len(gmail_stock_list) == 0:
                bot.send_message(user_id, "❌ **Gmail Stock khatam ho gaya hai!** Admin se contact karein.")
                send_log(f"⚠️ **Delivery Failed (Gmail):** Out of Stock\n👤 **Name:** {name}\n🆔 **UTR:** `{utr_found}`")
                return

            stock_item = gmail_stock_list.pop(0)
            account_data = stock_item["text"]
            msg_id_to_delete = stock_item["msg_id"]

            try:
                bot.delete_message(GMAIL_GROUP_ID, msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR GMAIL] {e}")

            record_purchase(user_id, utr_found, account_data)

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n📧 **Gmail Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
            # LIVE CHANNEL ALERT
            send_log(f"🎉 **NEW SUCCESSFUL GMAIL PURCHASE!**\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\n🆔 **UTR:** `{utr_found}`\n📧 **Data:** `{account_data}`")

        elif current_state == "AWAITING_NUMBER_PAYMENT_PROOF":
            req_info = temp_number_requests.get(user_id, {})
            service = req_info.get("service", "number")
            
            if len(number_stock_list) == 0:
                bot.send_message(user_id, "❌ **Number Stock khatam ho gaya hai!** Admin se contact karein.")
                send_log(f"🚨 **Number Stock Empty after Payment!**\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **UTR:** `{utr_found}`")
                return

            stock_item = number_stock_list.pop(0)
            number_data = stock_item["text"]
            msg_id_to_delete = stock_item["msg_id"]

            try:
                bot.delete_message(NUMBER_GROUP_ID, msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR NUMBER] {e}")

            record_purchase(user_id, utr_found, f"[{service.upper()}] {number_data}")

            bot.send_message(
                user_id,
                f"🎉 **Payment Verified & Number Allotted!**\n\n"
                f"📱 **Service:** `{service.upper()}`\n"
                f"📞 **Phone Number:** `{number_data}`\n"
                f"🆔 **UTR:** `{utr_found}`\n\n"
                "⏳ *OTP ka wait karein. Jaise hi OTP aayega, bot aapko yahin bhej dega.*",
                parse_mode="Markdown"
            )

            # LIVE CHANNEL ALERT
            send_log(
                f"🎉 **NEW SUCCESSFUL NUMBER PURCHASE!**\n\n"
                f"👤 **Name:** {name}\n"
                f"🌐 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"📱 **Service:** `{service.upper()}`\n"
                f"📞 **Number Given:** `{number_data}`\n"
                f"🆔 **UTR:** `{utr_found}`"
            )

        elif current_state == "AWAITING_FB_PAYMENT_PROOF":
            if len(fb_stock_list) == 0:
                bot.send_message(user_id, "❌ **Facebook Stock khatam ho gaya hai!** Admin se contact karein.")
                send_log(f"⚠️ **Delivery Failed (Facebook):** Out of Stock\n👤 **Name:** {name}\n🆔 **UTR:** `{utr_found}`")
                return

            stock_item = fb_stock_list.pop(0)
            account_data = stock_item["text"]
            msg_id_to_delete = stock_item["msg_id"]

            try:
                bot.delete_message(FB_GROUP_ID, msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR FB] {e}")

            record_purchase(user_id, utr_found, account_data)

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n👥 **Facebook Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
            # LIVE CHANNEL ALERT
            send_log(f"🎉 **NEW SUCCESSFUL FACEBOOK PURCHASE!**\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\n🆔 **UTR:** `{utr_found}`\n👥 **Data:** `{account_data}`")

        elif current_state == "AWAITING_TWITTER_PAYMENT_PROOF":
            if len(twitter_stock_list) == 0:
                bot.send_message(user_id, "❌ **Twitter Stock khatam ho gaya hai!** Admin se contact karein.")
                send_log(f"⚠️ **Delivery Failed (Twitter):** Out of Stock\n👤 **Name:** {name}\n🆔 **UTR:** `{utr_found}`")
                return

            stock_item = twitter_stock_list.pop(0)
            account_data = stock_item["text"]
            msg_id_to_delete = stock_item["msg_id"]

            try:
                bot.delete_message(TWITTER_GROUP_ID, msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR TWITTER] {e}")

            record_purchase(user_id, utr_found, account_data)

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n🐦 **Twitter Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
            # LIVE CHANNEL ALERT
            send_log(f"🎉 **NEW SUCCESSFUL TWITTER PURCHASE!**\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\n🆔 **UTR:** `{utr_found}`\n🐦 **Data:** `{account_data}`")

        elif current_state == "AWAITING_INSTA_PAYMENT_PROOF":
            if len(insta_stock_list) == 0:
                bot.send_message(user_id, "❌ **Instagram Stock khatam ho gaya hai!** Admin se contact karein.")
                send_log(f"⚠️ **Delivery Failed (Instagram):** Out of Stock\n👤 **Name:** {name}\n🆔 **UTR:** `{utr_found}`")
                return

            stock_item = insta_stock_list.pop(0)
            account_data = stock_item["text"]
            msg_id_to_delete = stock_item["msg_id"]

            try:
                bot.delete_message(INSTA_GROUP_ID, msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR INSTA] {e}")

            record_purchase(user_id, utr_found, account_data)

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n📸 **Instagram Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
            # LIVE CHANNEL ALERT
            send_log(f"🎉 **NEW SUCCESSFUL INSTAGRAM PURCHASE!**\n👤 **Name:** {name}\n🌐 **Username:** {username}\n🆔 **User ID:** `{user_id}`\n🆔 **UTR:** `{utr_found}`\n📸 **Data:** `{account_data}`")

    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        bot.send_message(user_id, "⚠️ **Error processing image!**\n\nPlease screenshot dobara bhejein.", parse_mode="Markdown")
        send_log(f"⚠️ **System Exception Error (Payment):** {e}\n👤 **Name:** {name}")

# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    print("Bot Running with Dual Sync (Live Log Channel + Silent user.json Backup)...")
    bot.infinity_polling()
