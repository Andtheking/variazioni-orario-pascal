import logging
import os
import inspect

from datetime import datetime

from utils.jsonUtils import fromJSONFile, toJSONFile, load_configs

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


logging.getLogger().setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def log(message: str, send_with_bot:bool = False, tipo: str = "info", only_file=False):
    now = datetime.now()
    message = str(message)
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
    if send_with_bot and load_configs()["canale_log"] is not None:
        logQueue.append(f"#{tipo.upper()}\n" + messageForBot)
        toJSONFile('logQueue.json',logQueue)
        
    m = 'a'
    if not os.path.exists("./log.txt"):
        m='w'
        
    with open("./log.txt",m, encoding="utf-8") as f:
        f.write(messageForFile)
    
