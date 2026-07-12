import os
import time
import sqlite3
import threading
import requests
import telebot

from telebot import types

# ================= CONFIG =================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

API_KEY = "nxa_9f1208cee0f2cd50cdc197bd814eb95e83bc0636"

BASE_URL = "http://nexaotpservice.com/api/v1"

HEADERS = {
    "X-API-Key": API_KEY
}

OTP_GROUP = "https://t.me/otprange"

OTP_CHANNEL = "https://t.me/gmailbuysellw2"

SUPPORT_LINK = "https://t.me/Fbinstabuyerh"

FORCE_CHANNEL = "gmailbuysellw2"

FORCE_GROUP = "otprange"

ADMIN_ID = 123456789

OTP_PRICE = 0.30

REFERRAL_BONUS = 1.00

MIN_WITHDRAW = 150

WITHDRAW_FEE = 10

# ================= BOT =================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ================= DATABASE =================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

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

# ================= MENU =================

def main_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row("🚀 Start")

    markup.row(
        "📞 Get Number",
        "💰 Balance"
    )

    markup.row(
        "👤 Profile",
        "📶 View Range"
    )

    markup.row(
        "👥 Refer",
        "🛟 Support"
    )

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

    if cursor.fetchone() is None:

        cursor.execute("""
        INSERT INTO users(
            user_id,
            referred_by
        )
        VALUES(?,?)
        """, (user_id, ref))

        conn.commit()

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📢 OTP Channel",
            url=OTP_CHANNEL
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "👥 OTP And Range Group",
            url=OTP_GROUP
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "✅ VERIFIED",
            callback_data="verified_join"
        )
    )

    bot.send_message(
        message.chat.id,
        "🔥 Welcome To Next Level OTP Bot\n\n"
        "⚠️ প্রথমে Channel এবং Group Join করুন,\n"
        "তারপর VERIFIED বাটনে ক্লিক করুন।",
        reply_markup=markup
    )


# ================= VERIFY =================

@bot.callback_query_handler(func=lambda c: c.data == "verified_join")
def verified_join(call):

    try:

        user_id = call.from_user.id

        channel = bot.get_chat_member(
            f"@{FORCE_CHANNEL}",
            user_id
        )

        group = bot.get_chat_member(
            f"@{FORCE_GROUP}",
            user_id
        )

        if channel.status not in [
            "member",
            "administrator",
            "creator"
        ]:
            bot.answer_callback_query(
                call.id,
                "❌ OTP Channel Join করুন"
            )
            return

        if group.status not in [
            "member",
            "administrator",
            "creator"
        ]:
            bot.answer_callback_query(
                call.id,
                "❌ OTP Group Join করুন"
            )
            return

        bot.send_message(
            call.message.chat.id,
            "✅ Verification Successful",
            reply_markup=main_menu()
        )

    except Exception as e:

        bot.answer_callback_query(
            call.id,
            "❌ আগে Channel এবং Group Join করুন"
        )

        print(e)


# ================= START BUTTON =================

@bot.message_handler(func=lambda m: m.text == "🚀 Start")
def start_button(message):

    start(message)


# ================= REFER =================

@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):

    user_id = message.from_user.id

    username = bot.get_me().username

    link = f"https://t.me/{username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        f"""
👥 *Your Referral Link*

{link}

💰 যদি আপনার Referral User
৫০টি OTP Receive করে,
তাহলে আপনি *১ টাকা Bonus* পাবেন।
        """,
        parse_mode="Markdown"
    )
  # ================= GET NUMBER =================

@bot.message_handler(func=lambda m: m.text == "📞 Get Number")
def ask_range(message):

    msg = bot.send_message(
        message.chat.id,
        "📶 Enter Range\n\nExample:\n237620XXX"
    )

    bot.register_next_step_handler(msg, get_number)


def get_number(message):

    range_id = message.text.strip()
    user_id = message.from_user.id

    try:

        payload = {
            "range": range_id,
            "format": "national"
        }

        response = requests.post(
            BASE_URL + "/numbers/get",
            json=payload,
            headers=HEADERS,
            timeout=20
        )

        data = response.json()

        print("GET NUMBER:", data)

        number = data.get("number")
        number_id = data.get("number_id")

        if not number or not number_id:

            bot.send_message(
                message.chat.id,
                f"❌ No Number Found\n\n{data}"
            )
            return

        if not str(number).startswith("+"):
            number = "+" + str(number)

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

        markup = types.InlineKeyboardMarkup(row_width=2)

        markup.add(
            types.InlineKeyboardButton(
                "🔄 Change Number",
                callback_data="change_number"
            ),
            types.InlineKeyboardButton(
                "♻️ Refresh OTP",
                callback_data="refresh_otp"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "👥 OTP Group",
                url=OTP_GROUP
            )
        )

        bot.send_message(
            message.chat.id,
            f"""📞 *NUMBER:* `{number}`

🆔 *ID:* `{number_id}`

📶 *RANGE:* `{range_id}`

💸 OTP নিয়ে পাবেন *০.৩০ টাকা*
""",
            parse_mode="Markdown",
            reply_markup=markup
        )

        threading.Thread(
            target=auto_check_otp,
            args=(
                message.chat.id,
                number_id,
                range_id,
                number
            ),
            daemon=True
        ).start()

    except Exception as e:

        bot.send_message(
            message.chat.id,
            f"❌ Error\n\n{e}"
        )
      # ===== REFERRAL BONUS =====

                if total_otp == 50 and referred_by != 0:

                    cursor.execute("""
                    UPDATE users
                    SET balance = balance + ?,
                        referral_count = referral_count + 1
                    WHERE user_id = ?
                    """, (REFERRAL_BONUS, referred_by))

                    conn.commit()

                # ===== BUTTON =====

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

                # ===== USER MESSAGE =====

                bot.send_message(
                    chat_id,
                    f"""
