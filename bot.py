import logging
import json
import random
import os
import tempfile
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from telegram.error import BadRequest, TelegramError
import time

# Bot token and channel username
BOT_TOKEN = "7993719241:AAE6ItGn4ciaJv8c_Hjwlt01lTqhuqj9j8Q"  # Replace with your bot token
CHANNEL_USERNAME = "@megasaruku0"  # Replace with your channel username
ADMIN_ID = 1134468682  # Replace with your Telegram user ID

# File to save and load user data
DATA_FILE = "users_data.json"
ITEMS_FILE = 'items.json'

# Initialize bot and set up logging
bot = Bot(token=BOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load user data from file
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save user data to file
def save_data(users_data):
    with open(DATA_FILE, "w") as file:
        json.dump(users_data, file)

# Load items from JSON file
def load_items():
    try:
        with open(ITEMS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save items to JSON file
def save_items(items):
    with open(ITEMS_FILE, 'w') as file:
        json.dump(items, file, indent=4)

# Initialize user data
users_data = load_data()

# Check if the user has joined the channel
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError as e:
        logger.error(f"Error checking membership: {e}")
        return False

# Start command with referral tracking and storing user's name
def start(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        referrer_id = context.args[0] if context.args else None

        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name if update.effective_user.last_name else ""

        if user_id not in users_data:
            users_data[user_id] = {"first_name": first_name, "last_name": last_name, "referrals": 0, "is_vip": False}
            
            if referrer_id and referrer_id != user_id and referrer_id in users_data:
                users_data[referrer_id]["referrals"] += 1
                save_data(users_data)

                if users_data[referrer_id]["referrals"] >= 25 and not users_data[referrer_id]["is_vip"]:
                    users_data[referrer_id]["is_vip"] = True
                    save_data(users_data)
                    bot.send_message(chat_id=int(referrer_id), text="Congratulations! You've earned VIP status! \nContact @Vip_support0bot")

        save_data(users_data)

        if check_channel_membership(user_id):
            referral_link = f"https://t.me/{bot.username}?start={user_id}"
            welcome_message = f"Welcome to the bot, {first_name} {last_name}! 🎉\n\n" \
                              f"Here are the commands you can use:\n\n" \
                              f"/gen - Get a random item\n" \
                              f"/alive - Check if the bot is running\n" \
                              f"/help - Get help\n" \
                              f"/vip - Access VIP content\n" \
                              f"/referral - Check your referral count\n\n" \
                              f"Your referral link: {referral_link}"
            update.message.reply_text(welcome_message)
        else:
            keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            caption = "Access Denied 🚫\n\nYou must join the channel to use the bot."
            update.message.reply_photo(photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg?20200919053248", caption=caption, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("An error occurred while processing your request. Please try again later.")

# Command to generate random item
def gen(update: Update, context: CallbackContext):
    try:
        items = load_items()
        if items:
            user_id = str(update.effective_user.id)
            if check_channel_membership(user_id):
                item = random.choice(items)
                update.message.reply_photo(photo=item['image'], caption=f"Enjoy mawa...❤️\nLink: {item['url']}")
            else:
                keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                caption = "Access Denied 🚫\n\nYou must join the channel to use the bot."
                update.message.reply_photo(photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg?20200919053248", caption=caption, reply_markup=reply_markup)
        else:
            update.message.reply_text("No items available.")
    except Exception as e:
        logger.error(f"Error in gen command: {e}")
        update.message.reply_text("An error occurred while generating the item. Please try again later.")

# Alive command
def alive(update: Update, context: CallbackContext):
    update.message.reply_text("Bot is Alive ⚡")

# Help command
def help_command(update: Update, context: CallbackContext):
    help_message = "Here are the commands you can use:\n\n" \
                   "/gen - Get a random item 🎁\n" \
                   "/alive - Check if the bot is running 🏃‍♂️\n" \
                   "/help - Get help ❓\n" \
                   "/vip - Access VIP content 🌟\n" \
                   "/referral - See your referral count 👥"
    update.message.reply_text(help_message)


# VIP command
def vip(update: Update, context: CallbackContext):
    message = (
        "To unlock VIP status, you need to refer 25 members! 🎉\n"
        "\n"
        "What does VIP status give you?\n"
        "- Access to ad-free content\n"
        "- Exclusive links without interruptions\n"
        "\n"
        "If you're interested in a VIP subscription:\n"
        "- Monthly: ₹100\n"
        "- Lifetime: ₹300\n"
        "\n"
        "For more information or assistance, please contact: @Vip_support0bot 📩"
    )

    user_id = str(update.effective_user.id)
    if user_id in users_data and users_data[user_id]["is_vip"]:
        update.message.reply_text("Welcome, VIP! Enjoy your exclusive content 🔥")
    else:
        update.message.reply_text(message)
# Referral command
def referral(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    referral_count = users_data.get(user_id, {}).get("referrals", 0)
    referral_link = f"https://t.me/{bot.username}?start={user_id}"
    keyboard = [[InlineKeyboardButton("Refer a Friend", switch_inline_query="")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"You have referred {referral_count} friends.\nYour referral link: {referral_link}", reply_markup=reply_markup)

# Admin-only data command
def data(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_file.write(json.dumps(users_data, indent=4).encode('utf-8'))
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as file:
            context.bot.send_document(chat_id=ADMIN_ID, document=file, filename='users_data.json')
    except Exception as e:
        logger.error(f"Error sending data to admin: {e}")

# Command to add a new item (admin only)
def add_item(update: Update, context: CallbackContext):
    try:
        if update.effective_user.id != ADMIN_ID:
            update.message.reply_text("You are not authorized to use this command.")
            return

        if len(context.args) < 2:
            update.message.reply_text("Please provide both a URL and an image link. Usage: /additem <url> <image_link>")
            return

        url = context.args[0]
        image_link = context.args[1]

        items = load_items()
        new_item = {"url": url, "image": image_link}
        items.append(new_item)
        save_items(items)
        update.message.reply_text(f"New item added: {new_item}")
    except Exception as e:
        logger.error(f"Error in add_item command: {e}")
        update.message.reply_text("An error occurred while adding the item. Please try again later.")

# Command to broadcast a message to all users (admin only)
def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        update.message.reply_text("Please provide a message to broadcast.")
        return

    message = " ".join(context.args)
    sent, blocked = 0, 0

    for user_id in users_data.keys():
        try:
            context.bot.send_message(chat_id=int(user_id), text=message)
            sent += 1
        except (BadRequest, TelegramError) as e:
            if "bot was blocked by the user" in str(e):
                blocked += 1

    update.message.reply_text(f"Broadcast completed. Sent: {sent}, Blocked: {blocked}")

# Main function to set up handlers and start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CommandHandler("alive", alive))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("vip", vip))
    dp.add_handler(CommandHandler("referral", referral))
    dp.add_handler(CommandHandler("data", data))
    dp.add_handler(CommandHandler("additem", add_item))
    dp.add_handler(CommandHandler("broadcast", broadcast))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
