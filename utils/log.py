import logging
import os
import inspect

from datetime import datetime

from telegram.ext import ExtBot, ContextTypes
from telegram.constants import ParseMode


from .jsonUtils import fromJSONFile, toJSONFile



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)



def log(message: str, send_with_bot:bool = False, tipo: str = "info", only_file=False):
    now = datetime.now()
    
    if not only_file:
        if tipo == "errore":
            logger.error(message)
        elif tipo == "warning":
            logger.warning(message)
        else: #if tipo == "info":
            logger.info(message)
            
        
    messageForFile = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] - {inspect.stack()[1].filename} - " + message + "\n"
    messageForBot = message
    
    logQueue = fromJSONFile('logQueue.json')
    if send_with_bot and fromJSONFile('sensible/utils.json')["canale_log"] is not None:
        logQueue.append(f"#{tipo.upper()}\n" + messageForBot)
        toJSONFile('logQueue.json',logQueue)
        
    m = 'a'
    if not os.path.exists("./log.txt"):
        m='w'
        
    with open("./log.txt",m, encoding="utf-8") as f:
        f.write(messageForFile)
    
async def send_logs_channel(context: ContextTypes.DEFAULT_TYPE):
    logQueue = fromJSONFile('logQueue.json')
    
    if len(logQueue) == 0:
        return
    
    mex = f"#{context.bot.name.replace('@','').upper()} LOG RECAP\n\n"
    while len(logQueue) != 0:
        mex += logQueue.pop()+"\n\n--- Un altro log trovato ---\n\n"
    mex = mex[:len(mex)-len("\n\n--- Un altro log trovato ---\n\n")]
    
    while len(mex) > 0:
        await context.bot.send_message(fromJSONFile('sensible/utils.json')["canale_log"], mex, parse_mode=ParseMode.HTML)
        mex = mex[4095:]
        
    toJSONFile('logQueue.json',logQueue)
