import telebot
from telebot import types
import requests
import re
import os

# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631269601:AAH5keWN0qXjK60H8GTN5G-MLpqQTapxCuM"

# ALAG-ALAG STOCK GROUPS/CHANNELS
GMAIL_GROUP_ID = -1004388026969     # Gmail Stock Group ID
NUMBER_GROUP_ID = -1004418431812    # Phone Number Stock Group ID
FB_GROUP_ID = -1003966946655        # Facebook Stock Group ID
TWITTER_GROUP_ID = -1003851497827   # Twitter Stock Group ID
INSTA_GROUP_ID = -1003988074533     # Instagram Stock Group ID

# ALERT / LOG / BROADCAST CHANNEL
RAW_CHANNEL_ID = "4418224009"

if not str(RAW_CHANNEL_ID).startswith("-100"):
    LOG_CHANNEL_ID = int(f"-100{RAW_CHANNEL_ID.replace('-', '')}")
else:
    LOG_CHANNEL_ID = int(RAW_CHANNEL_ID)

ADMIN_USER_ID = 6403557650
OCR_API_KEY = "K83665952588957"
ADMIN_USERNAME = "BhaiCharaYT"

USERS_FILE = "registered_users.txt"  # Registered Users Database File

# =========================================================
# PAYMENT CONFIG
# =========================================================

EXPECTED_AMOUNT = "30"
UPI_ID = "paytm.s26tbd7@pty"
UPI_NAME = "Mr Subham"
QR_PINNED_MESSAGE_ID = 39

EXPECTED_NAME_KEYWORDS = ["DICTATOR", "MERCHANT", "SHOP", "SUBHAM"]

# =========================================================

bot = telebot.TeleBot(BOT_TOKEN)

used_utrs = set()
user_states = {}
gmail_stock_list = []       
number_stock_list = []      
fb_stock_list = []          
twitter_stock_list = []     
insta_stock_list = []       

user_purchases = {}
temp_number_requests = {}

# =========================================================
# DATABASE & LOG FUNCTIONS
# =========================================================

def save_user_id(chat_id):
    """New User Chat ID ko text file me save karne ke liye"""
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = set(line.strip() for line in f.readlines())
    
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{str(chat_id)}\n")

