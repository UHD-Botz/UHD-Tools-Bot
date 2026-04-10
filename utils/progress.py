import time
import math

# Size ko MB/GB mein dikhane ke liye
def humanbytes(size):
    if not size: return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

# Time ko Mins/Secs mein dikhane ke liye
def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

# THE LIVE PROGRESS BAR FUNCTION
async def progress_bar(current, total, msg, start_time, action_text):
    now = time.time()
    diff = now - start_time

    # Har 3 second mein update karega taaki Telegram block na kare
    if round(diff % 3.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = round((total - current) / speed) * 1000 if speed > 0 else 0
        
        # Tera custom progress bar design 「 ▰▰▰▱▱▱▱▱▱▱ 」
        filled_blocks = int(percentage / 10)
        bar = "▰" * filled_blocks + "▱" * (10 - filled_blocks)
        
        text = f"⏳ **{action_text}**\n\n"
        text += f"**Progress :-** {round(percentage, 2)}% 「 {bar} 」\n"
        text += f"**Size :** {humanbytes(current)} / {humanbytes(total)}\n"
        text += f"**Speed :** {humanbytes(speed)}/s\n"
        text += f"**ETA :** {time_formatter(eta)}"
        
        try:
            await msg.edit_text(text)
        except Exception:
            pass # Message same hone par Telegram error ignore karega
