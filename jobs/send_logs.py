if __name__ == '__main__':
    pass    
else:
    from utils.jsonUtils import load_configs, fromJSONFile, toJSONFile


from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from asyncio import sleep

async def send_logs_channel(context: ContextTypes.DEFAULT_TYPE):
    logQueue = fromJSONFile('logQueue.json')
    
    if len(logQueue) == 0:
        return
    
    log_count = {}
    for log in logQueue:
        if log in log_count:
            log_count[log] += 1
        else:
            log_count[log] = 1
    
    separator = "\n\n--- Un altro log trovato ---\n\n"
    mex = f"#{context.bot.name.replace('@','').upper()} LOG RECAP\n\n"
    
    for log, count in log_count.items():
        if count > 1:
            mex += f"{log} (x{count})" + separator
        else:
            mex += log + separator
    
    mex = mex[:len(mex)-len(separator)].replace("<","&lt;").replace(">","&gt;").replace("&","&amp;")
    
    while len(mex) > 0:
        too_long = mex[0:4095] # Diviso per massimo di telegram
        await context.bot.send_message(load_configs()["canale_log"], too_long, parse_mode=ParseMode.HTML)
        mex = mex[4095:]
        await sleep(5)
    
    # Svuota la coda e salva su file
    toJSONFile('logQueue.json', [])

