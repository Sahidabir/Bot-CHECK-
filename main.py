import telebot
from telebot import types
import requests
import sqlite3
import threading
import time
import phonenumbers
from phonenumbers import geocoder, region_code_for_number
from flask import Flask
import os
import logging
#=================Add Flag Function=========
def get_flag(country_code):
    if not country_code:
        return ""
    return ''.join(chr(127397 + ord(c)) for c in country_code.upper())
# ================= CONFIG =================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

API_KEY = os.environ.get("API_KEY")

BASE_URL = "http://185.190.142.81/api/v1"

HEADERS = {
    "X-API-Key": API_KEY
}

OTP_GROUP = "https://t.me/otprange"

SUPPORT_LINK = "https://t.me/Fbinstabuyerh"

FORCE_CHANNEL = "gmailbuysellw2"

FORCE_GROUP = "otprange"

ADMIN_ID = 8222394658

OTP_PRICE = 0.30

REFERRAL_BONUS = 1

MIN_WITHDRAW = 150

WITHDRAW_FEE = 10

# ================= BOT =================

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ================= WEB SERVER =================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

# ================= DATABASE =================

conn = sqlite3.connect("database.db", check_same_thread=False, isolation_level=None)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    user_id INTEGER PRIMARY KEY,

    balance REAL DEFAULT 0,

    total_otp INTEGER DEFAULT 0,

    referred_by INTEGER DEFAULT 0,

    referral_count INTEGER DEFAULT 0,

    current_number TEXT,

    current_order_id TEXT,

    current_range TEXT
)
""")

conn.commit()

# ================= MAIN MENU =================

def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🚀 Start")

    markup.row("📞 Get Number", "💰 Balance")

    markup.row("👤 Profile", "📶 View Range")

    markup.row("👥 Refer", "🛟 Support")

    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    ref = 0

    args = message.text.split()

    if len(args) > 1:

        try:
            ref = int(args[1])
        except:
            ref = 0

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    exists = cursor.fetchone()

    if not exists:

        cursor.execute("""
        INSERT INTO users (
            user_id,
            referred_by
        )
        VALUES (?, ?)
        """, (user_id, ref))

        conn.commit()

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "📢 OTP Channel",
            url="https://t.me/gmailbuysellw2"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "👥 OTP And Range Group",
            url="https://t.me/otprange"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "✅ VERIFIED",
            callback_data="verified_join"
        )
    )

    bot.send_message(
        message.chat.id,
        """
🔥 Welcome To Next Level OTP Bot

⚠️ নিচের Channel/Group Join করুন
তারপর VERIFIED বাটনে ক্লিক করুন।
        """,
        reply_markup=markup
    )

# ================= VERIFIED =================

@bot.callback_query_handler(func=lambda c: c.data == "verified_join")
def verified_join(call):

    user_id = call.from_user.id

    try:

        channel = bot.get_chat_member(
            f"@{FORCE_CHANNEL}",
            user_id
        )

        group = bot.get_chat_member(
            f"@{FORCE_GROUP}",
            user_id
        )

        if channel.status in ["member", "administrator", "creator"] and group.status in ["member", "administrator", "creator"]:

            bot.send_message(
                call.message.chat.id,
                "✅ VERIFIED SUCCESSFULLY",
                reply_markup=main_menu()
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Join All Channels First"
            )

    except:

        bot.answer_callback_query(
            call.id,
            "❌ Join Required"
        )

# ================= START BUTTON =================

@bot.message_handler(func=lambda m: m.text == "🚀 Start")
def start_button(message):

    bot.send_message(
        message.chat.id,
        "🔥 BOT STARTED",
        reply_markup=main_menu()
    )

# ================= REFER =================

@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):

    user_id = message.from_user.id

    link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        f"""
👥 YOUR REFERRAL LINK

{link}

💸 RULE:

