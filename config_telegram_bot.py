import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
import json
import jdatetime

# Replace the following values with your own information
TOKEN = '5688155667:AAFRToj9g0SeThFVfNB18MAhIoJDE0nPR-0'

def start(update, context):

    keyboard = [
        [KeyboardButton("Expiration Date")],
        [KeyboardButton("Traffic used")],
        [KeyboardButton("Total Traffic")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Press a button:", reply_markup=reply_markup)

def button_callback(update, context):
    """Handles button callback query"""
    conn = sqlite3.connect('/etc/x-ui/x-ui.db')
    # conn = sqlite3.connect('C:\\Users\\vbahramian\\Desktop\\x-ui.db')
    cursor = conn.cursor()
    emails = GetAllEmail(cursor)
    text = update.message.text
    username = update.message.from_user.username
    email = [dictionary[username] for dictionary in emails if username in dictionary]
    if len(email) > 0:
        for e in email:
            if text == 'Expiration Date':
                cursor.execute("SELECT expiry_time FROM client_traffics WHERE email= ?", (str(e),))
                expiry_time = cursor.fetchone()
                if expiry_time[0] > 0:
                    jalali_datetime = jdatetime.datetime.fromtimestamp(expiry_time[0] / 1000).date()
                    year = jalali_datetime.year
                    month = jalali_datetime.month
                    day = jalali_datetime.day
                    current_date = jdatetime.datetime.now().date()
                    date_difference = jalali_datetime - current_date
                    update.message.reply_text(f"{str(e)}: {year}/{month}/{day} (Days left: {date_difference.days})")
                else:
                    update.message.reply_text(f"{str(e)}: Unlimited")
            elif text == 'Traffic used':
                cursor.execute("SELECT up,down FROM client_traffics WHERE email= ?", (str(e),))
                traffic_used = cursor.fetchone()
                update.message.reply_text(str(e) + ": " + str(round(((traffic_used[0] + traffic_used[1]) / 1024 / 1024 / 1024), 2)) + " GB")
            elif text == 'Total Traffic':
                cursor.execute("SELECT total FROM client_traffics WHERE email= ?", (str(e),))
                total = cursor.fetchone()
                if total[0] > 0:
                    update.message.reply_text(str(e) + ": " + str(round((total[0] / 1024 / 1024 / 1024), 2)) + " GB")
                else:
                    update.message.reply_text(f"{str(e)}: Unlimited")
    else:
        if text == 'تعرفه ها':
            update.message.reply_document(document=open('/root/VPN.pdf', 'rb'))

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
def main():
    """Starts the Telegram bot"""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
