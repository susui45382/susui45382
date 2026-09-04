import os
import re
import requests

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

# ---------------------------------------------------------
# BOT TOKEN
# ---------------------------------------------------------
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "8776497163:AAHgwc9jvi_gQvObU5--X3QQ-iMzc1WtofQ"
)

# ---------------------------------------------------------
# OCR.SPACE API KEY
# ---------------------------------------------------------
OCR_SPACE_API_KEY = os.getenv(
    "OCR_SPACE_API_KEY",
    "K83665952588957"
)

# ---------------------------------------------------------
# ADMIN TELEGRAM USER ID
# ---------------------------------------------------------
ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "123456789"
    )
)

# ---------------------------------------------------------
# YOUR UPI DETAILS
# ---------------------------------------------------------
MY_UPI_ID = "paytm.s26tbd7@pty"
MY_UPI_NAME = "Subham"

BUY_BUTTON_TEXT = "👑 Buy Premium Access 🔥"


# =========================================================
# TELEGRAM GROUP CONFIG
# =========================================================

START_GROUP_ID = int(
    os.getenv(
        "START_GROUP_ID",
        "-1003831777288"
    )
)

START_PINNED_MESSAGE_ID = int(
    os.getenv(
        "START_PINNED_MESSAGE_ID",
        "14"
    )
)


DEMO_GROUP_ID = int(
    os.getenv(
        "DEMO_GROUP_ID",
        "-1003831777288"
    )
)

DEMO_PINNED_MESSAGE_ID = int(
    os.getenv(
        "DEMO_PINNED_MESSAGE_ID",
        "7"
    )
)


QR_GROUP_ID = int(
    os.getenv(
        "QR_GROUP_ID",
        "-1003831777288"
    )
)

QR_PINNED_MESSAGE_ID = int(
    os.getenv(
        "QR_PINNED_MESSAGE_ID",
        "16"
    )
)


VIDEO_GROUP_ID = int(
    os.getenv(
        "VIDEO_GROUP_ID",
        "-1003831777288"
    )
)


# =========================================================
# PREMIUM PLANS
# =========================================================

PLAN_DETAILS = {

    "plan_49": {
        "price_str": "₹49",
        "amount": 49,
        "name": "🫦 𝐂𝐇*𝐋𝐃-𝐏*𝐑𝐍🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_49",
                "18"
            )
        ),
    },

    "plan_69": {
        "price_str": "₹69",
        "amount": 69,
        "name": "🫦 𝐑𝐏𝐄-𝐏*𝐑𝐍🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_69",
                "30"
            )
        ),
    },

    "plan_79": {
        "price_str": "₹79",
        "amount": 79,
        "name": "🫦 𝐃𝐄𝐒𝐈 𝐁𝐇𝐀𝐁𝐇𝐈🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_79",
                "22"
            )
        ),
    },

    "plan_99": {
        "price_str": "₹99",
        "amount": 99,
        "name": "🫦 𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌 𝐒𝐓𝐀𝐑🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_99",
                "23"
            )
        ),
    },

    "plan_149": {
        "price_str": "₹149",
        "amount": 149,
        "name": "🫦 𝐓𝐄𝐄𝐍 𝐈𝐍𝐃𝐈𝐀𝐍🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_149",
                "26"
            )
        ),
    },

    "plan_199": {
        "price_str": "₹199",
        "amount": 199,
        "name": "🫦 𝐁𝐑𝐎𝐓𝐇𝐄𝐑-𝐒𝐈𝐒𝐓𝐄𝐑🫦💦",
        "video_id": int(
            os.getenv(
                "VIDEO_ID_199",
                "28"
            )
        ),
    },
}


# =========================================================
# STATE
# =========================================================

WAITING_FOR_SCREENSHOT = 1

