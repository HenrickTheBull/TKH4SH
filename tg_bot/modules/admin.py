import html
from typing import Optional

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
)
from tg_bot.modules.helper_funcs.decorators import kigcmd, rate_limit
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.language import gs
from tg_bot.modules.log_channel import loggable
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms


@kigcmd(command="promote", can_disable=False)
@connection_status
@bot_admin
@can_promote
@user_admin(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
@rate_limit(40, 60)
def promote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    # promoter = chat.get_member(user.id)
    """
    if (
            not (promoter.can_promote_members or promoter.status == "creator")
            and not user.id in SUDO_USERS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return
    """
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("How am I meant to promote someone that's already an admin?")
        return

    if user_id == bot.id:
        message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("I can't promote someone who isn't in the group.")
        else:
            message.reply_text("An error occured while promoting.")
        return

    bot.sendMessage(
        chat.id,
        f"<b>{user_member.user.first_name or user_id}</b> was promoted by <b>{message.from_user.first_name}</b> in <b>{chat.title}</b>",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@kigcmd(command="demote", can_disable=False)
@connection_status
@bot_admin
@can_promote
@user_admin(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
@rate_limit(40, 60)
def demote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("This person CREATED the chat, how would I demote them?")
        return

    if user_member.status != "administrator":
        message.reply_text("Can't demote what wasn't promoted!")
        return

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
        )

        bot.sendMessage(
            chat.id,
            f"<b>{user_member.user.first_name or user_id or None}</b> was demoted by <b>{message.from_user.first_name or None}</b> in <b>{chat.title or None}</b>",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "Could not demote. I might not be admin, or the admin status was appointed by another"
            " user, so I can't act upon them!"
        )
        return


"""
@kigcmd(command="admincache", can_disable=False)
@u_admin
@rate_limit(40, 60)
def refresh_admin(update, _):
    ADMIN_CACHE.pop(update.effective_chat.id)
    update.effective_message.reply_text("Admins cache refreshed!")
"""


@kigcmd(command="title", can_disable=False)
@connection_status
@bot_admin
@can_promote
@user_admin(AdminPerms.CAN_PROMOTE_MEMBERS)
@rate_limit(40, 60)
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "This person CREATED the chat, how can i set custom title for him?"
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "Can't set title for non-admins!\nPromote them first to set custom title!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "I can't set my own title myself! Get the one who made me admin to do it for me."
        )
        return

    if not title:
        message.reply_text("Setting blank title doesn't do anything!")
        return

    if len(title) > 16:
        message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("I can't set custom title for admins that I didn't promote!")
        return

    bot.sendMessage(
        chat.id,
        f"Sucessfully set title for <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@kigcmd(command="pin", can_disable=False)
@bot_admin
@can_pin
@user_admin(AdminPerms.CAN_PIN_MESSAGES)
@loggable
@rate_limit(40, 60)
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = (
                args[0].lower() != "notify"
                or args[0].lower() == "loud"
                or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@kigcmd(command="unpin", can_disable=False)
@bot_admin
@can_pin
@user_admin(AdminPerms.CAN_PIN_MESSAGES)
@loggable
@rate_limit(40, 60)
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNPINNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@kigcmd(command="invitelink", can_disable=False)
@connection_status
@rate_limit(40, 60)
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user

    # 1. Determine target chat ID
    if args:
        chat_id_str = args[0]
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            if chat_id_str.startswith('@'):
                chat_id = chat_id_str
            else:
                message.reply_text("Please provide a valid chat ID (integer) or username (starting with @).")
                return
    else:
        chat = update.effective_chat
        if chat.type == chat.PRIVATE:
            message.reply_text("Please provide a group chat ID as an argument.")
            return
        chat_id = chat.id

    # 2. Retrieve target chat details
    try:
        target_chat = bot.get_chat(chat_id)
    except (BadRequest, Unauthorized):
        message.reply_text("I am not in that chat, or the chat ID is invalid, or I do not have access to it.")
        return
    except TelegramError as e:
        message.reply_text(f"An error occurred while fetching chat: {e.message}")
        return

    if target_chat.type == target_chat.PRIVATE:
        message.reply_text("The specified chat ID corresponds to a private chat, not a group or channel.")
        return

    # 3. Check if requester has permission (user_admin check on target_chat)
    from tg_bot import DEV_USERS, SUDO_USERS
    is_authorized = False
    if user.id in DEV_USERS or user.id in SUDO_USERS:
        is_authorized = True
    else:
        try:
            user_member = target_chat.get_member(user.id)
            if user_member.status == 'creator':
                is_authorized = True
            elif user_member.status == 'administrator' and user_member.can_invite_users:
                is_authorized = True
        except TelegramError:
            pass

    if not is_authorized:
        message.reply_text("Who dis non-admin telling me what to do? You must be an administrator with invite privileges in that chat.")
        return

    # 4. Retrieve invite link
    invitelink = None
    if target_chat.username:
        invitelink = f"https://t.me/{target_chat.username}"
    else:
        try:
            bot_member = target_chat.get_member(bot.id)
            if bot_member.status in ('administrator', 'creator') and (bot_member.status == 'creator' or bot_member.can_invite_users):
                invitelink = bot.exportChatInviteLink(target_chat.id)
            else:
                message.reply_text("I need to be an administrator with invite privileges in that chat to retrieve the invite link.")
                return
        except TelegramError:
            message.reply_text("I am not in that chat or cannot access its members.")
            return

    if not invitelink:
        message.reply_text("Failed to retrieve or generate the invite link.")
        return

    # 5. Send invite link to user via DM
    if update.effective_chat.type == 'private':
        message.reply_text(f"Here is the invite link for <b>{html.escape(target_chat.title)}</b>:\n{invitelink}", parse_mode=ParseMode.HTML)
    else:
        try:
            bot.send_message(
                chat_id=user.id,
                text=f"Here is the invite link for <b>{html.escape(target_chat.title)}</b>:\n{invitelink}",
                parse_mode=ParseMode.HTML
            )
            message.reply_text("I've sent the invite link to you in DMs!")
        except Unauthorized:
            message.reply_text("Please start a conversation with me in DMs first so I can send you the invite link.")
        except TelegramError:
            message.reply_text("Failed to send you a DM. Please check your privacy settings or start a conversation with me first.")


@kigcmd(command=["admin", "admins"])
@rate_limit(40, 60)
def adminlist(update: Update, _):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        if not admin.is_anonymous:
            user = admin.user
            name = user.mention_markdown()
            text += "\n -> {} • `{}` • `{}` • `{}`".format(name, user.id, admin.status,
                                                           escape_markdown(
                                                               admin.custom_title) if admin.custom_title else "")

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def get_help(chat):
    return gs(chat, "admin_help")


__mod_name__ = "Admin"
