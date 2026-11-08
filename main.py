import telebot
from telebot import types, apihelper
import re
import os
import threading
from datetime import datetime
from pymongo import MongoClient

# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631269601:AAEd2ZNNPZydSwCF5xqnRuJ_m3YLG4JajDg"

# MONGODB CONNECTION STRING (Successfully Configured)
MONGO_URI = "mongodb+srv://botuser:Tsv3rQQQ-g4jAY3@cluster0.fe1k9gv.mongodb.net/?appName=Cluster0"

# STOCK GROUPS / CHANNELS
GMAIL_GROUP_ID = -1004388026969
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
DEFAULT_EXPECTED_AMOUNT = "25"  # Updated base price ₹25
ACCOUNT_EXPECTED_AMOUNT = "99"  # Price for WA and TG Accounts ₹99
UPI_ID = "paytm.s26tbd7@pty"
UPI_NAME = "Mr Subham"
QR_PINNED_MESSAGE_ID = 39

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
user_payment_details = {}

def save_user_info(user_obj):
    """User profile metadata ko MongoDB me permanently store karta hai"""
    if not user_obj:
        return
        
    uid_str = str(user_obj.id)
    username = f"@{user_obj.username}" if user_obj.username else "No Username"
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

def record_purchase(user_id, utr_or_ref, data_str):
    """Purchase Order Database me save karta hai"""
    now = datetime.now()
    col_purchases.insert_one({
        "user_id": str(user_id),
        "utr": utr_or_ref,
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

# OPTIMIZED FOR HIGH CONCURRENCY (100-200 USERS)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=30)

# =========================================================
# HELPER & LIVE LOG FUNCTIONS
# =========================================================

def send_log(text, reply_markup=None):
    """ALERT CHANNEL PAR LIVE MSG BHEJNE KE LIYE (ASYNC BACKGROUND)"""
    def _async_send():
        try:
            bot.send_message(LOG_CHANNEL_ID, text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            print(f"[LOG ERROR]: {e}")
    threading.Thread(target=_async_send).start()

def send_log_photo(photo_id, caption, reply_markup=None):
    """ALERT CHANNEL PAR SCREENSHOT SEND KARNE KE LIYE"""
    def _async_send_photo():
        try:
            bot.send_photo(LOG_CHANNEL_ID, photo=photo_id, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            print(f"[LOG PHOTO ERROR]: {e}")
    threading.Thread(target=_async_send_photo).start()

# =========================================================
# REAL-TIME ACTIVITY TRACKER (MIDDLEWARE)
# =========================================================

@bot.middleware_handler(update_types=['message', 'callback_query'])
def track_all_user_activities(bot_instance, update):
    """User active hote hi MongoDB update ho jayega"""
    def _async_track():
        if hasattr(update, 'from_user') and update.from_user:
            save_user_info(update.from_user)
    threading.Thread(target=_async_track).start()

# =========================================================
# MAIN MENU
# =========================================================

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        "🛒 Buy Account",
        "🛒 Buy Gmail",
        "👤 Profile",
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
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
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
            bot.send_message(
                message.chat.id,
                "📊 REGISTERED USERS LIST\n\n"
                "❌ Abhi koi registered user nahi mila."
            )
            return

        total_users = len(users_list)
        header = f"📊 REGISTERED USERS LIST\n\n👥 Total Users: {total_users}\n\n"
        current_text = header
        part_number = 1

        for index, user in enumerate(users_list, start=1):
            user_id = str(user.get("_id", "")).strip()
            username = str(user.get("username", "")).strip()

            if not username or username.lower() in ["no username", "none", "null", "no_username"]:
                user_line = f"{index}. 🆔 {user_id}\n"
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
        bot.send_message(
            message.chat.id,
            "❌ User list load karte waqt error aayi.\n\n"
            f"Error: {str(e)[:500]}"
        )

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
    
    send_log(
        f"📦 **New Stock Added (📧 Gmail Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Gmail Stock Available:** {get_stock_count('gmail')}"
    )

@bot.message_handler(func=lambda message: message.chat.id == FB_GROUP_ID, content_types=['text'])
def capture_fb_stock(message):
    text_content = message.text.strip()
    add_stock_item("facebook", message.message_id, text_content)

    send_log(
        f"📦 **New Stock Added (👥 Facebook Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Facebook Stock Available:** {get_stock_count('facebook')}"
    )

@bot.message_handler(func=lambda message: message.chat.id == TWITTER_GROUP_ID, content_types=['text'])
def capture_twitter_stock(message):
    text_content = message.text.strip()
    add_stock_item("twitter", message.message_id, text_content)

    send_log(
        f"📦 **New Stock Added (🐦 Twitter Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Twitter Stock Available:** {get_stock_count('twitter')}"
    )

@bot.message_handler(func=lambda message: message.chat.id == INSTA_GROUP_ID, content_types=['text'])
def capture_insta_stock(message):
    text_content = message.text.strip()
    add_stock_item("instagram", message.message_id, text_content)

    send_log(
        f"📦 **New Stock Added (📸 Instagram Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Instagram Stock Available:** {get_stock_count('instagram')}"
    )

# =========================================================
# MANUAL PAYMENT PROCESSOR GENERATOR
# =========================================================

def initiate_manual_payment(chat_id, category, amount, user_obj):
    ref_code = f"REF{chat_id % 10000}{int(datetime.now().timestamp()) % 1000}"
    user_states[chat_id] = "AWAITING_PAYMENT_PROOF"
    user_payment_details[chat_id] = {
        "category": category,
        "amount": amount,
        "ref_code": ref_code
    }

    try:
        bot.copy_message(chat_id=chat_id, from_chat_id=GMAIL_GROUP_ID, message_id=QR_PINNED_MESSAGE_ID)
    except Exception:
        pass

    payment_text = (
        f"💳 **MANUAL PAYMENT INSTRUCTIONS**\n\n"
        f"📦 **Category:** `{category.upper()}`\n"
        f"💰 **Locked Amount:** ₹{amount}\n"
        f"🔖 **Ref Code:** `{ref_code}`\n\n"
        f"👤 **UPI Name:** `{UPI_NAME}`\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        f"📲 Upar diye gaye QR/UPI ID par ₹{amount} send karein.\n"
        f"⚠️ **Aapko Payment karne ke baad Screenshot ya 12-digit UTR text chat me bhejna hoga.**\n"
        f"⏳ Verification status bot me instant update kiya jayega."
    )
    bot.send_message(chat_id, payment_text, parse_mode="Markdown")

    send_log(
        f"📲 **Payment Initiated**\n\n"
        f"👤 **User:** {user_obj.first_name} (`@{user_obj.username}`)\n"
        f"🆔 **ID:** `{chat_id}`\n"
        f"🛍️ **Category:** `{category.upper()}`\n"
        f"💵 **Price:** ₹{amount}\n"
        f"🔖 **Ref Code:** `{ref_code}`"
    )

# =========================================================
# MAIN MENU TEXT HANDLER
# =========================================================

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_menu_and_proofs(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

    save_user_info(message.from_user)

    # CHECK IF USER IS SUBMITTING PROOF (SCREENSHOT OR UTR TEXT)
    current_state = user_states.get(user_id)
    if current_state == "AWAITING_PAYMENT_PROOF":
        handle_payment_proof_submission(message)
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

    elif message.text == "🛒 Buy Gmail":
        stock_cnt = get_stock_count("gmail")
        if stock_cnt == 0:
            bot.send_message(user_id, "❌ **Gmail Out of Stock!**\n\nFilhal koi Gmail available nahi hai.", parse_mode="Markdown")
            return

        inline_kb = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton("💳 Pay & Verify", callback_data="show_qr_gmail")
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
        btn_pay = types.InlineKeyboardButton("💳 Pay & Verify", callback_data="show_qr_fb")
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
        btn_pay = types.InlineKeyboardButton("💳 Pay & Verify", callback_data="show_qr_twitter")
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
        btn_pay = types.InlineKeyboardButton("💳 Pay & Verify", callback_data="show_qr_insta")
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
            history_text += f"{idx}. **UTR/REF:** `{item['utr']}`\n   **Data:** `{item['data']}`\n\n"
        bot.send_message(user_id, history_text, parse_mode="Markdown")

# =========================================================
# INLINE BUTTON HANDLERS
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.message.chat.id
    save_user_info(call.from_user)

    if call.data == "show_qr_wa_acc":
        if get_stock_count("wa_account") == 0:
            bot.answer_callback_query(call.id, "❌ WhatsApp Account Out of Stock!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal WhatsApp Accounts available nahi hain.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "wa_account", ACCOUNT_EXPECTED_AMOUNT, call.from_user)

    elif call.data == "show_qr_tg_acc":
        if get_stock_count("tg_account") == 0:
            bot.answer_callback_query(call.id, "❌ Telegram Account Out of Stock!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Telegram Accounts available nahi hain.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "tg_account", ACCOUNT_EXPECTED_AMOUNT, call.from_user)

    elif call.data == "show_qr_gmail":
        if get_stock_count("gmail") == 0:
            bot.answer_callback_query(call.id, "❌ Gmail Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Gmail available nahi hai.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "gmail", DEFAULT_EXPECTED_AMOUNT, call.from_user)

    elif call.data == "show_qr_fb":
        if get_stock_count("facebook") == 0:
            bot.answer_callback_query(call.id, "❌ Facebook Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Facebook available nahi hai.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "facebook", DEFAULT_EXPECTED_AMOUNT, call.from_user)

    elif call.data == "show_qr_twitter":
        if get_stock_count("twitter") == 0:
            bot.answer_callback_query(call.id, "❌ Twitter Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Twitter available nahi hai.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "twitter", DEFAULT_EXPECTED_AMOUNT, call.from_user)

    elif call.data == "show_qr_insta":
        if get_stock_count("instagram") == 0:
            bot.answer_callback_query(call.id, "❌ Instagram Stock Out!", show_alert=True)
            bot.send_message(user_id, "❌ **Out of Stock!**\n\nFilhal Instagram available nahi hai.", parse_mode="Markdown")
            return
        bot.answer_callback_query(call.id, "✅ Order Created!")
        initiate_manual_payment(user_id, "instagram", DEFAULT_EXPECTED_AMOUNT, call.from_user)

    # ADMIN APPROVE / REJECT CALLBACKS
    elif call.data.startswith("app_") or call.data.startswith("rej_"):
        handle_admin_approval(call)

# =========================================================
# PAYMENT PROOF SUBMISSION HANDLER
# =========================================================

def handle_payment_proof_submission(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

    details = user_payment_details.get(user_id, {})
    category = details.get("category", "gmail")
    amount = details.get("amount", "25")
    ref_code = details.get("ref_code", "REF000")

    utr_found = None
    if message.content_type == 'text':
        text_entered = message.text.strip()
        utr_match = re.search(r"\b\d{12}\b", text_entered)
        if utr_match:
            utr_found = utr_match.group(0)
        else:
            utr_found = text_entered

    payment_doc = {
        "user_id": str(user_id),
        "name": name,
        "username": username,
        "category": category,
        "amount": amount,
        "ref_code": ref_code,
        "submitted_at": datetime.now(),
        "status": "PENDING"
    }
    
    pay_id = str(col_pending_payments.insert_one(payment_doc).inserted_id)
    user_states[user_id] = None

    bot.send_message(
        user_id,
        "⏳ **Payment Proof Submitted!**\n\n"
        f"🔖 **Ref Code:** `{ref_code}`\n"
        "Aapki payment request admin ko bhej di gayi hai.\n"
        "Please wait karein, verify hote hi aapka item bhej diya jayega.",
        parse_mode="Markdown"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton("✅ Approve & Deliver", callback_data=f"app_{pay_id}")
    btn_reject = types.InlineKeyboardButton("❌ Reject Payment", callback_data=f"rej_{pay_id}")
    markup.add(btn_approve, btn_reject)

    log_msg = (
        f"🚨 **NEW PAYMENT SUBMISSION**\n\n"
        f"👤 **Name:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🛍️ **Category:** `{category.upper()}`\n"
        f"💵 **Price:** ₹{amount}\n"
        f"🔖 **Ref Code:** `{ref_code}`\n"
        f"📝 **UTR/Text:** `{utr_found if utr_found else 'Photo Submitted'}`"
    )

    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
        send_log_photo(photo_id, caption=log_msg, reply_markup=markup)
    else:
        send_log(log_msg, reply_markup=markup)

# =========================================================
# ADMIN APPROVAL / REJECTION HANDLER
# =========================================================

def handle_admin_approval(call):
    if call.from_user.id != ADMIN_USER_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin can action this!", show_alert=True)
        return

    action, pay_id = call.data.split("_", 1)
    from bson.objectid import ObjectId
    
    pay_doc = col_pending_payments.find_one({"_id": ObjectId(pay_id)})
    if not pay_doc:
        bot.answer_callback_query(call.id, "❌ Record not found!", show_alert=True)
        return

    if pay_doc.get("status") != "PENDING":
        bot.answer_callback_query(call.id, "⚠️ Already processed!", show_alert=True)
        return

    user_id = int(pay_doc["user_id"])
    category = pay_doc["category"]
    ref_code = pay_doc["ref_code"]

    category_group_map = {
        "gmail": GMAIL_GROUP_ID,
        "facebook": FB_GROUP_ID,
        "twitter": TWITTER_GROUP_ID,
        "instagram": INSTA_GROUP_ID,
        "wa_account": WA_ACC_GROUP_ID,
        "tg_account": TG_ACC_GROUP_ID
    }

    if action == "app":
        stock_item = get_and_pop_stock(category)
        if not stock_item:
            bot.answer_callback_query(call.id, f"❌ {category.upper()} Out of stock!", show_alert=True)
            return

        account_data = stock_item["text"]
        msg_id_to_delete = stock_item["msg_id"]

        try:
            group_id = category_group_map.get(category)
            if group_id:
                bot.delete_message(group_id, msg_id_to_delete)
        except Exception as e:
            print(f"[DELETE ERROR]: {e}")

        record_purchase(user_id, ref_code, account_data)
        col_pending_payments.update_one({"_id": ObjectId(pay_id)}, {"$set": {"status": "APPROVED"}})

        bot.send_message(
            user_id,
            f"✅ **Payment Approved!**\n\n"
            f"🔖 **Ref Code:** `{ref_code}`\n\n"
            f"📦 **{category.upper()} Account Delivered:**\n`{account_data}`",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "✅ Payment Approved & Item Delivered!", show_alert=True)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n🟢 **STATUS: APPROVED & DELIVERED**"
            )
        except Exception:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + "\n\n🟢 **STATUS: APPROVED & DELIVERED**"
            )

    elif action == "rej":
        col_pending_payments.update_one({"_id": ObjectId(pay_id)}, {"$set": {"status": "REJECTED"}})
        
        bot.send_message(
            user_id,
            f"❌ **Payment Rejected!**\n\n"
            f"🔖 **Ref Code:** `{ref_code}`\n"
            "Aapki payment verify nahi ho payi. Direct Support admin se contact karein.",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "❌ Payment Rejected!", show_alert=True)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n🔴 **STATUS: REJECTED**"
            )
        except Exception:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + "\n\n🔴 **STATUS: REJECTED**"
            )

# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    print("Bot starting with Multi-Threading & Manual Verification System...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
