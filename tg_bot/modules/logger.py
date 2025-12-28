import os
import time
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters

from tg_bot import dispatcher, OWNER_ID, log as LOGGER
from tg_bot.modules.sql import chat_logger_sql as sql

# Create a folder for logs if it doesn't exist
LOG_FOLDER = "chat_logs"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

def log_command(update: Update, context: CallbackContext):
    """
    Enables or disables logging for a specific chat.
    Usage: /log <chat_id> (or use inside the group)
    Only available to the Bot Owner.
    """
    user = update.effective_user
    
    # OWNER CHECK: Strictly prevent anyone else from using this
    if user.id != OWNER_ID:
        return

    args = context.args
    message = update.effective_message
    
    # Determine which chat ID to toggle
    if len(args) >= 1:
        try:
            chat_id = str(int(args[0]))
            chat_name = f"Manually Added {chat_id}"
        except ValueError:
            message.reply_text("Invalid Chat ID. Please provide a numeric ID (Snowflake).")
            return
    else:
        # If no ID provided, use the current chat
        chat = update.effective_chat
        chat_id = str(chat.id)
        chat_name = chat.title or chat.first_name

    # Toggle Logic
    if sql.is_logging_enabled(chat_id):
        sql.disable_logging(chat_id)
        message.reply_text(f"🛑 Logging has been **DISABLED** for chat ID: `{chat_id}`", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Logging disabled for {chat_id} by owner.")
    else:
        sql.enable_logging(chat_id, chat_name)
        message.reply_text(f"✅ Logging has been **ENABLED** for chat ID: `{chat_id}`\n\nMessages will be saved to `{LOG_FOLDER}/{chat_id}.txt`", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Logging enabled for {chat_id} by owner.")

def capture_messages(update: Update, context: CallbackContext):
    """
    Catches all text messages. If the chat is in the DB, save the text.
    """
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Skip updates that aren't text or don't have a chat
    if not chat or not message or not message.text:
        return

    # 1. Check if logging is enabled for this chat ID
    if sql.is_logging_enabled(str(chat.id)):
        
        # 2. Format the log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_name = user.first_name if user else "Unknown"
        user_id = user.id if user else 0
        
        # Format: [Time] [User_ID] Name: Message
        log_entry = f"[{timestamp}] [{user_id}] {user_name}: {message.text}\n"
        
        # 3. Append to file
        file_path = os.path.join(LOG_FOLDER, f"{chat.id}.txt")
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            LOGGER.error(f"Failed to write log for chat {chat.id}: {e}")

# Register Handlers
# Priority 1 ensures this runs before other commands/handlers might consume the update
log_cmd_handler = CommandHandler("log", log_command, run_async=True)
capture_handler = MessageHandler(Filters.text & ~Filters.update.edited_message, capture_messages, run_async=True)

dispatcher.add_handler(log_cmd_handler)
dispatcher.add_handler(capture_handler, group=1)