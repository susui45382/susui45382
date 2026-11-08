import telebot
from telebot import types, apihelper
import re
import os
import urllib.parse
import uuid
from datetime import datetime
from pymongo import MongoClient

# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631269601:AAEoNW4k1Xqmzvz5Ww4dIUtMrGTv3IEQYAc"

# MONGODB CONNECTION STRING (Successfully Configured)
MONGO_URI = "mongodb+srv://botuser:Tsv3rQQQ-g4jAY3@cluster0.fe1k9gv.mongodb.net/?appName=Cluster0"

# STOCK GROUPS / CHANNELS
GMAIL_GROUP_ID = -1004388026969
NUMBER_GROUP_ID = -1004418431812
FB_GROUP_ID = -1003966946655
TWITTER_GROUP_ID = -1003851497827
INSTA_GROUP_ID = -1003988074533
WA_ACC_GROUP_ID = -1004370815511  # Dynamic stock mapping
TG_ACC_GROUP_ID = -1004443734529  # Dynamic stock mapping

# ALERT / LOG / BROADCAST CHANNEL
RAW_CHANNEL_ID = "4418224009"

if not str(RAW_CHANNEL_ID).startswith("-100"):
    LOG_CHANNEL_ID = int(f"-100{RAW_CHANNEL_ID.replace('-', '')}")
else:
    LOG_CHANNEL_ID = int(RAW_CHANNEL_ID)

ADMIN_USER_ID = 6403557650
ADMIN_USERNAME = "BhaiCharaYT"

# PAYMENT CONFIG
DEFAULT_EXPECTED_AMOUNT = "30"  # Base price
ACCOUNT_EXPECTED_AMOUNT = "99"  # Price for WA and TG Accounts
UPI_ID = "paytm.s26tbd7@pty"
UPI_NAME = "Mr Subham"

# =========================================================
# MONGODB CLOUD STORAGE SYSTEM (PERMANENT NO-LOSS DB)
# =========================================================

client = MongoClient(MONGO_URI)
db = client["telegram_store_bot"]

col_users = db["users"]
col_stocks = db["stocks"]
col_utrs = db["used_utrs"]
col_purchases = db["purchases"]
col_pending_payments = db["pending_payments"]

# Dynamic runtime states
user_states = {}
temp_number_requests = {}
user_payment_amounts = {}

def get_dynamic_qr_url(upi_id, name, amount, note="Store Payment"):
    """Generates Price-Locked QR Code URL via API"""
    encoded_name = urllib.parse.quote(name)
    encoded_note = urllib.parse.quote(note)
    
    upi_url = f"upi://pay?pa={upi_id}&pn={encoded_name}&am={amount}&cu=INR&tn={encoded_note}"
    encoded_upi_url = urllib.parse.quote(upi_url)
    
    qr_code_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_upi_url}"
    return qr_code_image_url

def save_user_info(user_obj):
    """User profile metadata ko MongoDB me permanently store karta hai"""
    if not user_obj:
        return
        
    uid_str = str(user_obj.id)
    username = f"@{user_obj.username}" if user_obj.username else "Unknown"
    first_name = user_obj.first_name if user_obj.first_name else "User"

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    col_users.update_one(
        {"_id": uid_str},
        {
            "$set": {
                "name": first_name,
                "username": username,
                "last_active_date": current_date,
                "last_active_time": current_time
            },
            "$setOnInsert": {
                "joined_date": current_date,
                "joined_time": current_time
            }
        },
        upsert=True
    )

def record_purchase(user_id, utr, data_str):
    """Purchase Order Database me save karta hai"""
    now = datetime.now()
    col_purchases.insert_one({
        "user_id": str(user_id),
        "utr": utr,
        "data": data_str,
        "purchased_date": now.strftime("%Y-%m-%d"),
        "purchased_time": now.strftime("%H:%M:%S")
    })

