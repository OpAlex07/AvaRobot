from telethon import events

from Ava import telethn


def register(**args):
    """ʀᴇɢɪsᴛᴇʀs ᴀ ɴᴇᴡ ᴍᴇssᴀɢᴇ."""
    pattern = args.get("pattern")

    r_pattern = r"^[/!.]"

    if pattern is not None and not pattern.startswith("(?i)"):
        args["pattern"] = f"(?i){pattern}"

    args["pattern"] = pattern.replace("^/", r_pattern, 1)

    def decorator(func):
        telethn.add_event_handler(func, events.NewMessage(**args))
        return func

    return decorator


def Uvinline(**args):
    def decorator(func):
        telethn.add_event_handler(func, events.CallbackQuery(**args))
        return func

    return decorator