USED_UTRS = set()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🟢 ₹49 — 🫦 𝐂𝐇*𝐋𝐃-𝐏*𝐑𝐍🫦💦",
                callback_data="plan_49"
            )
        ],

        [
            InlineKeyboardButton(
                "🔵 ₹69 — 🫦 𝐑𝐏𝐄-𝐏*𝐑𝐍🫦💦",
                callback_data="plan_69"
            )
        ],

        [
            InlineKeyboardButton(
                "🟣 ₹79 — 🫦 𝐃𝐄𝐒𝐈 𝐁𝐇𝐀𝐁𝐇𝐈🫦💦",
                callback_data="plan_79"
            )
        ],

        [
            InlineKeyboardButton(
                "🟠 ₹99 — 🫦 𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌 𝐒𝐓𝐀𝐑🫦💦",
                callback_data="plan_99"
            )
        ],

        [
            InlineKeyboardButton(
                "🔥 ₹149 — 🫦 𝐓𝐄𝐄𝐍 𝐈𝐍𝐃𝐈𝐀𝐍🫦💦",
                callback_data="plan_149"
            )
        ],

        [
            InlineKeyboardButton(
                "👑 ₹199 — 🫦 𝐁𝐑𝐎𝐓𝐇𝐄𝐑-𝐒𝐈𝐒𝐓𝐄𝐑🫦💦",
                callback_data="plan_199"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Demo",
                callback_data="demo"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# OCR API
# =========================================================

def extract_text_from_image_api(
    image_bytes
):

    try:

        url = (
            "https://api.ocr.space/"
            "parse/image"
        )

        payload = {

            "apikey": OCR_SPACE_API_KEY,

            "language": "eng",

            "isOverlayRequired": False,

            "OCREngine": 2,

            "scale": True,

            "detectOrientation": True,

        }

        files = {

            "file": (
                "payment.jpg",
                image_bytes,
                "image/jpeg"
            )

        }

        response = requests.post(

            url,

            data=payload,

            files=files,

            timeout=30

        )

        response.raise_for_status()

        result = response.json()

        if result.get(
            "IsErroredOnProcessing"
        ):

            print(
                "OCR ERROR:",
                result.get(
                    "ErrorMessage"
                )
            )

            return ""


        parsed_results = result.get(
            "ParsedResults",
            []
        )


        if not parsed_results:

            return ""


        all_text = []


        for item in parsed_results:

            text = item.get(
                "ParsedText",
                ""
            )

            if text:

                all_text.append(
                    text
                )


        return "\n".join(
            all_text
        )


    except Exception as e:

        print(
            "OCR EXCEPTION:",
            e
        )

        return ""


# =========================================================
# NORMALIZE OCR TEXT
# =========================================================

def normalize_ocr_text(
    text
):

    text = text.lower()

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = text.replace(
        ",",
        ""
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# AMOUNT CHECK
# =========================================================

def amount_found_in_text(
    text,
    expected_amount
):

    amount = str(
        expected_amount
    )


    patterns = [

        # 49
        rf"(?<!\d){amount}(?!\d)",

        # 49.00
        rf"(?<!\d){amount}\.00(?!\d)",

        # 49.0
        rf"(?<!\d){amount}\.0(?!\d)",

        # ₹49
        rf"₹\s*{amount}\b",

        # ₹ 49
        rf"₹\s+{amount}\b",

        # Rs 49
        rf"\brs\.?\s*{amount}\b",

        # INR 49
        rf"\binr\.?\s*{amount}\b",

    ]


    for pattern in patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            return True


    # OCR कभी 4 9 कर देता है

    if len(amount) == 2:

        spaced = (
            amount[0]
            + r"\s+"
            + amount[1:]
        )

        if re.search(
            rf"(?<!\d){spaced}(?!\d)",
            text
        ):

            return True


    # 49 . 00

    if re.search(
        rf"(?<!\d)"
        rf"{amount}"
        rf"\s*\.\s*0+"
        rf"(?!\d)",
        text
    ):

        return True


    return False


# =========================================================
# RECEIVER CHECK
# =========================================================

def receiver_found_in_text(
    text
):

    upi_id = (
        MY_UPI_ID.lower()
    )

    upi_username = (
        MY_UPI_ID
        .split("@")[0]
        .lower()
    )

    name_parts = (
        MY_UPI_NAME
        .lower()
        .split()
    )


    # Full UPI

    if upi_id in text:

        return True


    # UPI username

    if upi_username in text:

        return True


    # Full name

    full_name = " ".join(
        name_parts
    )

    if full_name in text:

        return True


    # First + last name

    if len(name_parts) >= 2:

        first_name = name_parts[0]

        last_name = name_parts[-1]

        if (
            first_name in text
            and
            last_name in text
        ):

            return True


    # First name

    if name_parts:

        if name_parts[0] in text:

            return True


    return False


# =========================================================
# UTR EXTRACTION
# =========================================================

def extract_utr(
    text
):

    patterns = [

        r"(?:utr|transaction"
        r"\s*id|txn\s*id|upi"
        r"\s*ref(?:erence)?"
        r"|reference\s*no)"
        r"\s*[:#\-]?\s*"
        r"(\d{10,16})",

        r"\b\d{10,16}\b",

    ]


    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )


        if matches:

            if isinstance(
                matches[0],
                tuple
            ):

                return matches[0][0]


            return matches[0]


    return None


# =========================================================
# ADMIN NOTIFICATION
# =========================================================

async def send_admin_notification(
    context,
    user,
    plan_info,
    utr,
    extracted_text
):

    try:

        username = (
            f"@{user.username}"
            if user.username
            else "No Username"
        )

        admin_text = (

            "💰 **NEW PAYMENT VERIFIED**\n\n"

            f"👤 **User:** "
            f"{user.full_name}\n"

            f"🆔 **User ID:** "
            f"`{user.id}`\n"

            f"📱 **Username:** "
            f"{username}\n\n"

            f"👑 **Plan:** "
            f"{plan_info['name']}\n"

            f"💵 **Amount:** "
            f"{plan_info['price_str']}\n"

            f"🔢 **UTR:** "
            f"`{utr or 'Not Found'}`\n\n"

            "🤖 **OCR Verification:** "
            "PASSED"
        )


        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=admin_text,

            parse_mode="Markdown"

        )


        # OCR text admin ko bhejna

        if extracted_text:

            short_text = extracted_text[:3500]

            await context.bot.send_message(

                chat_id=ADMIN_ID,

                text=(
                    "📝 **OCR TEXT:**\n\n"
                    f"`{short_text}`"
                ),

                parse_mode="Markdown"

            )


    except Exception as e:

        print(
            "ADMIN NOTIFICATION ERROR:",
            e
        )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_chat_id = (
        update.effective_chat.id
    )


    try:

        context.user_data.clear()


        # Start pinned message

        await context.bot.copy_message(

            chat_id=user_chat_id,

            from_chat_id=START_GROUP_ID,

            message_id=START_PINNED_MESSAGE_ID

        )


        # Main menu

        await context.bot.send_message(

            chat_id=user_chat_id,

            text=(
    "👋 **Welcome!**\n\n"
    "🎉 Welcome to VIP Access Bot!\n\n"
    "✨ Get exclusive access to premium content\n"
    "💰 Affordable plans starting at just ₹99\n"
    "✨ Content quality aisi ki dekhi nahi hogi\n"
    "✨ Only Premium Content\n"
    "✨ Daily New Uploads\n"
    "✨ Cp, Rp, Indian, Foreign, Dark everything\n"
    "✨ 10000+ Cp videos\n"
    "✨ 25000+ Rp videos\n"
    "✨ M0m S0n 5k Videos\n\n"
    "✨ TRY OUR ANY PLAN FOR CHECKING THE QUALITY ✨"
),

            reply_markup=main_menu(),

            parse_mode="Markdown"

        )


    except Exception as e:

        print(
            "START ERROR:",
            e
        )


        await context.bot.send_message(

            chat_id=user_chat_id,

            text=(
                "❌ Start message भेजने में "
                "समस्या हुई।"
            )

        )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_chat_id = (
        query.from_user.id
    )


    # =====================================================
    # BUY PREMIUM
    # =====================================================

    if query.data == "buy_premium":

        await query.edit_message_text(

            text=(
                "🔥 **Exclusive Premium Plans** 👑\n\n"
                "👇 नीचे से अपना मनपसंद प्लान चुनें:"
            ),

            reply_markup=premium_menu(),

            parse_mode="Markdown"

        )

        return ConversationHandler.END


    # =====================================================
    # DEMO
    # =====================================================

    if query.data == "demo":

        try:

            await context.bot.copy_message(

                chat_id=user_chat_id,

                from_chat_id=DEMO_GROUP_ID,

                message_id=DEMO_PINNED_MESSAGE_ID

            )


            await context.bot.send_message(

                chat_id=user_chat_id,

                text=(
                    "🎁 **Demo ऊपर भेज दिया गया है।**\n\n"
                    "👇 अब अपना option चुनें:"
                ),

                reply_markup=main_menu(),

                parse_mode="Markdown"

            )


        except Exception as e:

            print(
                "DEMO ERROR:",
                e
            )


            await context.bot.send_message(

                chat_id=user_chat_id,

                text=(
                    "❌ Demo भेजने में समस्या हुई।"
                )

            )


        return ConversationHandler.END


    # =====================================================
    # BACK MAIN
    # =====================================================

    if query.data == "back_main":

        await query.edit_message_text(

            text=(
                "👇 **अपना option चुनें:**"
            ),

            reply_markup=main_menu(),

            parse_mode="Markdown"

        )

        return ConversationHandler.END


    # =====================================================
    # PLAN SELECTED
    # =====================================================

    if query.data.startswith(
        "plan_"
    ):

        if query.data not in PLAN_DETAILS:

            await context.bot.send_message(

                chat_id=user_chat_id,

                text="❌ Invalid plan."

            )

            return ConversationHandler.END


        plan_info = PLAN_DETAILS[
            query.data
        ]


        # Plan save

        context.user_data[
            "selected_plan"
        ] = query.data


        try:

            # QR message

            await context.bot.copy_message(

                chat_id=user_chat_id,

                from_chat_id=QR_GROUP_ID,

                message_id=QR_PINNED_MESSAGE_ID

            )


            # Payment instructions

            await context.bot.send_message(

                chat_id=user_chat_id,

                text=(

                    f"💳 **Payment for "
                    f"{plan_info['name']}**\n\n"

                    f"📌 **Amount:** "
                    f"`{plan_info['price_str']}`\n\n"

                    f"📌 **UPI ID:** "
                    f"`{MY_UPI_ID}`\n\n"

                    f"📌 **Name:** "
                    f"`{MY_UPI_NAME}`\n\n"

                    f"1️⃣ Exact "
                    f"**{plan_info['price_str']}** "
                    f"का payment करें।\n\n"

                    "2️⃣ Payment complete होने के बाद "
                    "**पूरा payment screenshot** "
                    "photo के रूप में भेजें।\n\n"

                    "🤖 Screenshot OCR से verify होगा।"
                ),

                parse_mode="Markdown",

                reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(

                                "🔙 Back to Plans",

                                callback_data="buy_premium"

                            )

                        ]

                    ]

                )

            )


            return WAITING_FOR_SCREENSHOT


        except Exception as e:

            print(
                "PLAN ERROR:",
                e
            )


            await context.bot.send_message(

                chat_id=user_chat_id,

                text=(
                    "❌ QR Code load करने में "
                    "समस्या हुई।"
                )

            )


            return ConversationHandler.END