যদি আপনার রেফার করা ইউজার
মিনিমাম ৫০ টা OTP receive করে,
তাহলে আপনি পাবেন ১ টাকা।
        """
    )

# ================= GET NUMBER BUTTON =================

@bot.message_handler(func=lambda m: m.text == "📞 Get Number")
def ask_range(message):

    msg = bot.send_message(
        message.chat.id,
        "📶 ENTER RANGE ID\n\nExample:\n237620XXX"
    )

    bot.register_next_step_handler(msg, get_number)

# ================= GET NUMBER =================
def get_number(message):

    range_id = message.text.strip()
    user_id = message.from_user.id

    try:

        payload = {
            "range": range_id,
            "format": "international"
        }

        response = requests.post(
            BASE_URL + "/numbers/get",
            json=payload,
            headers=HEADERS
        )

        data = response.json()
        print("GET NUMBER:", data)

        number = data.get("number")
        number_id = data.get("number_id")

        if not number or not number_id:
            bot.send_message(
                message.chat.id,
                f"❌ NO NUMBERS FOUND\n\n{data}"
            )
            return

        # ================= AUTO COUNTRY DETECT =================
        try:
            parsed = phonenumbers.parse(str(number), None)

            country_code = region_code_for_number(parsed)
            country_name = geocoder.description_for_number(parsed, "en")
            flag = get_flag(country_code)

        except:
            country_name = "Unknown"
            flag = ""

# ================= SAVE DB =================

cursor.execute("""
UPDATE users
SET current_number=?,
    current_order_id=?,
    current_range=?
WHERE user_id=?
""", (
    number,
    number_id,
    range_id,
    user_id
))

conn.commit()

print("ORDER SAVED:", user_id, number_id)

# ================= AUTO OTP =================

def auto_check_otp(chat_id, number_id, range_id, number):

    for i in range(60):

        try:

            response = requests.get(
                BASE_URL + f"/numbers/{number_id}/sms",
                headers=HEADERS,
                timeout=15
            )

            data = response.json()

            print("AUTO OTP RESPONSE:", data)

            otp = data.get("otp")

            if otp:

                # ================= BALANCE UPDATE =================

                cursor.execute("""
                    UPDATE users
                    SET balance = balance + ?,
                        total_otp = total_otp + 1
                    WHERE user_id = ?
                """, (OTP_PRICE, chat_id))

                conn.commit()


                # ================= USER INFO =================

cursor.execute("""
    SELECT balance, total_otp, referred_by
    FROM users
    WHERE user_id = ?
""", (chat_id,))

info = cursor.fetchone()

# USER NOT FOUND FIX
if not info:

    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
    """, (chat_id,))

    conn.commit()

    current_balance = 0
    total_otp = 0
    referred_by = 0

else:

    current_balance = info[0]
    total_otp = info[1]
    referred_by = info[2]
                
                # ================= REFERRAL BONUS =================

                if total_otp == 50 and referred_by != 0:

                    cursor.execute("""
                        UPDATE users
                        SET balance = balance + ?,
                            referral_count = referral_count + 1
                        WHERE user_id = ?
                    """, (REFERRAL_BONUS, referred_by))

                    conn.commit()

                # ================= BUTTONS =================

                markup = types.InlineKeyboardMarkup()

                markup.row(
                    types.InlineKeyboardButton(
                        text=f"📋 COPY OTP : {otp}",
                        copy_text=types.CopyTextButton(
                            text=str(otp)
                        )
                    )
                )

                markup.row(
                    types.InlineKeyboardButton(
                        "📞 Another Number With This Range",
                        callback_data=f"another_{range_id}"
                    )
                )

                # ================= SEND USER =================

                bot.send_message(
                    chat_id,
                    f"""
✅ OTP RECEIVED

📋 OTP: `{otp}`

💸 OTP Income: +{OTP_PRICE} TK

💰 Your Balance: {current_balance:.2f} TK
                    """,
                    parse_mode="Markdown",
                    reply_markup=markup
                )

                # ================= SEND GROUP =================

                group_markup = types.InlineKeyboardMarkup()

                group_markup.row(
                    types.InlineKeyboardButton(
                        "📞 Get Number For This Range",
                        url=f"https://t.me/{bot.get_me().username}?start=range_{range_id}"
                    )
                )

                bot.send_message(
                    f"@{FORCE_GROUP}",
                    f"""
🔥 {bot.get_me().first_name}

📞 Number: {number}

📶 Range: {range_id}

📋 OTP: {otp}

💰 Earned: {OTP_PRICE} TK
                    """,
                    reply_markup=group_markup
                )

                # ================= CLEAR ACTIVE ORDER =================

                cursor.execute("""
                    UPDATE users
                    SET current_order_id = NULL
                    WHERE user_id = ?
                """, (chat_id,))

                conn.commit()

                return

            time.sleep(5)

        except Exception as e:

            print("AUTO OTP ERROR:", e)

            time.sleep(5)


