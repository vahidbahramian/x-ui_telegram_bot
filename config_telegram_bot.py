import datetime
import time

import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update, CallbackQuery
from telegram.ext import CallbackQueryHandler
import sqlite3
import json
import jdatetime
from telethon import TelegramClient
import socks
import asyncio
import os
# Replace 'API_ID' and 'API_HASH' with your actual API ID and hash
api_id = '7993438'
api_hash = '4b6a1b11e8ccd4439fde7248a588b5c4'

# Replace 'PHONE_NUMBER' with your phone number
phone_number = '+98 999 986 4029'
# TOKEN = '5688155667:AAFRToj9g0SeThFVfNB18MAhIoJDE0nPR-0'

TOKEN = "6533627389:AAGzwn3BQ_ypZWkQhhwvLQ252ImyzAMvYmk"

def start(update: Update, context: CallbackQuery):
    keyboard = [
        [InlineKeyboardButton("تمدید اکانت", callback_data='account_renewal'),
         InlineKeyboardButton("خرید اکانت جدید", callback_data='buy_account')],
        [InlineKeyboardButton("بررسی حجم و زمان باقی مانده", callback_data='account_inquiry')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Press a button:", reply_markup=reply_markup)

request_count = 0

def button_callback(update, context):
    """Handles button callback query"""
    query = update.callback_query
    text = query.data
    if text == "account_inquiry":
        global request_count
        # conn = sqlite3.connect('/etc/x-ui/x-ui.db')
        # conn = sqlite3.connect('C:\\Users\\vbahramian\\Desktop\\x-ui.db')
        conn = sqlite3.connect('/home/vahid/x-ui.db')
        cursor = conn.cursor()
        emails = GetAllEmail(cursor)
        username = query.from_user.username
        email = [dictionary[username] for dictionary in emails if username in dictionary]
        if len(email) > 0:
            for e in email:
                request_count = request_count + 1
                print(request_count, email, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), flush=True)
                cursor.execute("SELECT expiry_time, up, down, total FROM client_traffics WHERE email= ?",
                               (str(e),))
                row = cursor.fetchone()
                message = f"اکانت:\n{e}\n"
                if row[0] > 0:
                    jalali_datetime = jdatetime.datetime.fromtimestamp(row[0] / 1000).date()
                    year = jalali_datetime.year
                    month = jalali_datetime.month
                    day = jalali_datetime.day
                    current_date = jdatetime.datetime.now().date()
                    date_difference = jalali_datetime - current_date
                    message += f"تاریخ اتمام:\n{year}/{month}/{day}\n"
                    message += f"تعداد روزهای باقی مانده: {date_difference.days}"
                else:
                    message += "تاریخ اتمام: نامحدود\n"
                traffic_used = str(round(((row[1] + row[2]) / 1024 / 1024 / 1024), 2)) + " GB"
                if row[3] > 0:
                    total_traffic = str(round((row[3] / 1024 / 1024 / 1024), 2)) + " GB"
                    message += f"حجم مصرف شده:\n{traffic_used}/{total_traffic}"
                else:
                    message += f"حجم مصرف شده:\n{traffic_used}/Unlimited"
                context.bot.send_message(chat_id=query.message.chat_id, text=message)
    elif text == "account_renewal":
        # conn = sqlite3.connect('/etc/x-ui/x-ui.db')
        conn = sqlite3.connect('/home/vahid/x-ui.db')
        cursor = conn.cursor()
        emails = GetAllEmail(cursor)
        username = query.from_user.username
        email = [dictionary[username] for dictionary in emails if username in dictionary]
        if len(email) == 0:
            query.answer(text="شما اکانتی ندارید 😞 کانفیگ جدید خریداری کنید")
        else:
            keyboard = []
            for e in email:
                k = [InlineKeyboardButton( f"{e}", callback_data=f'us_account:{e}')]
                keyboard.append(k)
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=query.message.chat_id, text="Your Account:", reply_markup=reply_markup)
    elif "us_account" in text:
        acc = text.split(":")[1]


def GetAllEmail(cursor):
    # Execute a SELECT query to fetch the desired column
    cursor.execute("SELECT settings FROM inbounds")

    # Fetch all rows from the result
    rows = cursor.fetchall()

    # Extract the column values from each row
    json_values = []
    for row in rows:
        json_value = json.loads(row[0])
        json_values.append(json_value)

    result = []
    # Print the JSON values
    for value in json_values:
        for v in value["clients"]:
            if "tgId" in v:
                key_values = {}
                key_value = v["tgId"]
                key_values[key_value] = v["email"]
                result.append(key_values)
    return result


