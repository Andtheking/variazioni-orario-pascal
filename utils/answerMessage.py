from telegram import Message
from telegram.constants import ParseMode

async def rispondi(messaggio: Message, text: str, parse_mode = ParseMode.HTML, reply_markup=None, **args):
    try:
        await messaggio.reply_text(
            text=text, 
            parse_mode=parse_mode, 
            reply_markup=reply_markup,
            **args
        )
    except:
        await messaggio.chat.send_message(
            text=text, 
            parse_mode=parse_mode, 
            reply_markup=reply_markup,
            **args
        )