# ================= REFRESH OTP =================

@bot.callback_query_handler(func=lambda c: c.data == "refresh_otp")
def refresh_otp(call):

    user_id = call.from_user.id

    try:

        cursor.execute("""
            SELECT current_order_id
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()

        print("DB RESULT:", result)

        # ================= NO ACTIVE =================

        if not result or not result[0]:

            bot.answer_callback_query(
                call.id,
                "❌ No Active Number"
            )

            return

        number_id = result[0]

        print("NUMBER ID:", number_id)

        # ================= REQUEST =================

        response = requests.get(
            BASE_URL + f"/numbers/{number_id}/sms",
            headers=HEADERS,
            timeout=15
        )

        data = response.json()

        print("REFRESH OTP RESPONSE:", data)

        otp = data.get("otp")

        # ================= OTP FOUND =================

        if otp:

            markup = types.InlineKeyboardMarkup()

            markup.row(
                types.InlineKeyboardButton(
                    text=f"📋 COPY OTP : {otp}",
                    copy_text=types.CopyTextButton(
                        text=str(otp)
                    )
                )
            )

            bot.send_message(
                call.message.chat.id,
                f"""
✅ OTP RECEIVED

📋 OTP: `{otp}`
                """,
                parse_mode="Markdown",
                reply_markup=markup
            )

        else:

            bot.answer_callback_query(
                call.id,
                "⌛ OTP Not Received Yet"
            )

    except Exception as e:

        print("REFRESH OTP ERROR:", e)

        bot.send_message(
            call.message.chat.id,
            f"❌ ERROR\n\n{e}"
        )

# ================= CHANGE NUMBER =================

@bot.callback_query_handler(func=lambda c: c.data == "change_number")
def change_number(call):

    user_id = call.from_user.id

    cursor.execute("""
    SELECT current_range
    FROM users
    WHERE user_id=?
    """, (user_id,))

    result = cursor.fetchone()

    if not result:
        return

    range_id = result[0]

    class Fake:
        pass

    fake = Fake()

    fake.text = range_id
    fake.chat = call.message.chat
    fake.from_user = call.from_user

    get_number(fake)

# ================= ANOTHER NUMBER =================

@bot.callback_query_handler(func=lambda c: c.data.startswith("another_"))
def another_number(call):

    range_id = call.data.split("_")[1]

    class Fake:
        pass

    fake = Fake()

    fake.text = range_id
    fake.chat = call.message.chat
    fake.from_user = call.from_user

    get_number(fake)
# ================= ADMIN BROADCAST =================

broadcast_mode = {}

# ===== COMMAND =====

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):

    if message.from_user.id != ADMIN_ID:
        return

    broadcast_mode[message.from_user.id] = True

    bot.reply_to(
        message,
        "📢 Send Text / Photo / Video"
    )

# ===== TEXT =====

@bot.message_handler(func=lambda m: m.from_user.id in broadcast_mode and m.content_type == "text")
def broadcast_text(message):

    if message.text.startswith("/broadcast"):
        return

    send_all_users(message)

# ===== PHOTO =====

@bot.message_handler(content_types=['photo'])
def broadcast_photo(message):

    if message.from_user.id in broadcast_mode:
        send_all_users(message)

# ===== VIDEO =====

@bot.message_handler(content_types=['video'])
def broadcast_video(message):

    if message.from_user.id in broadcast_mode:
        send_all_users(message)

# ===== DOCUMENT =====

@bot.message_handler(content_types=['document'])
def broadcast_document(message):

    if message.from_user.id in broadcast_mode:
        send_all_users(message)

# ===== SEND FUNCTION =====

def send_all_users(message):

    cursor.execute("""
    SELECT user_id
    FROM users
    """)

    users = cursor.fetchall()

    total = 0
    failed = 0

    for user in users:

        user_id = user[0]

        try:

            # ===== TEXT =====
            if message.content_type == "text":

                bot.send_message(
                    user_id,
                    message.text
                )

            # ===== PHOTO =====
            elif message.content_type == "photo":

                bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption
                )

            # ===== VIDEO =====
            elif message.content_type == "video":

                bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption
                )

            # ===== DOCUMENT =====
            elif message.content_type == "document":

                bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption
                )

            total += 1

            time.sleep(0.05)

        except Exception as e:

            failed += 1

            print(e)

    broadcast_mode.pop(message.from_user.id, None)

    bot.send_message(
        message.chat.id,
        f"""
✅ Broadcast Completed

👥 Success: {total}

❌ Failed: {failed}
        """
    )


# ================= PROFILE =================

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):

    user_id = message.from_user.id

    cursor.execute("""
    SELECT balance,
           total_otp,
           referral_count
    FROM users
    WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if data is None:

        cursor.execute("""
        INSERT INTO users (user_id)
        VALUES (?)
        """, (user_id,))

        conn.commit()

        balance = 0
        total_otp = 0
        referral_count = 0

    else:

        balance = data[0]
        total_otp = data[1]
        referral_count = data[2]

    user = message.from_user

    bot.send_message(
        message.chat.id,
        f"""
👤 PROFILE

🆔 ID: {user.id}

👤 NAME: {user.first_name}

📛 USERNAME: @{user.username}

💰 BALANCE: {balance:.2f} TK

📩 TOTAL OTP: {total_otp}

👥 REFERRALS: {referral_count}
        """
    )
#===================BALANCE = =================

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):

    user_id = message.from_user.id

    cursor.execute("""
    SELECT balance,
           total_otp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if data is None:

        cursor.execute("""
        INSERT INTO users (user_id)
        VALUES (?)
        """, (user_id,))

        conn.commit()

        balance = 0
        total_otp = 0

    else:

        balance = data[0]
        total_otp = data[1]

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "💸 Withdraw",
            callback_data="withdraw"
        )
    )

    bot.send_message(
        message.chat.id,
        f"""
💰 YOUR BALANCE

💵 Balance: {balance:.2f} TK

📩 Total OTP: {total_otp}

💸 Per OTP = {OTP_PRICE} TK
        """,
        reply_markup=markup
    )


#==================WITHDRAW = =================

@bot.callback_query_handler(func=lambda c: c.data == "withdraw")
def withdraw(call):

    user_id = call.from_user.id

    cursor.execute("""
    SELECT balance
    FROM users
    WHERE user_id=?
    """, (user_id,))

    balance = cursor.fetchone()[0]

    if balance < MIN_WITHDRAW:

        bot.answer_callback_query(
            call.id,
            f"❌ Minimum Withdraw {MIN_WITHDRAW} TK"
        )

        return

    msg = bot.send_message(
        call.message.chat.id,
        "💸 SEND YOUR BKASH NUMBER"
    )

    bot.register_next_step_handler(
        msg,
        process_withdraw
    )

# ================= PROCESS WITHDRAW =================

def process_withdraw(message):

    bkash = message.text

    user_id = message.from_user.id

    cursor.execute("""
    SELECT balance
    FROM users
    WHERE user_id=?
    """, (user_id,))

    balance = cursor.fetchone()[0]

    final_amount = balance - WITHDRAW_FEE

    bot.send_message(
        message.chat.id,
        f"""
✅ WITHDRAW REQUEST SENT

📱 BKASH: {bkash}

💵 Amount: {final_amount:.2f} TK

⚠️ Withdraw Fee: {WITHDRAW_FEE} TK
        """
    )

    cursor.execute("""
    UPDATE users
    SET balance=0
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    bot.send_message(
        ADMIN_ID,
        f"""
💸 NEW WITHDRAW

👤 USER: {user_id}

📱 BKASH: {bkash}

💵 AMOUNT: {final_amount:.2f} TK
        """
    )

# ================= VIEW RANGE =================

@bot.message_handler(func=lambda m: m.text == "📶 View Range")
def view_range(message):

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "📶 OPEN RANGE GROUP",
            url=OTP_GROUP
        )
    )

    bot.send_message(
        message.chat.id,
        "🔥 CLICK BUTTON BELOW TO VIEW ACTIVE RANGE",
        reply_markup=markup
    )

# ================= SUPPORT =================

@bot.message_handler(func=lambda m: m.text == "🛟 Support")
def support(message):

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "🛟 CONTACT ADMIN",
            url=SUPPORT_LINK
        )
    )

    bot.send_message(
        message.chat.id,
        "Need Help?",
        reply_markup=markup
    )


# ================= RUN BOT =================

print("BOT RUNNING...")

def start_bot():
    while True:
        try:
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )
        except Exception as e:
            print(e)
            time.sleep(5)

threading.Thread(target=start_bot).start()

port = int(os.environ.get("PORT", 10000))

app.run(host="0.0.0.0", port=port)
