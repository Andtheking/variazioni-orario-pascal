import logging
import os

from datetime import datetime

from telegram.ext import ExtBot, ContextTypes
from telegram.constants import ParseMode

from jsonUtils import fromJSON
import inspect


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

logQueue = []

async def log(message: str, bot: ExtBot = None, tipo: str = "info"):
    now = datetime.now()
    
    if tipo == "errore":
        logger.error(message)
    else: #if tipo == "info":
        logger.info(message)
        
        
    messageForFile = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] - {inspect.stack()[1].filename} - " + message + "\n"
    messageForBot = message
    
    if bot is not None and fromJSON('sensible/utils.json')["canale_log"] is not None:
        logQueue.append(f"#{bot.name.replace('@','').upper()} #{tipo.upper()}\n" + messageForBot)
        
    m = 'a'
    if not os.path.exists("./log.txt"):
        m='w'
        
    with open("./log.txt",m, encoding="utf-8") as f:
        f.write(messageForFile)
    
async def send_logs_channel(context: ContextTypes.DEFAULT_TYPE):
    if len(logQueue) == 0:
        return
    
    mex = f"LOG RECAP\n\n"
    while len(logQueue) != 0:
        mex += logQueue.pop()+"\n\n--- Un altro log trovato ---\n\n"
    mex = mex[:len(mex)-len("\n\n--- Un altro log trovato ---\n\n")]
    
    while len(mex) > 0:
        await context.bot.send_message(fromJSON('sensible/utils.json')["canale_log"], mex, parse_mode=ParseMode.HTML)
        mex = mex[4095:]