def add_stock_item(category, msg_id, text_content):
    """Channel se aaye dynamic stock ko MongoDB me add karta hai"""
    col_stocks.insert_one({
        "category": category,
        "msg_id": msg_id,
        "text": text_content,
        "added_at": datetime.now()
    })

def get_and_pop_stock(category):
    """FIFO Basis par stock fetch karke MongoDB se pop karta hai"""
    stock_item = col_stocks.find_one_and_delete({"category": category})
    return stock_item

def get_stock_count(category):
    """Stock count fetch karne ke liye"""
    return col_stocks.count_documents({"category": category})

# ENABLE MIDDLEWARE BEFORE INITIALIZING TELEBOT
apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# HELPER & LIVE LOG FUNCTIONS
# =========================================================

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
    """User active hote hi MongoDB update ho jayega"""
    if hasattr(update, 'from_user') and update.from_user:
        save_user_info(update.from_user)

# =========================================================
# MAIN MENU
# =========================================================

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        "🛒 Buy Account",
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
        "📧 **Store & OTP Service Bot** me aapka swagat hai."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Unknown"
    user_id = message.chat.id
    
    send_log(
        f"🚀 **Bot Started**\n\n"
        f"👤 **Name:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`"
    )

# =========================================================
# ADMIN COMMANDS (BOT PRIVATE CHAT)
# =========================================================