def get_all_users():
    """Text file se sabhi active users ki ID fetch karne ke liye"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"[LOG ERROR] Channel par log nahi gaya: {e}")

# =========================================================
# CHANNEL COMMANDS (/user & /broadcast)
# =========================================================

@bot.channel_post_handler(func=lambda message: message.chat.id == LOG_CHANNEL_ID)
def handle_channel_commands(message):
    text = message.text.strip() if message.text else ""

    # --- 1. COMMAND: /user ---
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

    # --- 2. COMMAND: /broadcast ---
    if text.lower().startswith("/broadcast"):
        broadcast_msg = text[10:].strip()
        
        if not broadcast_msg:
            bot.send_message(LOG_CHANNEL_ID, "⚠️ **Format:** `/broadcast Aapka Message Yaha`", parse_mode="Markdown")
            return

        users = get_all_users()
        if not users:
            bot.send_message(LOG_CHANNEL_ID, "❌ Broadcast karne ke liye koi registered user nahi mila.", parse_mode="Markdown")
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
    save_user_id(message.chat.id)

    welcome_text = (
        f"👋 Welcome **{message.from_user.first_name}**!\n\n"
        "📧 **Gmail Store & OTP Number Bot** me aapka swagat hai."
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
# ADMIN STATUS COMMAND
# =========================================================

@bot.message_handler(commands=['botstatus'])
def check_bot_status(message):
    if message.chat.id != ADMIN_USER_ID:
        return
    
    users = get_all_users()
    bot.send_message(
        message.chat.id, 
        f"📊 **BOT STATUS**\n\n👥 **Total Users:** `{len(users)}`", 
        parse_mode="Markdown"
    )

# =========================================================
# SEPARATED STOCK GROUPS CAPTURE
# =========================================================

@bot.message_handler(func=lambda message: message.chat.id == GMAIL_GROUP_ID, content_types=['text'])
def capture_gmail_stock(message):
    text_content = message.text.strip()
    gmail_stock_list.append({"msg_id": message.message_id, "text": text_content})
    total_count = len(gmail_stock_list)
    
    send_log(
        f"📦 **New Stock Added (📧 Gmail Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Gmail Stock Available:** {total_count}"
    )

@bot.message_handler(func=lambda message: message.chat.id == NUMBER_GROUP_ID, content_types=['text'])
def capture_number_stock(message):
    text_content = message.text.strip()
    number_stock_list.append({"msg_id": message.message_id, "text": text_content})
    total_count = len(number_stock_list)
    
    send_log(
        f"📦 **New Stock Added (📞 Number Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Number Stock Available:** {total_count}"
    )

@bot.message_handler(func=lambda message: message.chat.id == FB_GROUP_ID, content_types=['text'])
def capture_fb_stock(message):
    text_content = message.text.strip()
    fb_stock_list.append({"msg_id": message.message_id, "text": text_content})
    total_count = len(fb_stock_list)
    
    send_log(
        f"📦 **New Stock Added (👥 Facebook Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Facebook Stock Available:** {total_count}"
    )

@bot.message_handler(func=lambda message: message.chat.id == TWITTER_GROUP_ID, content_types=['text'])
def capture_twitter_stock(message):
    text_content = message.text.strip()
    twitter_stock_list.append({"msg_id": message.message_id, "text": text_content})
    total_count = len(twitter_stock_list)
    
    send_log(
        f"📦 **New Stock Added (🐦 Twitter Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Twitter Stock Available:** {total_count}"
    )

@bot.message_handler(func=lambda message: message.chat.id == INSTA_GROUP_ID, content_types=['text'])
def capture_insta_stock(message):
    text_content = message.text.strip()
    insta_stock_list.append({"msg_id": message.message_id, "text": text_content})
    total_count = len(insta_stock_list)
    
    send_log(
        f"📦 **New Stock Added (📸 Instagram Stock)**\n\n"
        f"🆔 **Msg ID:** `{message.message_id}`\n"
        f"📝 **Data:** `{text_content}`\n"
        f"📊 **Total Instagram Stock Available:** {total_count}"
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
    for uid in user_purchases.keys():
        try:
            chat_member = bot.get_chat(uid)
            if chat_member.username and chat_member.username.lower() == target_username:
                found_chat_id = uid
                break
        except Exception:
            continue
            
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
            bot.send_message(message.chat.id, f"❌ User ko message bhejme me error aayi: {e}")
    else:
        bot.send_message(message.chat.id, f"❌ Is username (`@{target_username}`) ka koi active user bot me nahi mila ya usne koi item buy nahi kiya hai.")

# =========================================================
# MAIN MENU BUTTON HANDLERS
# =========================================================

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_menu(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

    save_user_id(user_id)

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
            history_text += f"{idx}. **Type:** `{item['utr']}`\n   **Data:** `{item['data']}`\n\n"
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
# INLINE BUTTON HANDLER
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.message.chat.id
    name = call.from_user.first_name
    username = f"@{call.from_user.username}" if call.from_user.username else "No Username"

    save_user_id(user_id)

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
# CLOUD OCR
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
# PAYMENT SCREENSHOT HANDLER
# =========================================================

@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    current_state = user_states.get(user_id)

    save_user_id(user_id)

    valid_states = [
        "AWAITING_PAYMENT_PROOF", 
        "AWAITING_NUMBER_PAYMENT_PROOF", 
        "AWAITING_FB_PAYMENT_PROOF", 
        "AWAITING_TWITTER_PAYMENT_PROOF",
        "AWAITING_INSTA_PAYMENT_PROOF"
    ]
    if current_state not in valid_states:
        return

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

            if user_id not in user_purchases:
                user_purchases[user_id] = []
            user_purchases[user_id].append({"utr": utr_found, "data": account_data})

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n📧 **Gmail Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
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

            if user_id not in user_purchases:
                user_purchases[user_id] = []
            user_purchases[user_id].append({"utr": utr_found, "data": f"[{service.upper()}] {number_data}"})

            bot.send_message(
                user_id,
                f"🎉 **Payment Verified & Number Allotted!**\n\n"
                f"📱 **Service:** `{service.upper()}`\n"
                f"📞 **Phone Number:** `{number_data}`\n"
                f"🆔 **UTR:** `{utr_found}`\n\n"
                "⏳ *OTP ka wait karein. Jaise hi OTP aayega, bot aapko yahin bhej dega.*",
                parse_mode="Markdown"
            )

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

            if user_id not in user_purchases:
                user_purchases[user_id] = []
            user_purchases[user_id].append({"utr": utr_found, "data": account_data})

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n👥 **Facebook Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
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

            if user_id not in user_purchases:
                user_purchases[user_id] = []
            user_purchases[user_id].append({"utr": utr_found, "data": account_data})

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n🐦 **Twitter Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
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

            if user_id not in user_purchases:
                user_purchases[user_id] = []
            user_purchases[user_id].append({"utr": utr_found, "data": account_data})

            bot.send_message(
                user_id,
                f"✅ **Payment Verified!**\n\n🆔 **UTR:** `{utr_found}`\n\n📸 **Instagram Account:**\n`{account_data}`",
                parse_mode="Markdown"
            )
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
    print("Bot Running with Channel Commands (/user & /broadcast)...")
    bot.infinity_polling()
