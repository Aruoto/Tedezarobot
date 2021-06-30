import html
from typing import Optional

from telegram import Message, Chat, User
from telegram import ChatPermissions
from telegram.error import BadRequest
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler

from Tedeza import dispatcher, LOGGER
from Tedeza.modules.helper_funcs.chat_status import (
    bot_admin,
    user_admin,
    is_user_admin,
    can_restrict,
)
from Tedeza.modules.helper_funcs.extraction import extract_user, extract_user_and_text, get_user
from Tedeza.modules.helper_funcs.string_handling import extract_time
from Tedeza.modules.helper_funcs.admin_rights import user_can_ban
from Tedeza.modules.helper_funcs.chat_status import is_user_admin
from Tedeza.modules.helper_funcs.alternate import typing_action
from Tedeza.modules.log_channel import loggable

# Reworked @meanii <https://github.com/meanii>  

@run_async
@bot_admin
@user_admin
@loggable
@typing_action
def mute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    
    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text(
            "You don't have enough rights to restrict someone from talking!"
        )
        return ""
    
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user."
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahh... I'm not muting myself!")
        return ""
    
    if user_id == 777000 or user_id == 1087968824:
        message.reply_text(str(user_id) + " is an account reserved for telegram, I cannot mute it!")
        return ""  
    
    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Well I'm not gonna stop an admin from talking!")
        
        elif member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(
                chat.id, user_id, permissions=ChatPermissions(can_send_messages=False)
            )
            reply_msg = "*{}* (`{}`) has been muted in *{}*.".format(
                member.user.first_name,
                member.user.id, chat.title) 
            
            message.reply_text(reply_msg,
                               reply_markup=InlineKeyboardMarkup(
                                   [
                                       [
                                           InlineKeyboardButton(text="Unmute", callback_data=f"muteb_mute={user_id}"),
                                           InlineKeyboardButton(text="Delete", callback_data=f"muteb_del")  
                                        ]
                                    ]
                                   ),
                               parse_mode=ParseMode.MARKDOWN
                               )
            return (
                "<b>{}:</b>"
                "\n#MUTE"
                "\n<b>Admin:</b> {}"
                "\n<b>User:</b> {}".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(member.user.id, member.user.first_name),
                )
            )

        else:
            message.reply_text("This user is already muted.")
    else:
        message.reply_text("This user isn't in the chat!")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
@typing_action
def unmute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text("You don't have enough rights to unmute people")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user."
        )
        return ""
    
    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("This user already has the right to speak.")
        else:
            context.bot.restrict_chat_member(
                chat.id,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_send_polls=True,
                    can_change_info=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            message.reply_text(f"Yep! *{member.user.first_name}* (`{member.user.id}`) can start talking again!",
                               parse_mode=ParseMode.MARKDOWN)
            return (
                "<b>{}:</b>"
                "\n#UNMUTE"
                "\n<b>Admin:</b> {}"
                "\n<b>User:</b> {}".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(member.user.id, member.user.first_name),
                )
            )
    else:
        message.reply_text(
            "This user isn't even in the chat, unmuting them won't make them talk more than they "
            "already do!"
        )

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_mute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text(
            "You don't have enough rights to restrict someone from talking!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_admin(chat, user_id, member):
        message.reply_text("I really wish I could mute admins.")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I'm not gonna mute myself.")
        return ""
    
    if user_id == 777000 or user_id == 1087968824:
        message.reply_text(str(user_id) + " is an account reserved for telegram, I cannot mute it!")
        return ""  

    if not reason:
        message.reply_text("You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        "<b>{}:</b>"
        "\n#TEMP MUTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>Time:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            time_val,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(
                chat.id,
                user_id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            reply_msg = "*{}* (`{}`) has been muted in *{}* for {}!.".format(
                member.user.first_name,
                member.user.id, chat.title,
                time_val) 
            message.reply_text(reply_msg,
                               reply_markup=InlineKeyboardMarkup(
                                   [[InlineKeyboardButton(text="Unmute", callback_data=f"muteb_mute={user_id}"),
                                     InlineKeyboardButton(text="Delete", callback_data=f"muteb_del")]]
                                   ),
                               parse_mode=ParseMode.MARKDOWN
                               )
            return log
        else:
            message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("shut up! muted for {}!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well damn, I can't mute that user.")

    return ""

@run_async
@bot_admin
@loggable
def muteb_callback(update, context):
    query = update.callback_query
    chat = update.effective_chat  
    user = update.effective_user
    if not query.data == "muteb_del":
        splitter = query.data.split("=")
        query_match = splitter[0]
        user_id = splitter[1]
        if query_match == "muteb_mute":
            if not is_user_admin(chat, int(user.id)):
                context.bot.answer_callback_query(query.id,
                                                text="You don't have enough rights to unmute people",
                                                show_alert=True)
                return ""
            else:
                member = chat.get_member(int(user_id))

                if member.status != "kicked" and member.status != "left":
                    if (
                        member.can_send_messages
                        and member.can_send_media_messages
                        and member.can_send_other_messages
                        and member.can_add_web_page_previews
                    ):
                        query.message.edit_text("This user already has the right to speak.")
                    else:
                        context.bot.restrict_chat_member(
                            chat.id,
                            int(user_id),
                            permissions=ChatPermissions(
                                can_send_messages=True,
                                can_invite_users=True,
                                can_pin_messages=True,
                                can_send_polls=True,
                                can_change_info=True,
                                can_send_media_messages=True,
                                can_send_other_messages=True,
                                can_add_web_page_previews=True,
                            ),
                        )
                        query.message.edit_text(f"Yep! *{member.user.first_name}* (`{member.user.id}`) can start talking again!",
                               parse_mode=ParseMode.MARKDOWN)
                        context.bot.answer_callback_query(query.id,
                                              text="Unmuted!"
                                              )
                        return (
                            "<b>{}:</b>"
                            "\n#UNMUTE"
                            "\n<b>Admin:</b> {}"
                            "\n<b>User:</b> {}".format(
                                html.escape(chat.title),
                                mention_html(user.id, user.first_name),
                                mention_html(member.user.id, member.user.first_name),
                            )
                        )
                        
    else:
        if not is_user_admin(chat, int(user.id)):
            context.bot.answer_callback_query(query.id,
                                              text="You don't have enough rights to delete this message.",
                                              show_alert=True)
            return ""
        else:
            query.message.delete()
            context.bot.answer_callback_query(query.id,
                                              text="Deleted!"
                                              )
            return ""
        
        

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CommandHandler(
    ["tmute", "tempmute"], temp_mute, pass_args=True, filters=Filters.group
)
MBUTTON_CALLBACK_HANDLER = CallbackQueryHandler(muteb_callback, pattern=r"muteb_")

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
dispatcher.add_handler(MBUTTON_CALLBACK_HANDLER)