# =========================================================
# SCREENSHOT HANDLER
# =========================================================

async def handle_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    user_chat_id = (
        update.effective_chat.id
    )


    selected_plan_key = (
        context.user_data.get(
            "selected_plan"
        )
    )


    # =====================================================
    # PLAN CHECK
    # =====================================================

    if not selected_plan_key:

        await update.message.reply_text(

            "❌ पहले कोई plan select करें।\n\n"
            "/start दबाएं।"

        )

        return ConversationHandler.END


    plan_info = PLAN_DETAILS.get(
        selected_plan_key
    )


    if not plan_info:

        await update.message.reply_text(

            "❌ Plan information नहीं मिली।"

        )

        return ConversationHandler.END


    expected_amount = int(
        plan_info["amount"]
    )


    # =====================================================
    # PHOTO CHECK
    # =====================================================

    if not update.message.photo:

        await update.message.reply_text(

            "❌ कृपया payment का "
            "screenshot/photo भेजें।"

        )

        return WAITING_FOR_SCREENSHOT


    # =====================================================
    # PROCESSING
    # =====================================================

    processing_msg = (
        await update.message.reply_text(

            "🔄 Screenshot read और "
            "verify किया जा रहा है..."

        )
    )


    try:

        # =================================================
        # DOWNLOAD PHOTO
        # =================================================

        photo_file = await (

            update.message
            .photo[-1]
            .get_file()

        )


        image_bytes = await (

            photo_file
            .download_as_bytearray()

        )


        # =================================================
        # OCR
        # =================================================

        extracted_text = (
            extract_text_from_image_api(
                image_bytes
            )
        )


        if not extracted_text:

            await processing_msg.edit_text(

                "❌ Screenshot का text "
                "read नहीं हो पाया।\n\n"

                "कृपया पूरा और साफ "
                "payment screenshot भेजें।"

            )

            return WAITING_FOR_SCREENSHOT


        print(
            "\n=========================="
        )

        print(
            "OCR TEXT:"
        )

        print(
            extracted_text
        )

        print(
            "==========================\n"
        )


        # =================================================
        # NORMALIZE
        # =================================================

        normalized_text = (
            normalize_ocr_text(
                extracted_text
            )
        )


        # =================================================
        # RECEIVER CHECK
        # =================================================

        receiver_ok = (
            receiver_found_in_text(
                normalized_text
            )
        )


        if not receiver_ok:

            await processing_msg.edit_text(

                "❌ **Payment Rejected!**\n\n"

                "Screenshot में receiver "
                "Name/UPI नहीं मिला।\n\n"

                "कृपया पूरा payment "
                "screenshot भेजें।",

                parse_mode="Markdown"

            )


            print(
                "REJECTED: RECEIVER"
            )


            return WAITING_FOR_SCREENSHOT


        # =================================================
        # AMOUNT CHECK
        # =================================================

        amount_ok = (
            amount_found_in_text(

                normalized_text,

                expected_amount

            )
        )


        if not amount_ok:

            await processing_msg.edit_text(

                "❌ **Payment Rejected!**\n\n"

                f"₹{expected_amount} की "
                "रकम screenshot में नहीं मिली।\n\n"

                "कृपया सही payment screenshot भेजें।",

                parse_mode="Markdown"

            )


            print(
                "REJECTED: AMOUNT"
            )


            return WAITING_FOR_SCREENSHOT


        # =================================================
        # UTR
        # =================================================

        found_utr = extract_utr(
            normalized_text
        )


        print(
            "FOUND UTR:",
            found_utr
        )


        # =================================================
        # DUPLICATE UTR
        # =================================================

        if found_utr:

            if found_utr in USED_UTRS:

                await processing_msg.edit_text(

                    "❌ **Payment Rejected!**\n\n"

                    "यह UTR पहले ही इस्तेमाल हो चुका है।\n\n"

                    "कृपया नया payment करें।",

                    parse_mode="Markdown"

                )

                return WAITING_FOR_SCREENSHOT


        # =================================================
        # SAVE UTR
        # =================================================

        if found_utr:

            USED_UTRS.add(
                found_utr
            )


        # =================================================
        # VERIFIED
        # =================================================

        await processing_msg.edit_text(

            "✅ **Payment Verify हो गया!**\n\n"

            "⏳ आपका premium content भेजा जा रहा है...",

            parse_mode="Markdown"

        )


        # =================================================
        # ADMIN NOTIFICATION
        # =================================================

        await send_admin_notification(

            context=context,

            user=user,

            plan_info=plan_info,

            utr=found_utr,

            extracted_text=extracted_text

        )


        # =================================================
        # SEND SCREENSHOT TO ADMIN
        # =================================================

        try:

            await context.bot.send_photo(

                chat_id=ADMIN_ID,

                photo=update.message.photo[-1].file_id,

                caption=(

                    "📸 **Payment Screenshot**\n\n"

                    f"👤 User ID: `{user.id}`\n"

                    f"💰 Amount: "
                    f"`{plan_info['price_str']}`\n"

                    f"🔢 UTR: "
                    f"`{found_utr or 'Not Found'}`"

                ),

                parse_mode="Markdown"

            )

        except Exception as e:

            print(
                "ADMIN PHOTO ERROR:",
                e
            )


        # =================================================
        # SEND PREMIUM VIDEO
        # =================================================

        video_message_id = (
            plan_info["video_id"]
        )


        try:

            await context.bot.copy_message(

                chat_id=user_chat_id,

                from_chat_id=VIDEO_GROUP_ID,

                message_id=video_message_id

            )

        except Exception as e:

            print(
                "VIDEO SEND ERROR:",
                e
            )


            await processing_msg.edit_text(

                "✅ Payment verify हो गया।\n\n"

                "लेकिन content भेजने में "
                "समस्या हुई। Admin को notify कर दिया गया।"

            )

            return ConversationHandler.END


        # =================================================
        # SUCCESS
        # =================================================

        await context.bot.send_message(

            chat_id=user_chat_id,

            text=(

                "🎉 **Payment Verified!**\n\n"

                f"👑 **Plan:** "
                f"{plan_info['name']}\n\n"

                f"💰 **Paid:** "
                f"{plan_info['price_str']}\n\n"

                "✅ आपकी premium access दे दी गई है।\n\n"

                "👇 आगे कुछ खरीदना हो तो:"
            ),

            parse_mode="Markdown",

            reply_markup=main_menu()

        )


        # =================================================
        # CLEAR USER DATA
        # =================================================

        context.user_data.clear()

        return ConversationHandler.END


    except Exception as e:

        import traceback

        print(
            "\n=============================="
        )

        print(
            "❌ SCREENSHOT ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "TRACEBACK:"
        )

        traceback.print_exc()

        print(
            "==============================\n"
        )

        try:

            await processing_msg.edit_text(

                "❌ Screenshot process करने में समस्या हुई।\n\n"
                "कृपया screenshot दोबारा भेजें।\n\n"
                "⚠️ Technical error log में save हो गया है।"

            )

        except Exception as edit_error:

            print(
                "PROCESSING MESSAGE ERROR:",
                repr(edit_error)
            )

        return WAITING_FOR_SCREENSHOT


