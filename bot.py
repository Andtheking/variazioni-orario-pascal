TOKEN = '5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4'

import logging
from telegram.ext import Updater, CommandHandler
from sito import *
import os

PORT = int(os.environ.get('PORT',5000))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def help(update, context):
    update.message.reply_text("Ecco l'help")

def start(update,context):
    update.message.reply_text("Hai premuto start")

def impostaClasse(update, context):
    print(update.message.from_user.name,": ",end="")
    update.message.reply_text(Main(update.message.text))
    

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
     updater = Updater(TOKEN, use_context=True)
     dp = updater.dispatcher
     dp.add_handler(CommandHandler("start", start))
     dp.add_handler(CommandHandler("help", help))
     dp.add_handler(CommandHandler("impostaClasse", impostaClasse))
     

     dp.add_error_handler(error)

     updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
     updater.bot.setWebhook('https://stormy-bayou-12485.herokuapp.com/' + TOKEN)
     updater.idle()
     
    

if __name__ == '__main__':
    main()
