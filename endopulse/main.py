from datetime import datetime, time, timedelta
import csv
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ContextTypes, ApplicationBuilder, Application, CallbackQueryHandler, CommandHandler, ContextTypes
import os
import pytz
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

import random
from telegram.ext import Updater, CommandHandler, CallbackContext

TIMEZONE = pytz.timezone("Asia/Singapore")

DATA_DIR = Path('data')
WRITE_FILE = DATA_DIR / 'mood_data.csv'

Path('data').mkdir(parents=True, exist_ok=True)
if not os.path.exists(WRITE_FILE):
    with open('data/mood_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'mood'])

# Initialize your bot with the token provided by BotFather
bot_token = os.environ['ENDOPULSE_TELEGRAM_TOKEN']
bot = telegram.Bot(token=bot_token)

# Function to ask mood
async def ask_mood(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
            InlineKeyboardButton("3", callback_data="3"),
            InlineKeyboardButton("4", callback_data="4"),
            InlineKeyboardButton("5", callback_data="5"),
        ],
        [
            InlineKeyboardButton("6", callback_data="6"),
            InlineKeyboardButton("7", callback_data="7"),
            InlineKeyboardButton("8", callback_data="8"),
            InlineKeyboardButton("9", callback_data="9"),
            InlineKeyboardButton("❌", callback_data="cancel"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    job = context.job
    await context.bot.send_message(job.chat_id, text="Please choose:", reply_markup=reply_markup)

# Handler for receiving mood response
def handle_response(update, context):
    user_mood = update.message.text
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Write to CSV
    with open('mood_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, user_mood])


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def schedule_for_day(context: CallbackContext):
    n = 3
    chat_id = context.job.chat_id
    # 9am to 2am next day in datetime

    t1 = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    t2 = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
    for _ in range(n):
        # pick random time between t1 and t2
        t = t1 + random.random() * (t2 - t1)
        print(f'scheduling for {t}')
        context.job_queue.run_once(ask_mood, t, chat_id=chat_id, name=str(chat_id))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Welcome."
    chat_id = update.message.chat_id
    await update.message.reply_text("I'll help you track your mood, 3 times a day from 9am to 2am the next day.")
    # job = context.job_queue.run_runonce(ask_mood, due, chat_id=chat_id, name=str(chat_id), data=due)
    # use singapore timezone
    context.job_queue.run_daily(
        callback=schedule_for_day,
        days=(0, 1, 2, 3, 4, 5, 6),
        time=time(hour=8, minute=0, second=0, tzinfo=TIMEZONE),
        chat_id=chat_id,
        name=str(chat_id)
    )

    context.job_queue.run_once(ask_mood, 5, chat_id=chat_id, name=str(chat_id))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    mood = query.data

    await query.edit_message_text(text=f"Feeling like {mood}. Thanks!")

    timestamp = str(datetime.now())

    with open(WRITE_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, mood])


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")

async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = 5

        job = context.job_queue.run_once(ask_mood, due, chat_id=chat_id, name=str(chat_id), data=due)
        context.chat_data["job"] = job

        update.message.reply_text(f"Timer successfully set for {due} seconds!")

    except (IndexError, ValueError):
        update.message.reply_text("Usage: /set <seconds>")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_timer))

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()