@bot.message_handler(commands=['botstatus'])
def check_bot_status(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    
    bot.send_message(
        message.chat.id, 
        f"📊 **BOT STATUS (MONGODB CLOUD)**\n\n"
        f"👥 **Total Users:** `{col_users.count_documents({})}` \n"
        f"📧 **Gmail Stock:** `{get_stock_count('gmail')}` \n"
        f"📞 **Number Stock:** `{get_stock_count('number')}` \n"
        f"💬 **WA Account Stock:** `{get_stock_count('wa_account')}` \n"
        f"📱 **TG Account Stock:** `{get_stock_count('tg_account')}` \n"
        f"👥 **FB Stock:** `{get_stock_count('facebook')}` \n"
        f"🐦 **Twitter Stock:** `{get_stock_count('twitter')}` \n"
        f"📸 **Insta Stock:** `{get_stock_count('instagram')}`", 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['user'])
def admin_get_users(message):
    if message.chat.id != ADMIN_USER_ID:
        return

    try:
        users_list = list(
            col_users.find(
                {},
                {
                    "_id": 1,
                    "username": 1,
                    "joined_date": 1,
                    "joined_time": 1
                }
            ).sort("_id", 1)
        )

        if not users_list:
            bot.send_message(message.chat.id, "📊 REGISTERED USERS LIST\n\n❌ Abhi koi registered user nahi mila.")
            return

        total_users = len(users_list)
        header = f"📊 REGISTERED USERS LIST\n\n👥 Total Users: {total_users}\n\n"
        current_text = header
        part_number = 1

        for index, user in enumerate(users_list, start=1):
            user_id = str(user.get("_id", "")).strip()
            username = str(user.get("username", "Unknown")).strip()

            if not username or username.lower() in ["no username", "none", "null", "no_username"]:
                username = "Unknown"

            if username == "Unknown":
                user_line = f"{index}. 🆔 {user_id} (No Username)\n"
            else:
                if not username.startswith("@"):
                    username = "@" + username
                user_line = f"{index}. 👤 {username}\n   🆔 {user_id}\n"

            if len(current_text) + len(user_line) > 3500:
                bot.send_message(message.chat.id, current_text)
                part_number += 1
                current_text = f"📊 REGISTERED USERS LIST (Part {part_number})\n\n"

            current_text += user_line + "\n"

        if current_text.strip():
            bot.send_message(message.chat.id, current_text)

    except Exception as e:
        print(f"[USER LIST ERROR]: {e}")
        bot.send_message(message.chat.id, f"❌ User list load karte waqt error aayi.\n\nError: {str(e)[:500]}")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.chat.id != ADMIN_USER_ID:
        return

    text = message.text.strip()
    broadcast_msg = text[10:].strip()
    if not broadcast_msg:
        bot.send_message(message.chat.id, "⚠️ **Format:** `/broadcast Aapka Message Yaha`", parse_mode="Markdown")
        return

    users_list = list(col_users.find({}))
    if not users_list:
        bot.send_message(message.chat.id, "❌ Broadcast karne ke liye koi registered user nahi mila.", parse_mode="Markdown")
        return

    success_count = 0
    failed_count = 0

    for uinfo in users_list:
        try:
            bot.send_message(int(uinfo["_id"]), broadcast_msg, parse_mode="Markdown")
            success_count += 1
        except Exception:
            failed_count += 1

    bot.send_message(
        message.chat.id, 
        f"✅ **Broadcast Completed!**\n\n📤 **Sent:** `{success_count}` Users\n❌ **Failed/Blocked:** `{failed_count}` Users", 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['sendotp'])
def admin_send_otp(message):
    if message.chat.id != ADMIN_USER_ID:
        return

    raw_text = message.text.strip()
    parts = raw_text.split(None, 2)

    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Format galat hai!\nSahi tarika: `/sendotp @username 574375`", parse_mode="Markdown")
        return

    target_username = parts[1].replace("@", "").strip()
    otp_code = parts[2].strip()

    uinfo = col_users.find_one({"username": {"$regex": f"^@?{re.escape(target_username)}$", "$options": "i"}})

    if uinfo:
        try:
            bot.send_message(
                int(uinfo["_id"]),
                f"🚨 **YOUR MESSAGE / OTP RECEIVED!**\n\n🔑 **Content:** `{otp_code}`\n\n*Apke paas update aa chuka hai, usey check karein.*",
                parse_mode="Markdown"
            )
            bot.send_message(message.chat.id, f"✅ Successfully `@{target_username}` ke paas bhej diya gaya hai!")
            send_log(f"📤 **Message Sent by Admin**\n\n👤 **To Username:** `@{target_username}`\n🔑 **Content:** `{otp_code}`")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ User ko message bhejne me error aayi: {e}")
    else:
        bot.send_message(message.chat.id, f"❌ Is username (`@{target_username}`) ka koi active user bot database me nahi mila.")

# =========================================================
# STOCK CAPTURE HANDLERS (SAVED DIRECT TO MONGODB)
# =========================================================

@bot.message_handler(func=lambda message: message.chat.id == GMAIL_GROUP_ID, content_types=['text'])
def capture_gmail_stock(message):
    text_content = message.text.strip()
    add_stock_item("gmail", message.message_id, text_content)
    send_log(f"📦 **New Stock Added (📧 Gmail Stock)**\n\n🆔 **Msg ID:** `{message.message_id}`\n📝 **Data:** `{text_content}`\n📊 **Total Gmail Stock:** {get_stock_count('gmail')}")

@bot.message_handler(func=lambda message: message.chat.id == NUMBER_GROUP_ID, content_types=['text'])
def capture_number_stock(message):
    text_content = message.text.strip()
    add_stock_item("number", message.message_id, text_content)
    send_log(f"📦 **New Stock Added (📞 Number Stock)**\n\n🆔 **Msg ID:** `{message.message_id}`\n📝 **Data:** `{text_content}`\n📊 **Total Number Stock:** {get_stock_count('number')}")

@bot.message_handler(func=lambda message: message.chat.id == FB_GROUP_ID, content_types=['text'])
def capture_fb_stock(message):
    text_content = message.text.strip()
    add_stock_item("facebook", message.message_id, text_content)
    send_log(f"📦 **New Stock Added (👥 Facebook Stock)**\n\n🆔 **Msg ID:** `{message.message_id}`\n📝 **Data:** `{text_content}`\n📊 **Total FB Stock:** {get_stock_count('facebook')}")

@bot.message_handler(func=lambda message: message.chat.id == TWITTER_GROUP_ID, content_types=['text'])
def capture_twitter_stock(message):
    text_content = message.text.strip()
    add_stock_item("twitter", message.message_id, text_content)
    send_log(f"📦 **New Stock Added (🐦 Twitter Stock)**\n\n🆔 **Msg ID:** `{message.message_id}`\n📝 **Data:** `{text_content}`\n📊 **Total Twitter Stock:** {get_stock_count('twitter')}")

@bot.message_handler(func=lambda message: message.chat.id == INSTA_GROUP_ID, content_types=['text'])
def capture_insta_stock(message):
    text_content = message.text.strip()
    add_stock_item("instagram", message.message_id, text_content)
    send_log(f"📦 **New Stock Added (📸 Instagram Stock)**\n\n🆔 **Msg ID:** `{message.message_id}`\n📝 **Data:** `{text_content}`\n📊 **Total Insta Stock:** {get_stock_count('instagram')}")

# =========================================================
# MAIN MENU TEXT HANDLER
# =========================================================

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_menu(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Unknown"

    save_user_info(message.from_user)

    # CHECK IF USER IS SUBMITTING PAYMENT PROOF (UTR or Screenshot)
    current_state = user_states.get(user_id)
    if current_state in [
        "AWAITING_PAYMENT_PROOF", 
        "AWAITING_NUMBER_PAYMENT_PROOF", 
        "AWAITING_FB_PAYMENT_PROOF", 
        "AWAITING_TWITTER_PAYMENT_PROOF", 
        "AWAITING_INSTA_PAYMENT_PROOF", 
        "AWAITING_WA_ACC_PAYMENT_PROOF", 
        "AWAITING_TG_ACC_PAYMENT_PROOF"
    ]:
        handle_manual_payment_proof(message)
        return

    if message.content_type != 'text':
        return

    if message.text == "🛒 Buy Account":
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_wa = types.InlineKeyboardButton("💬 Buy WhatsApp Account (₹99)", callback_data="show_qr_wa_acc")
        btn_tg = types.InlineKeyboardButton("📱 Buy Telegram Account (₹99)", callback_data="show_qr_tg_acc")
        markup.add(btn_wa, btn_tg)

        bot.send_message(
            user_id,
            "🛒 **BUY ACCOUNTS HUB**\n\n"
            "Kripya niche diye gaye options me se chunayein:\n\n"
            "💬 **WhatsApp Account:** ₹99\n"
            "📱 **Telegram Account:** ₹99",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif message.text == "📞 Buy Number":
        stock_cnt = get_stock_count("number")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Number Out of Stock!**\n\nFilhal koi number available nahi hai.", parse_mode="Markdown")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_wa = types.InlineKeyboardButton(f"💬 WhatsApp (₹{DEFAULT_EXPECTED_AMOUNT})", callback_data="pay_num_whatsapp")
        btn_tg = types.InlineKeyboardButton(f"📱 Telegram (₹{DEFAULT_EXPECTED_AMOUNT})", callback_data="pay_num_telegram")
        btn_fb = types.InlineKeyboardButton(f"👥 Facebook (₹{DEFAULT_EXPECTED_AMOUNT})", callback_data="pay_num_facebook")
        btn_ig = types.InlineKeyboardButton(f"📸 Instagram (₹{DEFAULT_EXPECTED_AMOUNT})", callback_data="pay_num_instagram")
        markup.add(btn_wa, btn_tg, btn_fb, btn_ig)

        bot.send_message(
            user_id,
            "📞 **SELECT SERVICE FOR OTP NUMBER**\n\n"
            f"💵 **Price:** ₹{DEFAULT_EXPECTED_AMOUNT} per Number\n"
            f"📦 **Available Number Stock:** {stock_cnt}\n\n"
            "Kripya niche diye gaye buttons me se select karein ki aapko kis app ke liye number chahiye:",
            reply_markup=markup
        )

    elif message.text == "🛒 Buy Gmail":
        stock_cnt = get_stock_count("gmail")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Gmail Out of Stock!**\n\nFilhal koi Gmail available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Send Proof", callback_data="show_qr_gmail")
        inline_kb.add(btn_pay)

        buy_text = (
            "🛒 **Buy Fresh Gmail Account**\n\n"
            f"💵 **Price:** ₹{DEFAULT_EXPECTED_AMOUNT} per Gmail\n"
            f"📦 **Available Stock:** {stock_cnt}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "👥 Buy Facebook":
        stock_cnt = get_stock_count("facebook")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Facebook Out of Stock!**\n\nFilhal koi Facebook Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Send Proof", callback_data="show_qr_fb")
        inline_kb.add(btn_pay)

        buy_text = (
            "👥 **Buy Facebook Account**\n\n"
            f"💵 **Price:** ₹{DEFAULT_EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {stock_cnt}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "🐦 Buy Twitter":
        stock_cnt = get_stock_count("twitter")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Twitter Out of Stock!**\n\nFilhal koi Twitter Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Send Proof", callback_data="show_qr_twitter")
        inline_kb.add(btn_pay)

        buy_text = (
            "🐦 **Buy Twitter Account**\n\n"
            f"💵 **Price:** ₹{DEFAULT_EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {stock_cnt}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "📸 Buy Instagram":
        stock_cnt = get_stock_count("instagram")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Instagram Out of Stock!**\n\nFilhal koi Instagram Account available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Send Proof", callback_data="show_qr_insta")
        inline_kb.add(btn_pay)

        buy_text = (
            "📸 **Buy Instagram Account**\n\n"
            f"💵 **Price:** ₹{DEFAULT_EXPECTED_AMOUNT} per Account\n"
            f"📦 **Available Stock:** {stock_cnt}\n\n"
            "Payment karne ke liye niche button par click karein."
        )
        bot.send_message(user_id, buy_text, parse_mode="Markdown", reply_markup=inline_kb)

    elif message.text == "👤 Profile":
        total_bought = col_purchases.count_documents({"user_id": str(user_id)})
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
        purchases = list(col_purchases.find({"user_id": str(user_id)}))
        if not purchases:
            bot.send_message(user_id, "📑 **MY PURCHASED HISTORY**\n\n❌ Aapne abhi tak koi item buy nahi kiya hai.", parse_mode="Markdown")
            return

        history_text = "📑 **YOUR PURCHASE HISTORY:**\n\n"
        for idx, item in enumerate(purchases, start=1):
            history_text += f"{idx}. **UTR:** `{item['utr']}`\n   **Data:** `{item['data']}`\n\n"
        bot.send_message(user_id, history_text, parse_mode="Markdown")

# =========================================================
# DYNAMIC PRICE-LOCKED QR SENDER FUNCTION
# =========================================================

def send_dynamic_payment_qr(user_id, item_name, amount):
    """Generates and sends dynamic price-locked QR code"""
    try:
        qr_url = get_dynamic_qr_url(
            upi_id=UPI_ID,
            name=UPI_NAME,
            amount=amount,
            note=f"Payment for {item_name}"
        )

        payment_text = (
            f"💳 **LOCKED PAYMENT QR FOR {item_name.upper()}**\n\n"
            f"💰 **Exact Price:** ₹{amount} *(Amount Locked)*\n"
            f"👤 **UPI Name:** `{UPI_NAME}`\n"
            f"📌 **UPI ID:** `{UPI_ID}`\n\n"
            "⚠️ **Note:** QR scan karte hi payment app me amount pehle se **Locked** aayega.\n"
            "📲 Payment karne ke baad apna **UTR Number ya Payment Screenshot** yahin chat me bhej dein!"
        )
        
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=payment_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[QR ERROR]: {e}")
        user_states[user_id] = None
        bot.send_message(user_id, "❌ QR code generate karne me dikkat aayi.")

# =========================================================
# INLINE BUTTON HANDLERS
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.message.chat.id
    name = call.from_user.first_name
    username = f"@{call.from_user.username}" if call.from_user.username else "Unknown"

    save_user_info(call.from_user)

    if call.data.startswith("pay_num_"):
        if get_stock_count("number") == 0:
            bot.answer_callback_query(call.id, "❌ Number Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal numbers available nahi hain.", parse_mode="Markdown")
            return

        service = call.data.split("_")[2]
        temp_number_requests[user_id] = {"service": service} 
        user_payment_amounts[user_id] = DEFAULT_EXPECTED_AMOUNT
        user_states[user_id] = "AWAITING_NUMBER_PAYMENT_PROOF"
        
        send_dynamic_payment_qr(user_id, f"{service.upper()} Number", DEFAULT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, f"✅ Selected: {service.upper()} Number")

    elif call.data == "show_qr_wa_acc":
        if get_stock_count("wa_account") == 0:
            bot.answer_callback_query(call.id, "❌ WhatsApp Account Out of Stock!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal WhatsApp Accounts available nahi hain.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_WA_ACC_PAYMENT_PROOF"
        user_payment_amounts[user_id] = ACCOUNT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "WhatsApp Account", ACCOUNT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    elif call.data == "show_qr_tg_acc":
        if get_stock_count("tg_account") == 0:
            bot.answer_callback_query(call.id, "❌ Telegram Account Out of Stock!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Telegram Accounts available nahi hain.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_TG_ACC_PAYMENT_PROOF"
        user_payment_amounts[user_id] = ACCOUNT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "Telegram Account", ACCOUNT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    elif call.data == "show_qr_gmail":
        if get_stock_count("gmail") == 0:
            bot.answer_callback_query(call.id, "❌ Gmail Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Gmail available nahi hai.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_PAYMENT_PROOF"
        user_payment_amounts[user_id] = DEFAULT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "Gmail Account", DEFAULT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    elif call.data == "show_qr_fb":
        if get_stock_count("facebook") == 0:
            bot.answer_callback_query(call.id, "❌ Facebook Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Facebook available nahi hai.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_FB_PAYMENT_PROOF"
        user_payment_amounts[user_id] = DEFAULT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "Facebook Account", DEFAULT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    elif call.data == "show_qr_twitter":
        if get_stock_count("twitter") == 0:
            bot.answer_callback_query(call.id, "❌ Twitter Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Twitter available nahi hai.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_TWITTER_PAYMENT_PROOF"
        user_payment_amounts[user_id] = DEFAULT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "Twitter Account", DEFAULT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    elif call.data == "show_qr_insta":
        if get_stock_count("instagram") == 0:
            bot.answer_callback_query(call.id, "❌ Instagram Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Instagram available nahi hai.", parse_mode="Markdown")
            return

        user_states[user_id] = "AWAITING_INSTA_PAYMENT_PROOF"
        user_payment_amounts[user_id] = DEFAULT_EXPECTED_AMOUNT
        
        send_dynamic_payment_qr(user_id, "Instagram Account", DEFAULT_EXPECTED_AMOUNT)
        bot.answer_callback_query(call.id, "✅ QR Code sent!")

    # =========================================================
    # ADMIN APPROVAL / REJECTION BUTTON CLICKS
    # =========================================================
    elif call.data.startswith("approve_pay_"):
        if call.from_user.id != ADMIN_USER_ID:
            bot.answer_callback_query(call.id, "❌ You are not authorized!", show_alert=True)
            return
        
        payment_id = call.data.replace("approve_pay_", "")
        pending_data = col_pending_payments.find_one({"_id": payment_id})

        if not pending_data:
            bot.answer_callback_query(call.id, "⚠️ Yeh payment request pehle hi process ho chuki hai!", show_alert=True)
            return

        target_user_id = int(pending_data["user_id"])
        category = pending_data["category"]
        amount = pending_data["amount"]
        service = pending_data.get("service", "")

        # Stock fetch karo
        stock_item = get_and_pop_stock(category)
        if not stock_item:
            bot.answer_callback_query(call.id, "❌ Stock khatam ho gaya hai!", show_alert=True)
            bot.send_message(ADMIN_USER_ID, f"❌ Stock Out error: `{category}` ke liye stock available nahi hai!")
            return

        account_data = stock_item["text"]
        msg_id_to_delete = stock_item["msg_id"]

        # Source group se message delete karo
        group_mapping = {
            "gmail": GMAIL_GROUP_ID,
            "number": NUMBER_GROUP_ID,
            "facebook": FB_GROUP_ID,
            "twitter": TWITTER_GROUP_ID,
            "instagram": INSTA_GROUP_ID,
            "wa_account": WA_ACC_GROUP_ID,
            "tg_account": TG_ACC_GROUP_ID
        }
        if category in group_mapping:
            try:
                bot.delete_message(group_mapping[category], msg_id_to_delete)
            except Exception as e:
                print(f"[DELETE ERROR] {e}")

        # Purchase record save karo
        dummy_utr = f"MANUAL-{payment_id[:6]}"
        if category == "number":
            record_purchase(target_user_id, dummy_utr, f"[{service.upper()}] {account_data}")
            bot.send_message(
                target_user_id,
                f"🎉 **Payment Approved & Order Successful!**\n\n"
                f"💰 **Paid Amount:** ₹{amount}\n"
                f"📱 **Service:** `{service.upper()}`\n"
                f"📞 **Phone Number:** `{account_data}`\n\n"
                "⏳ *OTP ka wait karein. Jaise hi OTP aayega, bot aapko yahin bhej dega.*",
                parse_mode="Markdown"
            )
        else:
            record_purchase(target_user_id, dummy_utr, account_data)
            bot.send_message(
                target_user_id,
                f"✅ **Payment Approved & Order Successful!**\n\n"
                f"💰 **Paid Amount:** ₹{amount}\n"
                f"📦 **{category.upper()} Account Details:**\n`{account_data}`",
                parse_mode="Markdown"
            )

        # Pending data delete karo
        col_pending_payments.delete_one({"_id": payment_id})

        # Admin message update karo
        try:
            bot.edit_message_caption(
                chat_id=ADMIN_USER_ID,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n✅ **STATUS: APPROVED BY ADMIN**",
                parse_mode="Markdown"
            )
        except Exception:
            try:
                bot.edit_message_text(
                    chat_id=ADMIN_USER_ID,
                    message_id=call.message.message_id,
                    text=call.message.text + "\n\n✅ **STATUS: APPROVED BY ADMIN**",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        bot.answer_callback_query(call.id, "✅ Payment Approved Successfully!")
        send_log(f"✅ **Payment Approved by Admin**\n👤 **User ID:** `{target_user_id}`\n📦 **Category:** `{category}`\n💰 **Amount:** `₹{amount}`")

    elif call.data.startswith("reject_pay_"):
        if call.from_user.id != ADMIN_USER_ID:
            bot.answer_callback_query(call.id, "❌ You are not authorized!", show_alert=True)
            return
        
        payment_id = call.data.replace("reject_pay_", "")
        pending_data = col_pending_payments.find_one({"_id": payment_id})

        if not pending_data:
            bot.answer_callback_query(call.id, "⚠️ Yeh payment request pehle hi process ho chuki hai!", show_alert=True)
            return

        target_user_id = int(pending_data["user_id"])
        col_pending_payments.delete_one({"_id": payment_id})

        # User ko Warning DM bhejo
        try:
            bot.send_message(
                target_user_id,
                "🚨 **WARNING: PAYMENT REJECTED / FRAUD DETECTED!** ⚠️\n\n"
                "Aapka payment proof / UTR / Screenshot **Admin** dwara reject kar diya gaya hai.\n"
                "Kripya koi bhi fake ya edited screenshot/payment na bhejein, warna aapko bot se permanently **Ban** kar diya jayega!\n\n"
                "Agar aapne asli payment kiya hai, toh support par contact karein.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[WARNING DM ERROR]: {e}")

        # Admin message update karo
        try:
            bot.edit_message_caption(
                chat_id=ADMIN_USER_ID,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n❌ **STATUS: REJECTED & WARNING SENT**",
                parse_mode="Markdown"
            )
        except Exception:
            try:
                bot.edit_message_text(
                    chat_id=ADMIN_USER_ID,
                    message_id=call.message.message_id,
                    text=call.message.text + "\n\n❌ **STATUS: REJECTED & WARNING SENT**",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        bot.answer_callback_query(call.id, "❌ Payment Rejected & Warning Sent!")
        send_log(f"❌ **Payment Rejected & Warning Sent**\n👤 **User ID:** `{target_user_id}`")

# =========================================================
# MANUAL PAYMENT PROOF HANDLER (TEXT OR PHOTO)
# =========================================================

def handle_manual_payment_proof(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Unknown"

    current_state = user_states.get(user_id)

    state_to_category = {
        "AWAITING_PAYMENT_PROOF": "gmail",
        "AWAITING_NUMBER_PAYMENT_PROOF": "number",
        "AWAITING_FB_PAYMENT_PROOF": "facebook",
        "AWAITING_TWITTER_PAYMENT_PROOF": "twitter",
        "AWAITING_INSTA_PAYMENT_PROOF": "instagram",
        "AWAITING_WA_ACC_PAYMENT_PROOF": "wa_account",
        "AWAITING_TG_ACC_PAYMENT_PROOF": "tg_account"
    }

    if current_state not in state_to_category:
        return

    category = state_to_category[current_state]
    amount = user_payment_amounts.get(user_id, DEFAULT_EXPECTED_AMOUNT)
    service = temp_number_requests.get(user_id, {}).get("service", "")

    # State reset karo
    user_states[user_id] = None

    payment_id = str(uuid.uuid4())

    # MongoDB me pending payment save karo
    col_pending_payments.insert_one({
        "_id": payment_id,
        "user_id": str(user_id),
        "name": name,
        "username": username,
        "category": category,
        "amount": amount,
        "service": service,
        "date": datetime.now()
    })

    # Admin ke paas Approve/Reject button ke sath message bhejo
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_pay_{payment_id}")
    btn_reject = types.InlineKeyboardButton("❌ Reject & Warn", callback_data=f"reject_pay_{payment_id}")
    admin_markup.add(btn_approve, btn_reject)

    admin_msg_text = (
        f"🚨 **NEW PAYMENT PROOF RECEIVED!**\n\n"
        f"👤 **User Name:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🛒 **Category:** `{category.upper()}`\n"
        f"💰 **Paid Amount:** `₹{amount}`\n"
    )
    if service:
        admin_msg_text += f"📱 **Service:** `{service.upper()}`\n"

    # User ko confirmation do
    bot.send_message(
        user_id,
        "⏳ **Payment Proof Submitted Successfully!**\n\nAapka payment verification ke liye Admin ke paas bhej diya gaya hai. Kripya thoda wait karein, approve hote hi aapko item mil jayega.",
        parse_mode="Markdown"
    )

    # Admin ko send karo
    if message.content_type == 'photo':
        photo_file_id = message.photo[-1].file_id
        admin_msg_text += f"\n📸 *User ne payment ka screenshot bheja hai upar.*"
        bot.send_photo(
            chat_id=ADMIN_USER_ID,
            photo=photo_file_id,
            caption=admin_msg_text,
            reply_markup=admin_markup,
            parse_mode="Markdown"
        )
    else:
        text_proof = message.text.strip()
        admin_msg_text += f"\n📝 **UTR / Details:** `{text_proof}`"
        bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_msg_text,
            reply_markup=admin_markup,
            parse_mode="Markdown"
        )

# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    print("Bot starting with Enhanced Manual Admin Approval & Warning System...")
    bot.infinity_polling()
