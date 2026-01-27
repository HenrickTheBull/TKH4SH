# Pipe module for ATProtocol music scrobbles
# Based on Last.fm module by @TheRealPhoenix

from atproto import Client, exceptions
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from tg_bot.modules.helper_funcs.decorators import kigcmd, rate_limit
import tg_bot.modules.sql.pipe_sql as sql


def resolve_handle(handle: str):
    """
    Resolve an ATProtocol handle to get DID and PDS.
    Returns tuple of (did, pds_url) or (None, None) if failed.
    """
    try:
        client = Client()
        # Resolve the handle to get DID
        profile = client.resolve_handle(handle)
        did = profile.did
        
        # Get the PDS URL from the DID document
        # The client will automatically use the correct PDS
        pds_url = client.session.pds_url if hasattr(client, 'session') else None
        
        return did, pds_url
    except Exception as e:
        print(f"Error resolving handle {handle}: {e}")
        return None, None


def get_current_track(client: Client, did: str):
    """
    Get the currently playing track from fm.teal.alpha.actor.status
    """
    try:
        # Query the repo for the status record
        from atproto import models
        params = models.ComAtprotoRepoListRecords.Params(
            repo=did,
            collection="fm.teal.alpha.actor.status",
            limit=1
        )
        response = client.com.atproto.repo.list_records(params)
        
        if response and response.records:
            record = response.records[0]
            return record.value
        return None
    except Exception as e:
        print(f"Error getting current track: {e}")
        return None


def get_recent_tracks(client: Client, did: str, limit: int = 3):
    """
    Get recent scrobbles from fm.teal.alpha.feed.play
    """
    try:
        from atproto import models
        params = models.ComAtprotoRepoListRecords.Params(
            repo=did,
            collection="fm.teal.alpha.feed.play",
            limit=limit
        )
        response = client.com.atproto.repo.list_records(params)
        
        if response and response.records:
            return [record.value for record in response.records]
        return []
    except Exception as e:
        print(f"Error getting recent tracks: {e}")
        return []


@kigcmd(command='sethandle')
@rate_limit(40, 60)
def set_handle(update: Update, context: CallbackContext):
    args = context.args
    msg = update.effective_message
    if args:
        user = update.effective_user.id
        handle = " ".join(args).strip()
        
        # Validate the handle format (should be like user.bsky.social)
        if not handle or '.' not in handle:
            msg.reply_text(
                "That doesn't look like a valid ATProtocol handle.\n"
                "Example: user.bsky.social"
            )
            return
        
        # Try to resolve the handle to validate it
        did, pds = resolve_handle(handle)
        if not did:
            msg.reply_text(
                "I couldn't resolve that handle. Please make sure it's correct!"
            )
            return
        
        sql.set_handle(user, handle)
        msg.reply_text(f"ATProtocol handle set as {handle}!")
    else:
        msg.reply_text(
            "That's not how this works...\n"
            "Run /sethandle followed by your ATProtocol handle!\n"
            "Example: /sethandle user.bsky.social"
        )


@kigcmd(command='clearhandle')
@rate_limit(40, 60)
def clear_handle(update: Update, _):
    user = update.effective_user.id
    sql.set_handle(user, "")
    update.effective_message.reply_text(
        "ATProtocol handle successfully cleared from my database!"
    )


@kigcmd(command='pipe')
@rate_limit(40, 60)
def pipe(update: Update, _):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    handle = sql.get_handle(user_id)
    
    if not handle:
        msg.reply_text("You haven't set your ATProtocol handle yet!\nUse /sethandle to set it.")
        return

    try:
        # Initialize client and resolve handle
        client = Client()
        did, pds = resolve_handle(handle)
        
        if not did:
            msg.reply_text(
                "I couldn't resolve your handle. Please make sure it's still valid!"
            )
            return
        
        # Try to get current track first
        current = get_current_track(client, did)
        
        if current:
            # User is currently listening
            artist = current.get('artist', 'Unknown Artist')
            track = current.get('track', 'Unknown Track')
            album = current.get('album', '')
            
            rep = f"{user} is currently listening to:\n"
            rep += f"🎧  <code>{artist} - {track}</code>"
            if album:
                rep += f"\n📀  <code>{album}</code>"
        else:
            # Get recent tracks instead
            recent = get_recent_tracks(client, did, limit=3)
            
            if not recent:
                msg.reply_text("You don't seem to have any scrobbles yet...")
                return
            
            rep = f"{user} was listening to:\n"
            for play in recent:
                artist = play.get('artist', 'Unknown Artist')
                track = play.get('track', 'Unknown Track')
                rep += f"🎧  <code>{artist} - {track}</code>\n"
            
            # Add note about recent scrobbles
            if len(recent) > 0:
                rep += f"\n(Recent scrobbles from Pipe)"
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML)
        
    except exceptions.AtProtoError as e:
        msg.reply_text(
            f"An error occurred while fetching your data from ATProtocol.\n"
            f"Please make sure your handle is correct and you have Pipe/Teal scrobbling enabled."
        )
    except Exception as e:
        print(f"Pipe module error: {e}")
        msg.reply_text(
            "Hmm... something went wrong.\n"
            "Please ensure that you've set the correct handle and have scrobbles!"
        )


__mod_name__ = "Pipe"
