import logging
import json
import random
import os
import tempfile
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.error import BadRequest

# Bot token and channel username
BOT_TOKEN = "8044627800:AAGvCBiRHSlP6aIEr4mI284TrzL2zIYAt4I"  # Replace with your bot token
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
    except FileNotFoundError:
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
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

# Start command with referral tracking and storing user's name
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    referrer_id = context.args[0] if context.args else None

    # Get user's first and last names
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name if update.effective_user.last_name else ""

    if user_id not in users_data:
        users_data[user_id] = {"first_name": first_name, "last_name": last_name, "referrals": 0, "is_vip": False}
        
        # Check if the user was referred
        if referrer_id and referrer_id != user_id and referrer_id in users_data:
            users_data[referrer_id]["referrals"] += 1
            save_data(users_data)  # Save after updating referral count

            # Grant VIP status if referrals reach 50
            if users_data[referrer_id]["referrals"] >= 50 and not users_data[referrer_id]["is_vip"]:
                users_data[referrer_id]["is_vip"] = True
                save_data(users_data)  # Save VIP status
                bot.send_message(chat_id=int(referrer_id), text="Congratulations! You've earned VIP status!")

    save_data(users_data)  # Save new user info

    # Generate and send welcome message or access denied message
    if check_channel_membership(user_id):
        referral_link = f"https://t.me/{bot.username}?start={user_id}"
        welcome_message = f"Welcome to the bot, {first_name} {last_name}! 🎉\n\n" \
                          f"Here are the commands you can use:\n\n" \
                          f"/gen - Get a random item\n" \
                          f"/alive - Check if the bot is running\n" \
                          f"/help - Get help\n" \
                          f"/vip - Access VIP content\n\n" \
                          f"Your referral link: {referral_link}"
        update.message.reply_text(welcome_message)
    else:
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        caption = "Access Denied 🚫\n\nYou must join the channel to use the bot."
        update.message.reply_photo(photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg?20200919053248", caption=caption, reply_markup=reply_markup)

# Command to generate random item
def gen(update: Update, context: CallbackContext):
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

# Command to add a new item (admin only)
def add_item(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        update.message.reply_text("Please provide both a URL and an image link. Usage: /additem <url> <image_link>")
        return

    url = context.args[0]
    image_link = context.args[1]

    # Load existing items
    items = load_items()

    # Add new item
    new_item = {"url": url, "image": image_link}
    items.append(new_item)

    # Save updated items
    save_items(items)

    update.message.reply_text(f"New item added: {new_item}")

# Alive command
def alive(update: Update, context: CallbackContext):
    update.message.reply_text("The bot is alive! 😊")

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

# Command to show referral counts and provide a referral button
def referral(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in users_data:
        referrals = users_data[user_id]["referrals"]
        referral_link = f"https://t.me/{bot.username}?start={user_id}"  # Unique referral link

        referral_message = f"You have referred {referrals} people. 🎉\n\n" \
                           f"Share your referral link:\n{referral_link}"

        # Create a button to share the referral link
        keyboard = [[InlineKeyboardButton("Refer a Friend", url=f"https://t.me/share/url?url={referral_link}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the message with the button
        update.message.reply_text(referral_message, reply_markup=reply_markup)
    else:
        update.message.reply_text("You have not referred anyone yet. 👀")

# Command for bot owner to view user data
def data(update: Update, context: CallbackContext):
    if update.effective_user.id == ADMIN_ID:
        # Create a temporary file to save the user data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_file.write(json.dumps(users_data, indent=4).encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Send the file to the admin
        with open(temp_file_path, 'rb') as file:
            context.bot.send_document(chat_id=ADMIN_ID, document=file, filename='users_data.json')

# Error handler
def error_handler(update: Update, context: CallbackContext):
    logger.error(f'Update "{update}" caused error "{context.error}"')
    if isinstance(context.error, BadRequest):
        update.message.reply_text("Sorry, an error occurred. Please try again later.")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CommandHandler("additem", add_item))
    dp.add_handler(CommandHandler("alive", alive))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("vip", vip))
    dp.add_handler(CommandHandler("referral", referral))
    dp.add_handler(CommandHandler("data", data))

    # Log all errors
    dp.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