# =========================================================
# TEXT DURING PAYMENT
# =========================================================

async def handle_text_during_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "❌ कृपया payment का "
        "**screenshot/photo** भेजें।",

        parse_mode="Markdown"

    )

    return WAITING_FOR_SCREENSHOT


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # TOKEN CHECK
    # =====================================================

    if (

        not BOT_TOKEN

        or
        BOT_TOKEN ==
        "PASTE_YOUR_BOT_TOKEN_HERE"

    ):

        print(
            "❌ BOT_TOKEN set नहीं है।"
        )

        return


    # =====================================================
    # OCR KEY CHECK
    # =====================================================

    if (

        not OCR_SPACE_API_KEY

        or
        OCR_SPACE_API_KEY ==
        "PASTE_YOUR_OCR_SPACE_API_KEY_HERE"

    ):

        print(
            "❌ OCR_SPACE_API_KEY set नहीं है।"
        )

        return


    # =====================================================
    # ADMIN CHECK
    # =====================================================

    if ADMIN_ID == 123456789:

        print(
            "⚠️ ADMIN_ID अभी default है।"
        )


    # =====================================================
    # APPLICATION
    # =====================================================

    app = (

        Application
        .builder()
        .token(BOT_TOKEN)
        .build()

    )


    # =====================================================
    # CONVERSATION HANDLER
    # =====================================================

    conv_handler = ConversationHandler(

        entry_points=[

            CallbackQueryHandler(

                button_handler,

                pattern=r"^plan_"

            )

        ],

        states={

            WAITING_FOR_SCREENSHOT: [

                MessageHandler(

                    filters.PHOTO,

                    handle_screenshot

                ),

                MessageHandler(

                    filters.TEXT
                    &
                    ~filters.COMMAND,

                    handle_text_during_payment

                ),

            ]

        },

        fallbacks=[

            CommandHandler(

                "start",

                start

            ),

            CallbackQueryHandler(

                button_handler,

                pattern=r"^(back_main)$"

            )

        ],

        allow_reentry=True,

        per_message=False,

    )


    # =====================================================
    # HANDLERS
    # =====================================================

    app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    app.add_handler(
        conv_handler
    )


    app.add_handler(

        CallbackQueryHandler(

            button_handler

        )

    )


    # =====================================================
    # START
    # =====================================================

    print(
        "🤖 Bot is running..."
    )


    app.run_polling(

        drop_pending_updates=True

    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()