✅ OTP RECEIVED

📋 OTP:
`{otp}`

💸 OTP Income: +{OTP_PRICE} TK

💰 Your Balance: {current_balance:.2f} TK
                    """,
                    parse_mode="Markdown",
                    reply_markup=markup
                )

                # ===== SEND TO GROUP =====

                bot.send_message(
                    f"@{FORCE_GROUP}",
                    f"""
🔥 {bot.get_me().first_name}

📞 Number: {number}

📶 Range: {range_id}

📋 OTP:
{otp}

💰 Earn: +{OTP_PRICE} TK
                    """
                )

                return

            time.sleep(5)

        except Exception as e:

            print("AUTO OTP ERROR:", e)
            time.sleep(5)
# ===== CLEAR ACTIVE ORDER =====

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

    cursor.execute("""
    SELECT current_order_id
    FROM users
    WHERE user_id=?
    """, (user_id,))

    result = cursor.fetchone()

    if not result or not result[0]:

        bot.answer_callback_query(
            call.id,
            "❌ No Active Number"
        )
        return

    number_id = result[0]

    try:

        response = requests.get(
            BASE_URL + f"numbers/{number_id}/sms",
            headers=HEADERS,
            timeout=15
        )

        data = response.json()

        print("REFRESH OTP:", data)

        otp = data.get("otp")

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

📋 OTP:
`{otp}`
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

    if not result or not result[0]:
        bot.answer_callback_query(call.id, "❌ No Active Range")
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

    range_id = call.data.replace("another_", "")

    class Fake:
        pass

    fake = Fake()
    fake.text = range_id
    fake.chat = call.message.chat
    fake.from_user = call.from_user

    get_number(fake)
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
        balance = 0
        total_otp = 0
        referral_count = 0
    else:
        balance = data[0]
        total_otp = data[1]
        referral_count = data[2]

    user = message.from_user

    username = f"@{user.username}" if user.username else "No Username"

    bot.send_message(
        message.chat.id,
        f"""
👤 PROFILE

🆔 ID: {user.id}

👤 NAME: {user.first_name}

📛 USERNAME: {username}

💰 BALANCE: {balance:.2f} TK

📩 TOTAL OTP: {total_otp}

👥 REFERRALS: {referral_count}
        """
    )


# ================= BALANCE =================

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):

    user_id = message.from_user.id

    cursor.execute("""
    SELECT balance,total_otp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if data is None:
        balance = 0
        total_otp = 0
    else:
        balance = data[0]
        total_otp = data[1]

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "💸 Withdraw",
            callback_data="withdraw"
        )
    )

    bot.send_message(
        message.chat.id,
        f"""
💰 YOUR BALANCE

💵 Balance : {balance:.2f} TK

📩 Total OTP : {total_otp}

💸 Per OTP : {OTP_PRICE} TK
        """,
        reply_markup=markup
    )


# ================= WITHDRAW =================

@bot.callback_query_handler(func=lambda c: c.data == "withdraw")
def withdraw(call):

    user_id = call.from_user.id

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    balance = row[0] if row else 0

    if balance < MIN_WITHDRAW:

        bot.answer_callback_query(
            call.id,
            f"❌ Minimum Withdraw {MIN_WITHDRAW} TK"
        )
        return

    msg = bot.send_message(
        call.message.chat.id,
        "💳 আপনার বিকাশ নম্বর পাঠান"
    )

    bot.register_next_step_handler(
        msg,
        process_withdraw
    )
# ================= PROCESS WITHDRAW =================

def process_withdraw(message):

    bkash = message.text.strip()

    user_id = message.from_user.id

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    if not row:
        bot.send_message(message.chat.id, "❌ User not found.")
        return

    balance = row[0]
    final_amount = balance - WITHDRAW_FEE

    cursor.execute(
        "UPDATE users SET balance=0 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()

    bot.send_message(
        message.chat.id,
        f"""
✅ Withdraw Request Submitted

📱 Bkash : {bkash}

💵 Amount : {final_amount:.2f} TK

💸 Fee : {WITHDRAW_FEE} TK
        """
    )

    try:
        bot.send_message(
            ADMIN_ID,
            f"""
💸 NEW WITHDRAW REQUEST

👤 User ID : {user_id}

📱 Bkash : {bkash}

💵 Amount : {final_amount:.2f} TK
            """
        )
    except Exception as e:
        print("Admin message error:", e)


# ================= VIEW RANGE =================

@bot.message_handler(func=lambda m: m.text == "📶 View Range")
def view_range(message):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📶 OTP & Range Group",
            url=OTP_GROUP
        )
    )

    bot.send_message(
        message.chat.id,
        "👇 Click the button below",
        reply_markup=markup
    )


# ================= SUPPORT =================

@bot.message_handler(func=lambda m: m.text == "🛟 Support")
def support(message):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "🛟 Contact Admin",
            url=SUPPORT_LINK
        )
    )

    bot.send_message(
        message.chat.id,
        "Need any help? Contact the admin.",
        reply_markup=markup
    )


# ================= RUN BOT =================

print("✅ BOT STARTED")

bot.infinity_polling(
    timeout=30,
    long_polling_timeout=30,
    skip_pending=True
)
