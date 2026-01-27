# Pipe module for ATProtocol music scrobbles
# Based on Last.fm module by @TheRealPhoenix

from atproto import Client, exceptions
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from tg_bot.modules.helper_funcs.decorators import kigcmd, rate_limit
import tg_bot.modules.sql.pipe_sql as sql


def model_to_dict(obj):
    """Recursively convert atproto model objects to dictionaries."""
    # Handle None and basic types first
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Try to convert model objects to dict
    if hasattr(obj, 'model_dump') and callable(getattr(obj, 'model_dump', None)):
        try:
            obj = obj.model_dump()
        except Exception as e:
            print(f"Error calling model_dump: {e}")
            if hasattr(obj, '__dict__'):
                obj = vars(obj)
    elif hasattr(obj, '__dict__') and not isinstance(obj, type):
        obj = vars(obj)
    
    # Recursively process collections
    if isinstance(obj, dict):
        return {k: model_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [model_to_dict(item) for item in obj]
    else:
        return obj


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
            # Convert to dict recursively
            value = model_to_dict(record.value)
            
            # Extract the item field which contains the track info
            if isinstance(value, dict) and 'item' in value:
                return value['item']
            return value
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
            tracks = []
            for record in response.records:
                # Convert to dict recursively
                value = model_to_dict(record.value)
                tracks.append(value)
            return tracks
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
            # Extract artist name from artists array
            artists = current.get('artists', [])
            artist = artists[0].get('artistName', 'Unknown Artist') if artists else 'Unknown Artist'
            track = current.get('trackName', 'Unknown Track')
            album = current.get('releaseName', '')
            
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
                # Extract artist name from artists array
                artists = play.get('artists', [])
                artist = artists[0].get('artistName', 'Unknown Artist') if artists else 'Unknown Artist'
                track = play.get('trackName', 'Unknown Track')
                rep += f"🎧  <code>{artist} - {track}</code>\n"
            
            # Add note about recent scrobbles
            if len(recent) > 0:
                rep += f"\n(Recent scrobbles from Pipe)"
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML)
        
    except exceptions.AtProtocolError as e:
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
