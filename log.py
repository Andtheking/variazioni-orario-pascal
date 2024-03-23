import logging
import os

from datetime import datetime

from telegram.ext import ExtBot
from telegram.constants import ParseMode

from jsonUtils import fromJSON
import inspect


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


async def log(message: str, bot: ExtBot = None, tipo: str = "info"):
    now = datetime.now()
    
    if tipo == "errore":
        logger.error(message)
    else: #if tipo == "info":
        logger.info(message)
        
        
    messageForFile = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] - {inspect.stack()[1].filename} - " + message + "\n"
    messageForBot = message
    
    if bot is not None and fromJSON('sensible/utils.json')["canale_log"] is not None:
        await bot.send_message(fromJSON('sensible/utils.json')["canale_log"], f"#{bot.name.replace('@','').upper()} #{tipo.upper()}\n\n" + messageForBot, parse_mode=ParseMode.HTML)
        
    m = 'a'
    if not os.path.exists("./log.txt"):
        m='w'
        
    with open("./log.txt",m) as f:
        f.write(messageForFile)
    