file_path = 'sended_message.txt'
def GetExpireUser(cursor):
    cursor.execute("SELECT inbound_id, enable, email, up, down, expiry_time, total FROM client_traffics WHERE inbound_id = 39")
    rows = cursor.fetchall()

    for row in rows:
        inbound_id = row[0]
        enable = row[1]
        email = row[2]
        up = row[3]
        down = row[4]
        expiry_time = row[5]
        total = row[6]
        my_list = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    my_list = file.readlines()
                except:
                    pass
        s = [string.strip() for string in my_list]
        my_list = list(filter(lambda x: x != '', s))
        users = my_list
        if enable == 1:
            now = time.time()
            if expiry_time > 0 and (expiry_time < (now + (86400 * 3)) * 1000):
                remind_days = round(((expiry_time / 1000) - now) / 86400)
                if email not in users:
                    my_list.append(email)
                    with open(file_path, 'w') as file:
                        for string in my_list:
                            file.write(f"{string}\n")
                    message = f"⚠️ اکانت شما {remind_days} روز دیگر منقضی می شود.\n\n✅️ لطفا برای شارژ مجدد اکانت خود اقدام نمایید.\n\nاکانت: {email}"
                    return {"email": email, "message": message}
            elif total > 0 and (up + down > total - (1 * 1024 * 1024 * 1024)): # 1 GB
                if email not in users:
                    my_list.append(email)
                    with open(file_path, 'w') as file:
                        for string in my_list:
                            file.write(f"{string}\n")
                    message = f" تنها ۱ گیگا بایت دیگر از ترافیک مصرفی شما باقی مانده است و شارژ اکانت شما به زودی به پایان می‌رسد.\n\n✅️ لطفا برای شارژ مجدد اکانت خود اقدام نمایید.\n\nاکانت: {email}"
                    return {"email": email, "message": message}
            else:
                if email in users:
                    my_list.remove(email)
                    with open(file_path, 'w') as file:
                        for string in my_list:
                            file.write(f"{string}\n")
        else:
            if email in users:
                my_list.remove(email)
                with open(file_path, 'w') as file:
                    for string in my_list:
                        file.write(f"{string}\n")
                message = f"❌️ شارژ اکانت شما به اتمام رسیده است.\n\n✅️ لطفا برای شارژ مجدد اکانت خود اقدام نمایید.\n\nاکانت: {email}"
                return {"email": email, "message": message}
    return None
def get_tgId_expire(exp, tgId_emails):
    for my_dict in tgId_emails:
        for key, value in my_dict.items():
            if value == exp['email']:
                return key
    return None
async def send_telegram_message(tgId, exp):
    # async with TelegramClient('VPN7007', api_id, api_hash, proxy=(socks.HTTP, '127.0.0.1', 8889, True)) as client:
    async with TelegramClient('VPN7007', api_id, api_hash) as client:
        if not await client.is_user_authorized():
            client.send_code_request(phone_number)
            client.sign_in(phone_number, input('Enter the code: '))
        username = tgId
        message_text = exp['message']
        await client.send_message(username, message_text)
        await client.send_message("vahidbahramian", message_text)
def check_expiration_time(context):
    conn = sqlite3.connect('/etc/x-ui/x-ui.db')
    # conn = sqlite3.connect('C:\\Users\\vbahramian\\Desktop\\x-ui.db')
    # conn = sqlite3.connect('/home/vahid/x-ui.db')
    cursor = conn.cursor()
    tgId_emails = GetAllEmail(cursor)
    exp = GetExpireUser(cursor)
    if exp is not None:
        tgId = get_tgId_expire(exp, tgId_emails)
        if tgId is not None:
            asyncio.run(send_telegram_message(tgId, exp))


def main():
    """Starts the Telegram bot"""
    Proxy_Url = {'proxy_url': 'socks5h://localhost:1080'}
    updater = Updater(TOKEN, request_kwargs=Proxy_Url, use_context=True)
    # updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_callback))
    # updater.job_queue.run_repeating(check_expiration_time, interval=60, first=0, context=0,
    #                                 name="check_expiration_time")
    updater.start_polling()
    updater.idle()

    # conn = sqlite3.connect('/home/vahid/x-ui.db')
    # # conn = sqlite3.connect('C:\\Users\\vbahramian\\Desktop\\x-ui.db')
    # cursor = conn.cursor()
    # tgId_emails = GetAllEmail(cursor)
    # exp = GetExpireUser(cursor)
    # if exp is not None:
    #     tgId = get_tgId_expire(exp, tgId_emails)
    #     if tgId is not None:
    #         client = TelegramClient('VPN7007', api_id, api_hash, proxy=(socks.HTTP, '127.0.0.1', 8889, True))
    #         client.connect()
    #         if not client.is_user_authorized():
    #             client.send_code_request(phone_number)
    #             client.sign_in(phone_number, input('Enter the code: '))
    #         username = tgId
    #         message_text = exp['message']
    #         client.send_message(username, message_text)
    #         client.disconnect()
if __name__ == '__main__':
    main()
