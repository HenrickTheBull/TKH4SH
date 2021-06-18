import html
import json
import os
from typing import List, Optional

from telegram import Update, ParseMode, TelegramError
from telegram.ext import CommandHandler, run_async, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import (
    dispatcher,
    WHITELIST_USERS,
    SARDEGNA_USERS,
    SUPPORT_USERS,
    SUDO_USERS,
    DEV_USERS,
    OWNER_ID,
)
from tg_bot.modules.helper_funcs.chat_status import whitelist_plus, dev_plus, sudo_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "tg_bot/elevated_users.json")


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "Eh, Error 13: That's a chat. Try a user ID"

    elif user_id == bot.id:
        reply = "Nope, Error 14: That's a bot. Try a user ID."

    else:
        reply = None
    return reply


# I added extra new lines
nations = """ H4SH has bot access levels to control users and devs.*
\n*Ψ Psi* - Devs who can access the bots server and can execute, edit, modify bot code. Can also manage other Nations
\n*Ω Omega* - Only one exists, bot owner.
Owner has complete bot access, including bot adminship in chats H4SH is at.
\n*Τ Tau* - Have super user access, can gban, manage users lower than them and are admins in H4SH.
\n*Μ Mu* - Have access to globally blacklist users across H4SH.
\n*Κ Kappa* - Same as Neptunians but can unban themselves if banned.
\n*Γ Gamma* - Cannot be banned, muted flood kicked but can be manually banned by admins.
\n*Disclaimer*: The Access levels in H4SH are there for troubleshooting, support, banning potential scammers.
Report abuse or ask us more on these at [Grand Aurochs Software](https://t.me/GASoftware).
"""


def send_nations(update):
    update.effective_message.reply_text(
        nations, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
    )


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Gamma Level Users:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def Sardegnalist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Kappa Level Users:</b>\n"
    for each_user in SARDEGNA_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Mu Level Users:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    true_sudo = list(set(SUDO_USERS) - set(DEV_USERS))
    reply = "<b>Known Tau Level Users :</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "<b>Psi Corp Memebers:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


from tg_bot.modules.language import gs

def get_help(chat):
    return gs(chat, "nation_help")

WHITELISTLIST_HANDLER = CommandHandler(
    ["whitelistlist", "gammas"], whitelistlist, run_async=True
)
SARDEGNALIST_HANDLER = CommandHandler(["kappas"], Sardegnalist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(
    ["supportlist", "mus"], supportlist, run_async=True
)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "taus"], sudolist, run_async=True)
DEVLIST_HANDLER = CommandHandler(["devlist", "psis"], devlist, run_async=True)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(SARDEGNALIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Nations"
__handlers__ = [
    WHITELISTLIST_HANDLER,
    SARDEGNALIST_HANDLER,
    SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER,
    DEVLIST_HANDLER,
]
